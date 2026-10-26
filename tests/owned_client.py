"""Authenticate existing domain/API regression fixtures through the real login API.

These fixtures previously used public Explorer IDs. Each fixture Explorer now
gets its own test-only account. Security tests use the unwrapped TestClient.
"""
import re
import threading
import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient as RawClient
from careerquest import api

_owners={}
_receipts={}
_lock=threading.RLock()
PASSWORD='test-only long passphrase for fixtures'


class TestClient(RawClient):
    __test__=False
    def __enter__(self):
        # Legacy tests deliberately vary developer-mode flags, but their storage
        # remains an isolated SQLite fixture. Cloud config has separate tests.
        with patch('careerquest.auth.check_configuration'):
            return super().__enter__()
    def _new_session(self):
        response=super().request('POST','/api/auth/register',json={'username':'test_'+uuid.uuid4().hex[:20],'password':PASSWORD,'demo_ack':True},headers={'x-cq-request':'1','cookie':''})
        if response.status_code!=200:raise AssertionError(f'Fixture registration failed: {response.status_code} {response.text}')
        return {'cookie':response.cookies.get('cq_session'),'csrf':response.json()['csrf_token'],'created':False}
    def request(self,method,url,**kwargs):
        path=str(url);match=re.search(r'/profiles/([^/]+)',path)
        if '/api/auth/' in path:return super().request(method,url,**kwargs)
        with _lock:
            current=getattr(self,'owner',None)
            if method.upper()=='POST' and path=='/api/profiles':
                body=kwargs.get('json') or {};key=body.get('creation_key')
                current=_receipts.get((api.DB,key)) if key else (current if current and not current['created'] else None)
                if not current:current=self._new_session()
                if key:_receipts[(api.DB,key)]=current
            elif match:current=_owners.get((api.DB,match.group(1)),current)
            if not current:current=self._new_session()
            self.owner=current
        headers=dict(kwargs.pop('headers',{}) or {})
        headers.update({'x-csrf-token':current['csrf'],'x-cq-request':'1','cookie':'cq_session='+current['cookie']})
        response=super().request(method,url,headers=headers,**kwargs)
        if method.upper()=='POST' and path=='/api/profiles' and response.status_code==200:
            with _lock:
                current['created']=True
                _owners[(api.DB,response.json()['profile']['id'])]=current
        return response
