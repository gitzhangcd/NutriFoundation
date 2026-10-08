#!/usr/bin/env bash
# Activate a verified immutable release on an already provisioned tunnel host.
set -euo pipefail
[[ $# == 3 ]] || { echo 'usage: install_release.sh ARCHIVE SHA256 COMMIT'; exit 2; }
archive="$1"; expected="$2"; commit="$3"
[[ "$commit" =~ ^[0-9a-f]{40}$ ]] || exit 2
[[ "$expected" =~ ^[0-9a-f]{64}$ ]] || exit 2
printf '%s  %s\n' "$expected" "$archive" | sha256sum --check --status
[[ -x /opt/nutriwb/venv/bin/python && -f /etc/nutriwb/accounts.json ]]
release="/opt/nutriwb/releases/$commit"
[[ ! -e "$release" ]]
[[ ! -e /opt/nutriwb/current || -L /opt/nutriwb/current ]]
previous="$(readlink /opt/nutriwb/current || true)"
config="/var/backups/nutriwb/config-$commit"
install -d -m 0700 "$config"
for unit in nutriwb.service nutriwb-backup.service nutriwb-backup.timer; do
  if [[ -f "/etc/systemd/system/$unit" ]]; then cp -a "/etc/systemd/system/$unit" "$config/$unit"; fi
done
rollback() {
  result=$?
  if [[ "$result" != 0 ]]; then
    systemctl stop nutriwb.service || true
    if [[ -n "$previous" ]]; then
      ln -sfn "$previous" /opt/nutriwb/current
      for unit in nutriwb.service nutriwb-backup.service nutriwb-backup.timer; do
        if [[ -f "$config/$unit" ]]; then cp -a "$config/$unit" "/etc/systemd/system/$unit"; fi
      done
      systemctl daemon-reload
      systemctl start nutriwb.service || true
    fi
    echo "ACTIVATION_FAILED_ROLLBACK_ATTEMPTED=$result"
  fi
  exit "$result"
}
trap rollback EXIT
if [[ -n "$previous" ]]; then
  /opt/nutriwb/venv/bin/python "$previous/apps/workbench/d0/backup_server.py"
fi
install -d -m 0755 "$release"
tar -xzf "$archive" -C "$release"
chown -R root:root "$release"
chmod -R go-w "$release"
systemctl stop nutriwb.service 2>/dev/null || true
ln -sfn "$release" /opt/nutriwb/current
for unit in nutriwb.service nutriwb-backup.service nutriwb-backup.timer; do
  install -m 0644 "$release/apps/workbench/d0/deploy/$unit" "/etc/systemd/system/$unit"
done
systemctl daemon-reload
systemctl start nutriwb.service
for attempt in {1..20}; do
  if curl -fsS -H 'Host: 127.0.0.1:18793' http://127.0.0.1:8793/health >/dev/null; then break; fi
  sleep 1
done
curl -fsS -H 'Host: 127.0.0.1:18793' http://127.0.0.1:8793/health
printf '\nRELEASE_ACTIVE=%s\n' "$commit"
