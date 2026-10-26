"""Host-only CLI: assign a login to an existing demo profile, or reset a password.

Passwords are entered privately; never pass them as shell arguments. This CLI
has no HTTP equivalent. Existing Explorer histories and XP remain untouched.
"""
import argparse
import getpass
import os
import sys
import time
import uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from careerquest import auth
from careerquest.store import connect


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('assign','reset'))
    parser.add_argument('--username',required=True)
    parser.add_argument('--profile-id',help='Existing unassigned demo profile UUID (assign only)')
    args=parser.parse_args()
    password=getpass.getpass('New passphrase (15–128 characters): ')
    if password!=getpass.getpass('Repeat passphrase: '):parser.error('Passphrases do not match')
    username=auth.credentials(args.username,password)
    c=connect(os.getenv('DATABASE_URL') or os.getenv('CAREERQUEST_DB','var/careerquest-react.sqlite3'))
    try:
        auth.initialize(c)
        with c:
            c.execute('BEGIN IMMEDIATE')
            old=c.execute('SELECT id FROM auth_accounts WHERE username=?',(username,)).fetchone()
            if args.action=='reset':
                if not old:parser.error('Account not found')
                c.execute('UPDATE auth_accounts SET password_hash=? WHERE id=?',(auth.HASHER.hash(password),old['id']))
                c.execute('DELETE FROM auth_sessions WHERE account_id=?',(old['id'],))
            else:
                if old:parser.error('Username already exists')
                if not args.profile_id or not c.execute('SELECT id FROM profiles WHERE id=?',(args.profile_id,)).fetchone():parser.error('Supply an existing demo profile ID')
                if c.execute('SELECT id FROM auth_accounts WHERE profile_id=?',(args.profile_id,)).fetchone():parser.error('Profile already has an owner; use reset')
                c.execute('INSERT INTO auth_accounts VALUES(?,?,?,?,?)',(str(uuid.uuid4()),username,auth.HASHER.hash(password),args.profile_id,time.time()))
        print('Login updated. No Explorer history or XP changed.')
    finally:c.close()


if __name__=='__main__':main()
