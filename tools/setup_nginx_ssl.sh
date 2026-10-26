#!/usr/bin/env bash
# Set up nginx reverse proxy + Let's Encrypt SSL in front of Odoo for akt-grp.com
# Run as root on 159.223.138.227
set -euo pipefail

DOMAINS="akt-grp.com www.akt-grp.com odoo.akt-grp.com"
PRIMARY="akt-grp.com"
EMAIL="ahmedslah25101995@gmail.com"
ODOO_CONF="/etc/odoo/odoo.conf"

echo "=== 1. Reading Odoo config ==="
ODOO_PORT="$(awk -F= '/^[[:space:]]*(xmlrpc_port|http_port)[[:space:]]*=/{gsub(/ /,"",$2); print $2}' "$ODOO_CONF" | tail -1)"
ODOO_PORT="${ODOO_PORT:-8069}"
WORKERS="$(awk -F= '/^[[:space:]]*workers[[:space:]]*=/{gsub(/ /,"",$2); print $2}' "$ODOO_CONF" | tail -1)"
WORKERS="${WORKERS:-0}"
if [ "$WORKERS" -gt 0 ] 2>/dev/null; then CHAT_PORT=8072; else CHAT_PORT="$ODOO_PORT"; fi
echo "odoo http port = $ODOO_PORT | workers = $WORKERS | websocket port = $CHAT_PORT"

echo "=== 2. Installing nginx + certbot ==="
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq nginx certbot python3-certbot-nginx

echo "=== 3. Writing nginx site ==="
rm -f /etc/nginx/sites-enabled/default
cat > /etc/nginx/conf.d/odoo-upstream.conf <<EOF
upstream odoo_backend { server 127.0.0.1:$ODOO_PORT; }
upstream odoo_chat    { server 127.0.0.1:$CHAT_PORT; }
map \$http_upgrade \$connection_upgrade { default upgrade; '' close; }
EOF

cat > /etc/nginx/sites-available/odoo <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAINS;

    access_log /var/log/nginx/odoo.access.log;
    error_log  /var/log/nginx/odoo.error.log;

    client_max_body_size 200m;
    proxy_read_timeout 900s;
    proxy_connect_timeout 900s;
    proxy_send_timeout 900s;

    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;

    location /websocket {
        proxy_pass http://odoo_chat;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$connection_upgrade;
    }

    location /longpolling {
        proxy_pass http://odoo_chat;
    }

    location / {
        proxy_pass http://odoo_backend;
        proxy_redirect off;
    }

    location ~* /web/static/ {
        proxy_cache_valid 200 60m;
        proxy_buffering on;
        expires 864000;
        proxy_pass http://odoo_backend;
    }

    gzip on;
    gzip_types text/css text/plain text/xml application/xml application/javascript application/json;
}
EOF
ln -sf /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/odoo
nginx -t
systemctl enable --now nginx
systemctl reload nginx

echo "=== 4. Opening firewall (if ufw active) ==="
if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
  ufw allow 80/tcp || true
  ufw allow 443/tcp || true
  ufw status
else
  echo "ufw not active - skipping"
fi

echo "=== 5. Requesting Let's Encrypt certificate ==="
CERT_ARGS=""
for d in $DOMAINS; do CERT_ARGS="$CERT_ARGS -d $d"; done
certbot --nginx $CERT_ARGS --non-interactive --agree-tos -m "$EMAIL" --redirect --cert-name "$PRIMARY"

echo "=== 6. Enabling proxy_mode in Odoo ==="
cp "$ODOO_CONF" "${ODOO_CONF}.bak.$(date +%s)"
if grep -qE '^[[:space:]]*proxy_mode[[:space:]]*=' "$ODOO_CONF"; then
  sed -i -E 's/^[[:space:]]*proxy_mode[[:space:]]*=.*/proxy_mode = True/' "$ODOO_CONF"
else
  sed -i '/^\[options\]/a proxy_mode = True' "$ODOO_CONF"
fi
grep -E 'proxy_mode|xmlrpc_port|http_port|workers' "$ODOO_CONF" || true
service odoo restart

echo "=== 7. Verifying ==="
sleep 8
for d in $DOMAINS; do
  printf '%-22s http->%s  https->%s\n' "$d" \
    "$(curl -s -o /dev/null -w '%{http_code}' -m 20 "http://$d/web/login" || echo ERR)" \
    "$(curl -s -o /dev/null -w '%{http_code}' -m 20 "https://$d/web/login" || echo ERR)"
done
certbot certificates | grep -E 'Certificate Name|Domains|Expiry'
echo "=== DONE ==="
