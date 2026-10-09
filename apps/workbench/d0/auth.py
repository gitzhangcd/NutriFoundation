"""Private synthetic accounts and durable, revocable cookie sessions."""
from __future__ import annotations
import base64
import hashlib
import hmac
import secrets
import sqlite3
import time
from pathlib import Path

ACTORS={'SYN-ADMIN':'manager','SYN-PRODUCER-1':'producer','SYN-EXPERT-A':'expert',
        'SYN-EXPERT-B':'expert','SYN-EXPERT-C':'expert','SYN-AUDITOR':'auditor',
        'SYN-EA-EXPERT-A':'expert','SYN-EA-EXPERT-B':'expert'}

def password_hash(password:str)->str:
    if len(password)<16:raise ValueError('PASSWORD_TOO_SHORT')
    salt=secrets.token_bytes(24)
    digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,310000)
    return 'pbkdf2_sha256$310000$'+base64.b64encode(salt).decode()+'$'+base64.b64encode(digest).decode()

def verify_password(password:str,encoded:str)->bool:
    try:
        algo,rounds,salt,digest=encoded.split('$')
        count=int(rounds)
        if algo!='pbkdf2_sha256' or not 310000<=count<=1000000:return False
        actual=hashlib.pbkdf2_hmac('sha256',password.encode(),base64.b64decode(salt,validate=True),count)
        return hmac.compare_digest(actual,base64.b64decode(digest,validate=True))
    except (ValueError,TypeError):return False

def digest(value:str)->str:return hashlib.sha256(value.encode()).hexdigest()

class Auth:
    def __init__(self,path:Path,accounts:dict,ttl:int=28800):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.accounts=accounts;self.ttl=ttl
        if not accounts:raise RuntimeError('ACCOUNTS_REQUIRED')
        seen=set()
        for username,a in accounts.items():
            if not username or len(username)>80 or set(a)!={'actor','role','password_hash'}:
                raise RuntimeError('INVALID_ACCOUNT_CONFIGURATION')
            if ACTORS.get(a['actor'])!=a['role'] or a['actor'] in seen:
                raise RuntimeError('SYNTHETIC_ACTOR_REQUIRED')
            seen.add(a['actor'])
        self.dummy=password_hash(secrets.token_urlsafe(32))
        with self.conn() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,username TEXT NOT NULL,
              csrf TEXT NOT NULL,expires REAL NOT NULL,fingerprint TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS attempts(key TEXT PRIMARY KEY,count INTEGER NOT NULL,started REAL NOT NULL);
            ''')
        self.path.chmod(0o600)
    def conn(self):
        c=sqlite3.connect(self.path,timeout=10);c.row_factory=sqlite3.Row
        return c
    def login(self,username,password,address):
        key=digest(address);now=time.time()
        with self.conn() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM attempts WHERE key=?',(key,)).fetchone()
            if row and now-row['started']<300 and row['count']>=5:return None,'RATE_LIMITED'
            account=self.accounts.get(username)
            valid=verify_password(password,account['password_hash'] if account else self.dummy)
            if not valid:
                count=row['count']+1 if row and now-row['started']<300 else 1
                started=row['started'] if row and now-row['started']<300 else now
                db.execute('INSERT OR REPLACE INTO attempts VALUES(?,?,?)',(key,count,started))
                return None,'UNAUTHENTICATED'
            db.execute('DELETE FROM attempts WHERE key=?',(key,))
            db.execute('DELETE FROM sessions WHERE expires<?',(now,))
            sid=secrets.token_urlsafe(48);csrf=secrets.token_urlsafe(32)
            db.execute('INSERT INTO sessions VALUES(?,?,?,?,?)',(digest(sid),username,csrf,now+self.ttl,digest(account['password_hash'])))
            return {'id':sid,'csrf_token':csrf,'username':username,'role':account['role']},None
    def session(self,sid):
        if not sid or len(sid)>200:return None
        with self.conn() as db:
            row=db.execute('SELECT * FROM sessions WHERE id=?',(digest(sid),)).fetchone()
        if not row or row['expires']<=time.time():return None
        account=self.accounts.get(row['username'])
        if not account or row['fingerprint']!=digest(account['password_hash']):return None
        return {**dict(row),**account}
    def logout(self,sid):
        with self.conn() as db:db.execute('DELETE FROM sessions WHERE id=?',(digest(sid or ''),))
