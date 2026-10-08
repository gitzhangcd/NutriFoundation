"""Stop writer, encrypt data snapshot, verify restore, then restart writer.

Root-owned timer only; no retention deletion until the operator selects policy.
"""
import os
import subprocess
import tempfile
from datetime import datetime,timezone
from pathlib import Path
from backup import backup,seal_backup,open_backup

def main():
    os.umask(0o077)
    service='nutriwb.service'
    if not Path('/var/lib/nutriwb/data/c2_synthetic.sqlite').is_file():raise RuntimeError('WORKFLOW_DATABASE_REQUIRED')
    was_active=subprocess.run(['systemctl','is-active','--quiet',service]).returncode==0
    destination=Path('/var/backups/nutriwb');destination.mkdir(mode=0o700,parents=True,exist_ok=True)
    key=Path('/etc/nutriwb/backup.key').read_bytes()
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    sealed=destination/(stamp+'.fernet')
    try:
        if was_active:subprocess.run(['systemctl','stop',service],check=True)
        if subprocess.run(['systemctl','is-active','--quiet',service]).returncode==0:
            raise RuntimeError('OFFLINE_REQUIRED')
        with tempfile.TemporaryDirectory(prefix='nutriwb-backup-') as td:
            temp=Path(td)
            snapshot=backup(Path('/var/lib/nutriwb/data'),temp/'snapshot',offline=True)
            seal_backup(snapshot,sealed,key)
            open_backup(sealed,temp/'restored',key)
        print('ENCRYPTED_BACKUP_AND_RESTORE_VERIFIED '+sealed.name)
    finally:
        if was_active:subprocess.run(['systemctl','start',service],check=True)
if __name__=='__main__':main()
