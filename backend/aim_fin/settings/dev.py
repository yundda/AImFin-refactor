from .base import *
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# DATABASES는 base.py에서 env('DATABASE_URL')로 로드하므로 여기서는 제거
# 만약 로컬에서 SQLite를 강제로 쓰고 싶다면 .env의 DATABASE_URL을 주석 처리하면 됨 (base.py의 default가 sqlite)

CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
CSRF_TRUSTED_ORIGINS = ["http://localhost:5173"]
CORS_ALLOW_CREDENTIALS = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False