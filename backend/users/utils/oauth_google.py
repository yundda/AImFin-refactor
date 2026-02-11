# users/oauth_google.py
import base64, hashlib, os, time, requests
from dataclasses import dataclass
from django.conf import settings

GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"

def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip('=')

def gen_pkce():
    code_verifier = b64url(os.urandom(32))
    code_challenge = b64url(hashlib.sha256(code_verifier.encode()).digest())
    return code_verifier, code_challenge

@dataclass
class OIDCIdToken:
    iss: str
    aud: str
    exp: int
    email: str | None
    name: str | None
    picture: str | None
    sub: str

    @staticmethod
    def from_jwt(jwt: str):
        # TODO: 실제 운영은 JWKS 서명 검증 필수!
        parts = jwt.split('.')
        if len(parts) != 3:
            raise ValueError('invalid jwt')
        payload_b64 = parts[1] + '=' * (-len(parts[1]) % 4)
        payload = base64.urlsafe_b64decode(payload_b64.encode())
        import json
        data = json.loads(payload)
        return OIDCIdToken(
            iss=data.get('iss', ''),
            aud=data.get('aud', ''),
            exp=int(data.get('exp', 0)),
            email=data.get('email'),
            name=data.get('name'),
            picture=data.get('picture'),
            sub=data.get('sub'),
        )

    def basic_validate(self):
        if self.aud != settings.GOOGLE_CLIENT_ID:
            raise ValueError('Invalid audience')
        if self.iss not in ['https://accounts.google.com', 'accounts.google.com']:
            raise ValueError('Invalid issuer')
        if int(time.time()) > self.exp:
            raise ValueError('ID token expired')

def build_auth_url(state: str, code_challenge: str) -> str:
    from urllib.parse import urlencode
    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': f"{settings.BASE_URL}/api/users/auth/google/callback",
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'prompt': 'select_account',
    }
    return f"{GOOGLE_AUTH}?{urlencode(params)}"

def exchange_code_for_token(code: str, code_verifier: str):
    data = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'code': code,
        'code_verifier': code_verifier,
        'grant_type': 'authorization_code',
        'redirect_uri': f"{settings.BASE_URL}/api/users/auth/google/callback",
    }
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    r = requests.post(GOOGLE_TOKEN, data=data, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()
