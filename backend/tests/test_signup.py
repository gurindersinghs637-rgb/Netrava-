"""Registration contracts and trusted profile persistence checks."""
import httpx
import pytest
from backend.app.core.config import settings

BASE = {'email': 'new.person@example.com', 'full_name': 'New Person', 'phone': '+919876543210',
        'password': 'strong-password-123', 'confirm_password': 'strong-password-123'}

@pytest.mark.parametrize('change', [
    {'email': 'invalid'}, {'phone': ''}, {'phone': 'abc1234567'}, {'phone': '123'}, {'full_name': '  '}, {'password': 'short'}, {'password': 'Hello@1234', 'confirm_password': 'Hello@1234'},
    {'confirm_password': 'different-password'}, {'role': 'administrator'},
    {'clinic_id': 'clinic-1'}, {'is_active': True},
])
def test_signup_validation(client, change):
    response = client.post('/api/v1/auth/signup', json={**BASE, **change})
    assert response.status_code == 422
    assert BASE['password'] not in response.text

@pytest.mark.parametrize('scenario,expected', [
    ('created', 201), ('duplicate', 409), ('obfuscated', 409),
    ('missing_profile', 503), ('unsafe_profile', 503), ('outage', 503),
    ('rate_limit', 429), ('rejected', 400),
])
def test_signup_provider_and_profile(client, monkeypatch, scenario, expected):
    monkeypatch.setattr(settings, 'SUPABASE_URL', 'https://provider.invalid')
    monkeypatch.setattr(settings, 'SUPABASE_KEY', 'public-test')
    monkeypatch.setattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', 'service-test')
    def handler(request):
        if request.url.path == '/auth/v1/admin/users':
            return httpx.Response(200, json={'users': []})
        if request.url.path == '/auth/v1/signup':
            import json
            payload = json.loads(request.content)
            assert payload['data'] == {'full_name': 'New Person', 'phone': '+919876543210'}
            assert 'confirm_password' not in payload
            assert request.headers['apikey'] == 'public-test'
            if scenario == 'duplicate':
                return httpx.Response(422, json={'code': 'user_already_exists'})
            if scenario == 'outage':
                return httpx.Response(500, json={'message': 'PRIVATE'})
            if scenario == 'rate_limit':
                return httpx.Response(429, json={})
            if scenario == 'rejected':
                return httpx.Response(400, json={})
            return httpx.Response(200, json={'id': 'new-id', 'email_confirmed_at': '2026-11-14T00:00:00Z', 'identities': [] if scenario == 'obfuscated' else [{'id': 'identity'}]})
        assert request.url.path == '/rest/v1/user_profiles'
        assert request.headers['apikey'] == 'service-test'
        assert request.url.params['id'] == 'eq.new-id'
        rows = [] if scenario == 'missing_profile' else [{'id': 'new-id', 'role': 'administrator' if scenario == 'unsafe_profile' else 'technician', 'email': BASE['email'], 'phone': BASE['phone'], 'is_active': True, 'clinic_id': 'private-clinic'}]
        return httpx.Response(200, json=rows)
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kw: original(transport=httpx.MockTransport(handler), **kw))
    response = client.post('/api/v1/auth/signup', json=BASE)
    assert response.status_code == expected
    assert 'service-test' not in response.text
    assert 'PRIVATE' not in response.text
    if expected == 201:
        assert response.json()['status'] == 'active'
        assert 'access_token' not in response.json()

@pytest.mark.parametrize('confirmation_required', [False, True])
def test_new_signup_can_login_and_me_without_approval(client, monkeypatch, confirmation_required):
    """Exercise the new identity through signup, password login and trusted /me."""
    monkeypatch.setattr(settings, 'ENVIRONMENT', 'development')
    monkeypatch.setattr(settings, 'SUPABASE_URL', 'https://provider.invalid')
    monkeypatch.setattr(settings, 'SUPABASE_KEY', 'public-test')
    monkeypatch.setattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', 'service-test')
    profile = {'id': 'brand-new-user', 'full_name': BASE['full_name'], 'email': BASE['email'],
               'phone': BASE['phone'], 'role': 'technician', 'is_active': True,
               'clinic_id': 'private-clinic', 'clinic': {'clinic_name': 'Personal screening workspace', 'is_active': True}}
    identity = {'id': 'brand-new-user', 'email': BASE['email']}
    created = False
    def handler(request):
        nonlocal created
        if request.url.path == '/auth/v1/admin/users':
            return httpx.Response(200, json={'users': []})
        if request.url.path == '/auth/v1/signup':
            import json
            assert json.loads(request.content)['password'] == BASE['password']
            created = True
            return httpx.Response(200, json={'user': identity, **({} if confirmation_required else {'access_token': 'signup-token'})})
        assert created
        if request.url.path == '/auth/v1/token':
            import json
            assert json.loads(request.content)['password'] == BASE['password']
            return httpx.Response(200, json={'access_token': 'new-user-token', 'user': identity})
        if request.url.path == '/auth/v1/user':
            assert request.headers['authorization'] == 'Bearer new-user-token'
            return httpx.Response(200, json=identity)
        return httpx.Response(200, json=[profile])
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kw: original(transport=httpx.MockTransport(handler), **kw))
    signup = client.post('/api/v1/auth/signup', json=BASE)
    assert signup.status_code == 201
    assert signup.json()['status'] == ('email_confirmation_required' if confirmation_required else 'active')
    # Confirmation is represented as completed before password login in that case.
    login = client.post('/api/v1/auth/login', json={'email': BASE['email'], 'password': BASE['password']})
    assert login.status_code == 200
    me = client.get('/api/v1/auth/me', headers={'Authorization': 'Bearer '+login.json()['access_token']})
    assert me.status_code == 200
    assert me.json()['role'] == 'technician'
    assert me.json()['email'] == BASE['email']

@pytest.mark.parametrize('body,expected', [
    ({'msg': 'User already registered'}, 'EMAIL_EXISTS'),
    ({'code': 'weak_password'}, 'WEAK_PASSWORD'),
    ({'code': 422, 'error_code': 'weak_password', 'msg': 'Password should be at least 12 characters.'}, 'WEAK_PASSWORD'),
    ({'code': 'over_email_send_rate_limit'}, 'EMAIL_RATE_LIMITED'),
    ({'code': 'email_address_not_authorized'}, 'EMAIL_DELIVERY_RESTRICTED'),
])
def test_signup_safe_provider_errors(client, monkeypatch, body, expected):
    monkeypatch.setattr(settings, 'SUPABASE_URL', 'https://provider.invalid')
    monkeypatch.setattr(settings, 'SUPABASE_KEY', 'public-test')
    monkeypatch.setattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', 'service-test')
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kw: original(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={'users': []}) if r.url.path == '/auth/v1/admin/users' else httpx.Response(400, json=body)), **kw))
    response = client.post('/api/v1/auth/signup', json=BASE)
    assert response.json()['detail']['error'] == expected


@pytest.mark.parametrize('confirmed', [False, True])
def test_existing_identity_never_resubmitted_or_password_changed(client, monkeypatch, confirmed):
    monkeypatch.setattr(settings, 'SUPABASE_URL', 'https://provider.invalid')
    monkeypatch.setattr(settings, 'SUPABASE_KEY', 'public-test')
    monkeypatch.setattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', 'service-test')
    def handler(request):
        assert request.method == 'GET'
        assert request.url.path == '/auth/v1/admin/users'
        return httpx.Response(200, json={'users': [{'email': BASE['email'].upper(), 'email_confirmed_at': 'date' if confirmed else None}]})
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kw: original(transport=httpx.MockTransport(handler), **kw))
    response=client.post('/api/v1/auth/signup',json=BASE)
    assert response.status_code==409
    assert 'existing password or use Forgot Password' in response.json()['detail']['message']


@pytest.mark.parametrize('provider_status,body,expected_status,expected_code', [
    (500, {'code': 'unexpected_failure', 'msg': 'Error sending confirmation email'}, 503, 'SIGNUP_EMAIL_DELIVERY_FAILED'),
    (500, {'code': 'unexpected_failure', 'msg': 'Error sending confirmation mail'}, 503, 'SIGNUP_EMAIL_DELIVERY_FAILED'),
    (500, {'code': 'unexpected_failure', 'msg': 'Database error saving new user'}, 503, 'SIGNUP_DATABASE_ERROR'),
    (504, {'code': 'request_timeout'}, 503, 'SIGNUP_PROVIDER_TIMEOUT'),
    (429, {'code': 'over_email_send_rate_limit'}, 429, 'EMAIL_RATE_LIMITED'),
    (403, {'code': 'signup_disabled'}, 400, 'SIGNUP_DISABLED'),
])
def test_signup_provider_failures_are_actionable(client, monkeypatch, provider_status, body, expected_status, expected_code):
    """Keep provider failure categories without exposing provider messages or secrets."""
    monkeypatch.setattr(settings, 'SUPABASE_URL', 'https://provider.invalid')
    monkeypatch.setattr(settings, 'SUPABASE_KEY', 'public-test')
    monkeypatch.setattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', 'service-test')
    original = httpx.AsyncClient
    def handler(request):
        if request.url.path == '/auth/v1/admin/users':
            return httpx.Response(200, json={'users': []})
        assert request.url.path == '/auth/v1/signup'
        return httpx.Response(provider_status, json=body)
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kw: original(transport=httpx.MockTransport(handler), **kw))
    response = client.post('/api/v1/auth/signup', json=BASE)
    assert response.status_code == expected_status
    assert response.json()['detail']['error'] == expected_code
    assert 'service-test' not in response.text


@pytest.mark.parametrize('stage,path', [
    ('duplicate_check', '/auth/v1/admin/users'),
    ('signup', '/auth/v1/signup'),
    ('profile_verification', '/rest/v1/user_profiles'),
])
def test_signup_failure_diagnostics_never_include_private_values(client, monkeypatch, stage, path):
    import io
    from loguru import logger
    monkeypatch.setattr(settings, 'SUPABASE_URL', 'https://provider.invalid')
    monkeypatch.setattr(settings, 'SUPABASE_KEY', 'public-test')
    monkeypatch.setattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', 'service-test')
    original = httpx.AsyncClient
    def handler(request):
        if request.url.path == path:
            return httpx.Response(500, json={'code': BASE['email'], 'message': 'DO_NOT_LOG_PROVIDER_BODY'})
        if request.url.path == '/auth/v1/admin/users':
            return httpx.Response(200, json={'users': []})
        return httpx.Response(200, json={'id': 'new-id', 'identities': [{'id': 'identity'}]})
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kw: original(transport=httpx.MockTransport(handler), **kw))
    output = io.StringIO()
    sink = logger.add(output, format='{message}', level='ERROR')
    try:
        response = client.post('/api/v1/auth/signup', json=BASE)
    finally:
        logger.remove(sink)
    assert response.status_code == 503
    assert f'stage={stage} status=500 provider_code=unrecognized' in output.getvalue()
    for value in [BASE['email'], BASE['password'], 'service-test', 'DO_NOT_LOG_PROVIDER_BODY']:
        assert value not in output.getvalue()
        assert value not in response.text


def test_login_unconfirmed_email_has_explicit_message(client, monkeypatch):
    monkeypatch.setattr(settings, 'SUPABASE_URL', 'https://provider.invalid')
    monkeypatch.setattr(settings, 'SUPABASE_KEY', 'public-test')
    monkeypatch.setattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', 'service-test')
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kw: original(transport=httpx.MockTransport(
        lambda r: httpx.Response(400, json={'error_code': 'email_not_confirmed', 'error_description': 'PRIVATE_PROVIDER_MESSAGE'})
    ), **kw))
    response = client.post('/api/v1/auth/login', json={'email': BASE['email'], 'password': BASE['password']})
    assert response.status_code == 401
    assert response.json()['detail']['error'] == 'EMAIL_NOT_CONFIRMED'
    assert 'confirm your email' in response.json()['detail']['message']
    assert 'PRIVATE_PROVIDER_MESSAGE' not in response.text
