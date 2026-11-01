#!/usr/bin/env bash
#
# Pull this repo onto the server and upgrade aos_construction_ext.
#
# Written to be pasted into a provider console, so it finds its own way
# around instead of taking paths as arguments: the module directory is
# located from the running configuration, and the database from the
# configuration or from the server itself when only one exists.
#
#   curl -fsSL https://raw.githubusercontent.com/ahmed251095/AKT/main/tools/deploy_module.sh -o /tmp/deploy.sh && bash /tmp/deploy.sh 2>&1 | tee /tmp/deploy.log
#
set -euo pipefail

REPO_URL="https://github.com/ahmed251095/AKT.git"
MODULES="aos_construction_management aos_construction_ext"
UPGRADE="aos_construction_ext"
ODOO_CONF="${ODOO_CONF:-/etc/odoo/odoo.conf}"
STAMP="$(date +%Y%m%d-%H%M%S)"

say() { printf '\n== %s\n' "$*"; }
die() { printf '\nFAILED: %s\n' "$*" >&2; exit 1; }

[ -r "$ODOO_CONF" ] || die "no odoo configuration at $ODOO_CONF (set ODOO_CONF=... and run again)"

# ---------------------------------------------------------------- locate
say "Locating $UPGRADE"
ADDONS_PATH="$(grep -E '^\s*addons_path\s*=' "$ODOO_CONF" | tail -1 | cut -d= -f2- | tr -d ' ')"
[ -n "$ADDONS_PATH" ] || die "addons_path is not set in $ODOO_CONF"

MODULE_DIR=""
IFS=',' read -ra DIRS <<< "$ADDONS_PATH"
for d in "${DIRS[@]}"; do
    if [ -d "$d/$UPGRADE" ]; then MODULE_DIR="$d/$UPGRADE"; break; fi
done
[ -n "$MODULE_DIR" ] || die "$UPGRADE is not in any directory of addons_path: $ADDONS_PATH"
PARENT="$(dirname "$MODULE_DIR")"
echo "   module:  $MODULE_DIR"
echo "   addons:  $PARENT"

# ---------------------------------------------------------------- database
DB="$(grep -E '^\s*db_name\s*=' "$ODOO_CONF" | tail -1 | cut -d= -f2- | tr -d ' ' || true)"
if [ -z "$DB" ] || [ "$DB" = "False" ]; then
    mapfile -t DBS < <(su - postgres -c "psql -tAc \"select datname from pg_database where datistemplate = false and datname <> 'postgres'\"" 2>/dev/null || true)
    [ "${#DBS[@]}" -eq 1 ] || die "could not tell which database to upgrade (found: ${DBS[*]:-none}). Re-run as: DB=<name> bash $0"
    DB="${DBS[0]}"
fi
echo "   database: $DB"

# ---------------------------------------------------------------- source
say "Fetching $REPO_URL"
WORK="/tmp/akt-deploy-$STAMP"
git clone --depth 1 "$REPO_URL" "$WORK" >/dev/null 2>&1 || die "could not clone $REPO_URL"
echo "   at commit $(git -C "$WORK" rev-parse --short HEAD) - $(git -C "$WORK" log -1 --format=%s)"

say "Backing up the current module directories to /root/akt-backup-$STAMP"
mkdir -p "/root/akt-backup-$STAMP"
for m in $MODULES; do
    [ -d "$PARENT/$m" ] && cp -a "$PARENT/$m" "/root/akt-backup-$STAMP/"
done
ls -1 "/root/akt-backup-$STAMP"

# The account Odoo actually runs under, which is NOT the owner of the module
# directory - that is often root, because somebody copied the module in as
# root. PostgreSQL here authenticates by peer, mapping the system user onto
# the database user, so running the upgrade as the wrong account fails with
# "Peer authentication failed" before it reads a single line of the module.
say "Finding the account Odoo runs as"
RUN_AS="$(systemctl show -p User --value odoo 2>/dev/null || true)"
[ -n "$RUN_AS" ] || RUN_AS="$(stat -c '%U' "$ODOO_CONF")"
[ -n "$RUN_AS" ] && [ "$RUN_AS" != "root" ] || RUN_AS="odoo"
id "$RUN_AS" >/dev/null 2>&1 || die "no such user: $RUN_AS"
echo "   $RUN_AS"

say "Copying the new source in"
OWNER="$RUN_AS:$(id -gn "$RUN_AS")"
for m in $MODULES; do
    [ -d "$WORK/$m" ] || continue
    rm -rf "${PARENT:?}/$m"
    cp -a "$WORK/$m" "$PARENT/$m"
    chown -R "$OWNER" "$PARENT/$m"
    find "$PARENT/$m" -name '__pycache__' -type d -prune -exec rm -rf {} +
    echo "   $m"
done

# ---------------------------------------------------------------- upgrade
# The service is stopped first on purpose. Upgrading while workers are
# serving requests rebuilds the registry underneath them and throws errors
# into whatever screen somebody has open; and a running worker keeps the old
# Python in memory, so the restart afterwards is what actually loads the new
# code, not the upgrade.
say "Stopping Odoo"
systemctl stop odoo 2>/dev/null || service odoo stop || die "could not stop odoo"

say "Upgrading $UPGRADE on $DB"
ODOO_BIN="$(command -v odoo || command -v odoo-bin || echo /usr/bin/odoo)"
set +e
su - "$RUN_AS" -s /bin/bash -c "$ODOO_BIN -c $ODOO_CONF -d $DB -u $UPGRADE --stop-after-init --log-level=warn" 2>&1 | tail -40
RC=${PIPESTATUS[0]}
set -e

say "Starting Odoo"
systemctl start odoo 2>/dev/null || service odoo start

if [ "$RC" -ne 0 ]; then
    cat <<MSG

The upgrade exited $RC. Odoo rolls the whole upgrade back in one
transaction, so the database is as it was; the old module source is in
/root/akt-backup-$STAMP if you want to put it back:

    cp -a /root/akt-backup-$STAMP/* $PARENT/ && service odoo restart

MSG
    exit "$RC"
fi

say "Done - $UPGRADE upgraded on $DB"
echo "Backup of the previous source: /root/akt-backup-$STAMP"
