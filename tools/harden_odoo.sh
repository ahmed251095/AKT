#!/usr/bin/env bash
# Harden the Odoo server behind nginx:
#   1. Bind Odoo to 127.0.0.1 so port 8069 is no longer reachable from the internet
#   2. Disable the database manager (list_db) and set a strong master password
# Safe: backs up odoo.conf and rolls back automatically if the site stops answering.
# Run as root on 159.223.138.227
set -uo pipefail

ODOO_CONF="/etc/odoo/odoo.conf"
CHECK_URL="https://akt-grp.com/web/login"
PW_FILE="/root/odoo_master_password.txt"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="${ODOO_CONF}.bak.${STAMP}"

set_opt() {  # set_opt <key> <value> -- replace under [options] or append
  local k="$1" v="$2"
  if grep -qE "^[[:space:]]*#?[[:space:]]*${k}[[:space:]]*=" "$ODOO_CONF"; then
    sed -i -E "s|^[[:space:]]*#?[[:space:]]*${k}[[:space:]]*=.*|${k} = ${v}|" "$ODOO_CONF"
  else
    sed -i "/^\[options\]/a ${k} = ${v}" "$ODOO_CONF"
  fi
}

echo "=== 0. Backup ==="
cp -a "$ODOO_CONF" "$BACKUP"
echo "backup -> $BACKUP"

echo "=== 1. Making sure Odoo knows which database to serve ==="
# Without this, list_db = False breaks login entirely.
DB_NAME="$(awk -F= '/^[[:space:]]*db_name[[:space:]]*=/{gsub(/[[:space:]]/,"",$2); print $2}' "$ODOO_CONF" | tail -1)"
DB_FILTER="$(awk -F= '/^[[:space:]]*dbfilter[[:space:]]*=/{gsub(/^[[:space:]]+|[[:space:]]+$/,"",$2); print $2}' "$ODOO_CONF" | tail -1)"
if [ -z "$DB_NAME" ] && [ -z "$DB_FILTER" ]; then
  mapfile -t DBS < <(sudo -u postgres psql -lqt 2>/dev/null | cut -d'|' -f1 | tr -d ' ' \
                     | grep -vE '^(template[01]|postgres)?$')
  echo "databases found: ${DBS[*]:-none}"
  if [ "${#DBS[@]}" -eq 1 ]; then
    set_opt db_name "${DBS[0]}"
    echo "db_name set to ${DBS[0]}"
  else
    echo "!! ABORT: found ${#DBS[@]} databases and no db_name/dbfilter in the config."
    echo "   Set db_name (or dbfilter) manually first, then re-run. Nothing was changed."
    rm -f "$BACKUP"; exit 1
  fi
else
  echo "already pinned: db_name='${DB_NAME}' dbfilter='${DB_FILTER}'"
fi

echo "=== 2. Disabling the database manager ==="
set_opt list_db "False"

echo "=== 3. Setting the master password ==="
if [ -s "$PW_FILE" ]; then
  MASTER_PW="$(cat "$PW_FILE")"
  echo "reusing existing password from $PW_FILE"
else
  MASTER_PW="$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32)"
  umask 077; printf '%s\n' "$MASTER_PW" > "$PW_FILE"; chmod 600 "$PW_FILE"
  echo "new password generated and stored in $PW_FILE (root-only, not printed here)"
fi
set_opt admin_passwd "$MASTER_PW"

echo "=== 4. Binding Odoo to localhost only ==="
set_opt http_interface "127.0.0.1"
# older alias, neutralise it if present so it cannot re-open the public bind
if grep -qE '^[[:space:]]*xmlrpc_interface[[:space:]]*=' "$ODOO_CONF"; then
  sed -i -E 's|^[[:space:]]*xmlrpc_interface[[:space:]]*=.*|xmlrpc_interface = 127.0.0.1|' "$ODOO_CONF"
fi

echo "--- resulting config (secrets masked) ---"
grep -vE '^[[:space:]]*(admin_passwd|db_password)' "$ODOO_CONF" | grep -E '=' | sed 's/^/    /'

echo "=== 5. Restarting Odoo ==="
service odoo restart
sleep 10

echo "=== 6. Verifying ==="
CODE="$(curl -s -o /dev/null -w '%{http_code}' -m 30 "$CHECK_URL" || echo ERR)"
echo "$CHECK_URL -> $CODE"
if [ "$CODE" != "200" ]; then
  echo "!! Site did not come back (got $CODE). ROLLING BACK."
  cp -a "$BACKUP" "$ODOO_CONF"
  service odoo restart
  sleep 10
  echo "rolled back. $CHECK_URL -> $(curl -s -o /dev/null -w '%{http_code}' -m 30 "$CHECK_URL" || echo ERR)"
  exit 1
fi

PUBIP="$(curl -s -m 10 https://api.ipify.org || echo 159.223.138.227)"
echo -n "public 8069 (${PUBIP}:8069) -> "
if timeout 8 bash -c "echo > /dev/tcp/${PUBIP}/8069" 2>/dev/null; then
  echo "STILL OPEN  <-- unexpected"
else
  echo "closed (good)"
fi
echo -n "localhost 8069 -> "
timeout 8 bash -c 'echo > /dev/tcp/127.0.0.1/8069' 2>/dev/null && echo "open (good, nginx needs it)" || echo "CLOSED <-- problem"
echo "db manager https://akt-grp.com/web/database/manager -> $(curl -s -o /dev/null -w '%{http_code}' -m 30 https://akt-grp.com/web/database/manager || echo ERR)  (expect 303/403/404, not 200)"

echo "=== 7. Firewall (only if ufw is already active) ==="
if command -v ufw >/dev/null && ufw status 2>/dev/null | grep -q "Status: active"; then
  ufw deny 8069/tcp || true
  ufw status | sed 's/^/    /'
else
  echo "ufw not active - skipped on purpose (enabling it blindly can lock out SSH)."
  echo "Odoo is bound to 127.0.0.1 now, so 8069 is already unreachable from outside."
fi

echo "=== DONE ==="
echo "Master password file: $PW_FILE   (read it with: cat $PW_FILE)"
echo "Config backup:        $BACKUP"
