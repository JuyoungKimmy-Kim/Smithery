#!/bin/bash

# SSL 인증서 디렉토리 생성
mkdir -p ssl

# 자체 서명된 SSL 인증서 생성
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=KR/ST=Seoul/L=Seoul/O=Development/CN=localhost"

echo "SSL 인증서가 생성되었습니다:"
echo "- ssl/cert.pem"
echo "- ssl/key.pem" 