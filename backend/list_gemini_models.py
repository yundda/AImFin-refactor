import requests
import os
import django
import sys

# Django 환경 설정
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aim_fin.settings.dev")
django.setup()

from django.conf import settings

def list_models():
    api_key = settings.GEMINI_API_KEY
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    print(f"Listing models using key (length {len(api_key)})...")
    resp = requests.get(url)
    if resp.status_code == 200:
        models = resp.json().get("models", [])
        for m in models:
            print(f"- {m['name']} (Supported: {m['supportedGenerationMethods']})")
    else:
        print(f"Error {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    list_models()
