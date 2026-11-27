#!/usr/bin/env bash
#
# Give Odoo the tool it needs to mirror its stylesheets for Arabic.
#
#   curl -fsSL https://raw.githubusercontent.com/ahmed251095/AKT/main/tools/install_rtlcss.sh -o /tmp/rtl.sh && bash /tmp/rtl.sh 2>&1 | tee /tmp/rtl.log
#
# Odoo mirrors web.assets_frontend for a right-to-left language by piping it
# through rtlcss, a node tool it shells out to. Without it Odoo logs a
# warning and stores the stylesheet unmirrored under the .rtl name, so an
# Arabic page gets `body { direction: ltr }` and lays itself out backwards.
#
# The public site no longer depends on this - akt_website takes the
# direction off the dir attribute instead - but Odoo's own screens, the
# backend and the website editor, are mirrored by that same bundle and have
# nothing else to fall back on.
#
# Installing the tool is not enough on its own: the wrong stylesheet is
# already saved in the database as an attachment, and Odoo would go on
# serving it. The generated bundles are dropped here so they are rebuilt,
# and the result is checked before the script reports success.
#
set -euo pipefail

ODOO_CONF="${ODOO_CONF:-/etc/odoo/odoo.conf}"

say() { printf '\n== %s\n' "$*"; }
die() { printf '\nFAILED: %s\n' "$*" >&2; exit 1; }

[ -r "$ODOO_CONF" ] || die "no odoo configuration at $ODOO_CONF (set ODOO_CONF=... and run again)"

# ---------------------------------------------------------------- install
if command -v rtlcss >/dev/null 2>&1; then
    say "rtlcss is already installed: $(command -v rtlcss) ($(rtlcss --version 2>/dev/null || echo 'version unknown'))"
else
    if ! command -v npm >/dev/null 2>&1; then
        say "Installing node and npm"
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -qq
        apt-get install -y -qq nodejs npm >/dev/null
    fi
    say "Installing rtlcss"
    npm install -g rtlcss >/dev/null 2>&1 || die "npm could not install rtlcss"
    command -v rtlcss >/dev/null 2>&1 || die "rtlcss installed but is not on PATH"
    echo "   $(command -v rtlcss)"
fi

# Odoo looks the tool up on the PATH of its own process, not of this shell.
# A systemd service gets a short PATH of its own, so if npm put rtlcss
# somewhere outside it the service would still not find it.
SERVICE_PATH="$(systemctl show -p Environment --value odoo 2>/dev/null | tr ' ' '\n' | sed -n 's/^PATH=//p' || true)"
[ -n "$SERVICE_PATH" ] || SERVICE_PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
RTLCSS_DIR="$(dirname "$(command -v rtlcss)")"
case ":$SERVICE_PATH:" in
    *":$RTLCSS_DIR:"*) ;;
    *) say "Putting rtlcss where the service will find it"
       ln -sf "$(command -v rtlcss)" /usr/local/bin/rtlcss
       echo "   /usr/local/bin/rtlcss -> $(command -v rtlcss)" ;;
esac

# ---------------------------------------------------------------- database
DB="${DB:-$(grep -E '^\s*db_name\s*=' "$ODOO_CONF" | tail -1 | cut -d= -f2- | tr -d ' ' || true)}"
if [ -z "$DB" ] || [ "$DB" = "False" ]; then
    mapfile -t DBS < <(su - postgres -c "psql -tAc \"select datname from pg_database where datistemplate = false and datname <> 'postgres'\"" 2>/dev/null || true)
    [ "${#DBS[@]}" -eq 1 ] || die "could not tell which database to use (found: ${DBS[*]:-none}). Re-run as: DB=<name> bash $0"
    DB="${DBS[0]}"
fi
say "Database: $DB"

say "Dropping the generated stylesheets so Odoo rebuilds them"
GONE="$(su - postgres -c "psql -tAc \"delete from ir_attachment where url like '/web/assets/%'\" '$DB'" | tr -d ' ')"
echo "   $GONE removed"

say "Restarting Odoo"
systemctl restart odoo 2>/dev/null || service odoo restart || die "could not restart odoo"

# ---------------------------------------------------------------- verify
PORT="$(grep -E '^\s*http_port\s*=' "$ODOO_CONF" | tail -1 | cut -d= -f2- | tr -d ' ' || true)"
[ -n "$PORT" ] || PORT=8069

say "Asking Odoo for the Arabic home page so the stylesheet is rebuilt"
for i in $(seq 1 30); do
    PAGE="$(curl -sS --max-time 60 -A 'Mozilla/5.0 (X11; Linux x86_64) Chrome/140.0' "http://127.0.0.1:$PORT/" || true)"
    [ -n "$PAGE" ] && break
    sleep 2
done
[ -n "$PAGE" ] || die "Odoo did not answer on port $PORT"

BUNDLE="$(printf '%s' "$PAGE" | grep -o '/web/assets/[^"]*frontend\.rtl\.min\.css' | head -1)"
if [ -z "$BUNDLE" ]; then
    cat <<'MSG'

The home page did not ask for a right-to-left stylesheet at all. That means
the page was not served in Arabic - check the website's default language in
Odoo - rather than that rtlcss is missing.

MSG
    exit 1
fi

DIRECTION="$(curl -sS --max-time 60 "http://127.0.0.1:$PORT$BUNDLE" | grep -oE 'body\{direction: ?(ltr|rtl)' | head -1 | grep -oE '(ltr|rtl)' || true)"
say "Checking the rebuilt stylesheet"
echo "   $BUNDLE"
echo "   body direction: ${DIRECTION:-could not tell}"

if [ "$DIRECTION" = "rtl" ]; then
    cat <<'MSG'

== Done

  Odoo is mirroring its stylesheets for Arabic now. The backend and the
  website editor read right-to-left as well, not just the public site.

  Open the site with a hard refresh (Ctrl+Shift+R) the first time.

MSG
else
    cat <<'MSG'

rtlcss is installed but the rebuilt stylesheet is still left-to-right.
Look for this line in the Odoo log:

  You need https://rtlcss.com/ to convert css file to right to left

If it is still there, the service cannot see the tool on its PATH; the
output above shows where it was installed. The public site is unaffected
either way - akt_website sets the direction itself.

MSG
    exit 1
fi
