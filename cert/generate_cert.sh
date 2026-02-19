#!/bin/sh

# Create cert directory if not exists
mkdir -p cert

# Generate Self-Signed Certificate
# Key: nginx.key (RSA 2048)
# Cert: nginx.crt (Valid for 365 days)
# Subject: CN=localhost
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout cert/nginx.key \
  -out cert/nginx.crt \
  -subj "/C=KR/ST=Seoul/L=Gangnam/O=AImFin/OU=Development/CN=localhost"

echo "Certificate (nginx.crt) and Key (nginx.key) generated in cert/"
