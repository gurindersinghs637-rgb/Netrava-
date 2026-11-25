"""Recovery email and one-time password update contract tests."""
import httpx
import pytest
from backend.app.core.config import settings

@pytest.fixture
def recovery(monkeypatch):
    monkeypatch.setattr(settings, 'SUPABASE_URL', 'https://provider.invalid')
    monkeypatch.setattr(settings, 'SUPABASE_KEY', 'public-test')
    monkeypatch.setattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', 'service-test')
    monkeypatch.setattr(settings, 'PASSWORD_RESET_REDIRECT_URL', 'https://netrava.example/api/v1/auth/reset-password')
    return monkeypatch

def transport(monkeypatch, handler):
    original=httpx.AsyncClient
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))

@pytest.mark.parametrize('status,expected',[(200,200),(429,429),(500,503)])
def test_recovery_email(client,recovery,status,expected):
    import json
    def handler(r):
        assert r.url.path=='/auth/v1/recover'
        assert r.url.params['redirect_to']==settings.PASSWORD_RESET_REDIRECT_URL
        assert r.headers['apikey']=='public-test'
        assert json.loads(r.content)=={'email':'person@example.com'}
        return httpx.Response(status,json={})
    transport(recovery,handler)
    r=client.post('/api/v1/auth/forgot-password',json={'email':'person@example.com'})
    assert r.status_code==expected
    if expected==200: assert 'If an account exists' in r.json()['message']

@pytest.mark.parametrize('verify_status,update_status,expected',[(200,200,200),(403,200,400),(200,422,400),(500,200,503)])
def test_reset(client,recovery,verify_status,update_status,expected):
    import json
    calls=[]
    def handler(r):
        calls.append(r.url.path)
        data=json.loads(r.content)
        if r.url.path=='/auth/v1/verify':
            assert data=={'token_hash':'one-time-recovery-proof','type':'recovery'}
            return httpx.Response(verify_status,json={'access_token':'recovery-session'})
        assert r.method=='PUT' and r.url.path=='/auth/v1/user'
        assert r.headers['authorization']=='Bearer recovery-session'
        assert data=={'password':'new-chosen-password'}
        return httpx.Response(update_status,json={})
    transport(recovery,handler)
    r=client.post('/api/v1/auth/reset-password',json={'token_hash':'one-time-recovery-proof','password':'new-chosen-password','confirm_password':'new-chosen-password'})
    assert r.status_code==expected
    assert 'recovery-session' not in r.text
    if verify_status!=200: assert len(calls)==1

def test_reset_mismatch_and_bad_email(client):
    assert client.post('/api/v1/auth/reset-password',json={'token_hash':'one-time-recovery-proof','password':'new-chosen-password','confirm_password':'different-password'}).status_code==422
    assert client.post('/api/v1/auth/forgot-password',json={'email':'invalid'}).status_code==422

def test_reset_page_security(client):
    r=client.get('/api/v1/auth/reset-password')
    assert r.status_code==200
    assert r.headers['cache-control']=='no-store'
    assert r.headers['referrer-policy']=='no-referrer'
    assert "frame-ancestors 'none'" in r.headers['content-security-policy']
    assert 'Confirm password' in r.text
    js=client.get('/api/v1/auth/reset-password.js')
    assert js.status_code==200 and 'history.replaceState' in js.text

def test_recovery_requires_config(client,recovery):
    recovery.setattr(settings,'PASSWORD_RESET_REDIRECT_URL','')
    assert client.post('/api/v1/auth/forgot-password',json={'email':'person@example.com'}).status_code==503

def test_recovery_then_new_password_login(client,recovery):
    """Controlled Auth verifies one-time proof, old password rejection and new login."""
    import json
    recovery.setattr(settings,'ENVIRONMENT','development')
    current='old-password-choice'
    used=False
    def handler(r):
        nonlocal current,used
        data=json.loads(r.content) if r.content else {}
        if r.url.path=='/auth/v1/recover': return httpx.Response(200,json={})
        if r.url.path=='/auth/v1/verify':
            if used: return httpx.Response(403,json={})
            used=True
            return httpx.Response(200,json={'access_token':'recovery-session'})
        if r.method=='PUT':
            assert r.headers['authorization']=='Bearer recovery-session'
            current=data['password']
            return httpx.Response(200,json={})
        if r.url.path=='/auth/v1/token':
            if data['password']!=current: return httpx.Response(400,json={})
            return httpx.Response(200,json={'access_token':'normal-session','user':{'id':'user','email':'person@example.com'}})
        if r.url.path=='/auth/v1/user':
            assert r.headers['authorization']=='Bearer normal-session'
            return httpx.Response(200,json={'id':'user','email':'person@example.com'})
        assert r.url.path=='/rest/v1/user_profiles'
        return httpx.Response(200,json=[{'id':'user','role':'technician','is_active':True,'clinic_id':'workspace','clinic':{'is_active':True,'clinic_name':'Private workspace'}}])
    transport(recovery,handler)
    assert client.post('/api/v1/auth/forgot-password',json={'email':'person@example.com'}).status_code==200
    payload={'token_hash':'one-time-recovery-proof','password':'new-password-choice','confirm_password':'new-password-choice'}
    assert client.post('/api/v1/auth/reset-password',json=payload).status_code==200
    assert client.post('/api/v1/auth/reset-password',json=payload).status_code==400
    assert client.post('/api/v1/auth/login',json={'email':'person@example.com','password':'old-password-choice'}).status_code==401
    login=client.post('/api/v1/auth/login',json={'email':'person@example.com','password':'new-password-choice'})
    assert login.status_code==200
    assert client.get('/api/v1/auth/me',headers={'Authorization':'Bearer '+login.json()['access_token']}).status_code==200
