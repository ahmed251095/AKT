#!/usr/bin/env bash
#
# Put the AKT public site onto the server's Odoo.
#
# Written to be pasted into a provider console, so it finds its own way
# around: the addons directory comes from the running configuration and the
# database from the configuration or from the server when only one exists.
#
#   curl -fsSL https://raw.githubusercontent.com/ahmed251095/AKT/main/tools/deploy_website.sh -o /tmp/site.sh && bash /tmp/site.sh 2>&1 | tee /tmp/site.log
#
# This installs Odoo's `website` and `crm` apps if they are not installed
# yet, because akt_website depends on them. Installing an app is not
# something Odoo can undo, so the database is dumped first and the path to
# the dump is printed at the end.
#
# What the site looks like afterwards:
#   /            the Arabic site      (Arabic is the website's default)
#   /en/...      the English site
#   /ar/...      redirects onto /... - the old links keep working
#   /odoo        the backend, unchanged
#
set -euo pipefail

REPO_URL="https://github.com/ahmed251095/AKT.git"
MODULE="akt_website"
LOCATOR="aos_construction_ext"   # a module already on this server
ODOO_CONF="${ODOO_CONF:-/etc/odoo/odoo.conf}"
STAMP="$(date +%Y%m%d-%H%M%S)"

say() { printf '\n== %s\n' "$*"; }
die() { printf '\nFAILED: %s\n' "$*" >&2; exit 1; }

[ -r "$ODOO_CONF" ] || die "no odoo configuration at $ODOO_CONF (set ODOO_CONF=... and run again)"

# ---------------------------------------------------------------- locate
say "Locating the addons directory"
ADDONS_PATH="$(grep -E '^\s*addons_path\s*=' "$ODOO_CONF" | tail -1 | cut -d= -f2- | tr -d ' ')"
[ -n "$ADDONS_PATH" ] || die "addons_path is not set in $ODOO_CONF"

PARENT=""
IFS=',' read -ra DIRS <<< "$ADDONS_PATH"
for d in "${DIRS[@]}"; do
    if [ -d "$d/$LOCATOR" ]; then PARENT="$d"; break; fi
done
if [ -z "$PARENT" ]; then
    # No landmark: fall back to the last entry that is not Odoo's own.
    for d in "${DIRS[@]}"; do
        case "$d" in */odoo/addons|*/odoo/odoo/addons) continue;; esac
        [ -d "$d" ] && PARENT="$d"
    done
fi
[ -n "$PARENT" ] || die "could not tell which directory of addons_path holds the custom modules: $ADDONS_PATH"
echo "   $PARENT"

# ---------------------------------------------------------------- database
DB="${DB:-$(grep -E '^\s*db_name\s*=' "$ODOO_CONF" | tail -1 | cut -d= -f2- | tr -d ' ' || true)}"
if [ -z "$DB" ] || [ "$DB" = "False" ]; then
    mapfile -t DBS < <(su - postgres -c "psql -tAc \"select datname from pg_database where datistemplate = false and datname <> 'postgres'\"" 2>/dev/null || true)
    [ "${#DBS[@]}" -eq 1 ] || die "could not tell which database to use (found: ${DBS[*]:-none}). Re-run as: DB=<name> bash $0"
    DB="${DBS[0]}"
fi
echo "   database: $DB"

say "Finding the account Odoo runs as"
RUN_AS="$(systemctl show -p User --value odoo 2>/dev/null || true)"
[ -n "$RUN_AS" ] || RUN_AS="$(stat -c '%U' "$ODOO_CONF")"
[ -n "$RUN_AS" ] && [ "$RUN_AS" != "root" ] || RUN_AS="odoo"
id "$RUN_AS" >/dev/null 2>&1 || die "no such user: $RUN_AS"
echo "   $RUN_AS"

# ---------------------------------------------------------------- source
say "Fetching $REPO_URL"
WORK="/tmp/akt-site-$STAMP"
git clone --depth 1 "$REPO_URL" "$WORK" >/dev/null 2>&1 || die "could not clone $REPO_URL"
[ -d "$WORK/$MODULE" ] || die "$MODULE is not in the repository"
echo "   at commit $(git -C "$WORK" rev-parse --short HEAD) - $(git -C "$WORK" log -1 --format=%s)"

# ---------------------------------------------------------------- backup
# Installing an app is not reversible, so there is a way back before the
# first install. On later runs the module is only upgraded and the dump is
# cheap insurance anyway.
say "Dumping $DB to /root/akt-site-$STAMP.sql.gz"
mkdir -p /root
su - postgres -c "pg_dump -Fp '$DB'" | gzip > "/root/akt-site-$STAMP.sql.gz"
ls -lh "/root/akt-site-$STAMP.sql.gz"

if [ -d "$PARENT/$MODULE" ]; then
    say "Backing up the current module to /root/akt-backup-$STAMP"
    mkdir -p "/root/akt-backup-$STAMP"
    cp -a "$PARENT/$MODULE" "/root/akt-backup-$STAMP/"
fi

# ---------------------------------------------------------------- install
say "Copying $MODULE in"
OWNER="$RUN_AS:$(id -gn "$RUN_AS")"
rm -rf "${PARENT:?}/$MODULE"
cp -a "$WORK/$MODULE" "$PARENT/$MODULE"
chown -R "$OWNER" "$PARENT/$MODULE"
find "$PARENT/$MODULE" -name '__pycache__' -type d -prune -exec rm -rf {} +
du -sh "$PARENT/$MODULE"

# The service is stopped first on purpose. Installing while workers are
# serving requests rebuilds the registry underneath them, and a running
# worker keeps the old Python in memory - the restart afterwards is what
# loads the new code, not the install.
say "Stopping Odoo"
systemctl stop odoo 2>/dev/null || service odoo stop || die "could not stop odoo"

INSTALLED="$(su - postgres -c "psql -tAc \"select state from ir_module_module where name = '$MODULE'\" '$DB'" 2>/dev/null | tr -d ' ' || true)"
if [ "$INSTALLED" = "installed" ]; then
    ACTION="-u $MODULE"; WHAT="Upgrading"
else
    ACTION="-i $MODULE"; WHAT="Installing"
fi

say "$WHAT $MODULE on $DB (this also brings in website and crm)"
ODOO_BIN="$(command -v odoo || command -v odoo-bin || echo /usr/bin/odoo)"
set +e
su - "$RUN_AS" -s /bin/bash -c "$ODOO_BIN -c $ODOO_CONF -d $DB $ACTION --stop-after-init --log-level=warn" 2>&1 | tail -40
RC=${PIPESTATUS[0]}
set -e

say "Starting Odoo"
systemctl start odoo 2>/dev/null || service odoo start

if [ "$RC" -ne 0 ]; then
    cat <<MSG

The install exited $RC. Odoo rolls a failed install back in one
transaction, so the database is as it was. The dump is at
/root/akt-site-$STAMP.sql.gz if you want to be sure.

MSG
    exit "$RC"
fi

cat <<MSG

== Done

  $MODULE is $( [ "$ACTION" = "-i $MODULE" ] && echo installed || echo upgraded ) on $DB.

  Arabic site   https://www.akt-grp.com/
  English site  https://www.akt-grp.com/en/
  Backend       https://www.akt-grp.com/odoo
  Leads         Odoo > CRM, tagged "Website: ..."

  Database dump before this run: /root/akt-site-$STAMP.sql.gz

MSG
