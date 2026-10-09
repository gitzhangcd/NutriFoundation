"""Create local private credential files; never print passwords or tokens."""
import argparse
import json
import os
import secrets
from pathlib import Path
from cryptography.fernet import Fernet
from auth import password_hash
NAMES=[('r0','SYN-EXPERT-A','expert'),('r1','SYN-EXPERT-B','expert'),('r2','SYN-EXPERT-C','expert'),
       ('ea1','SYN-EA-EXPERT-A','expert'),('ea2','SYN-EA-EXPERT-B','expert'),
       ('manager','SYN-ADMIN','manager'),('producer','SYN-PRODUCER-1','producer'),('auditor','SYN-AUDITOR','auditor')]
def provision(directory:Path):
    directory.mkdir(mode=0o700,parents=True,exist_ok=False)
    accounts={};credentials={'url':'http://127.0.0.1:18793','accounts':{}}
    for name,actor,role in NAMES:
        password=secrets.token_urlsafe(24)
        accounts[name]={'actor':actor,'role':role,'password_hash':password_hash(password)}
        credentials['accounts'][name]={'password':password,'role':role}
    credentials['future_https_access']={'username':'nutri-staging','password':secrets.token_urlsafe(24),'activation':'DEFERRED_SSH_TUNNEL_ONLY'}
    for name,value in [('accounts.json',accounts),('credentials.json',credentials)]:
        p=directory/name;p.write_text(json.dumps(value,indent=2)+'\n');p.chmod(0o600)
    p=directory/'backup.key';p.write_bytes(Fernet.generate_key());p.chmod(0o600)
    print('PRIVATE_CREDENTIAL_FILES_CREATED')
if __name__=='__main__':
    os.umask(0o077);p=argparse.ArgumentParser();p.add_argument('directory',type=Path);provision(p.parse_args().directory)
