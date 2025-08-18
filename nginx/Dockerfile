FROM nginx:alpine

# SSL 인증서 생성
RUN apk add --no-cache openssl

# SSL 디렉토리 생성
RUN mkdir -p /etc/nginx/ssl

# 자체 서명된 SSL 인증서 생성
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/key.pem \
    -out /etc/nginx/ssl/cert.pem \
    -subj "/C=KR/ST=Seoul/L=Seoul/O=Samsung/CN=ssai.samsungds.net"

# Nginx 설정 파일 복사
COPY default.conf /etc/nginx/conf.d/default.conf

# 포트 노출
EXPOSE 9631

# Nginx 시작
CMD ["nginx", "-g", "daemon off;"] 