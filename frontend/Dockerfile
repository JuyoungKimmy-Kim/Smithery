#Build stage
FROM node:18-alpine AS builder

#Proxy settings for build stage
ENV https_proxy=""
ENV no_proxy=""
COPY ./Certs/ca.crt /usr/local/share/ca-certificates/ca.crt 
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/ca.crt
RUN update-ca-certificates

WORKDIR /app

#proxy settings
RUN echo "http://xxx" > /etc/apk.proxy
RUN echo "https://xxx" >> /etc/apk.proxy
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/ca.crt

#npm setting
RUN npm config set strict-ssl false
RUN npm config set registry http://xxx
RUN npm config set proxy http://xxx
RUN npm config set https-proxy http://xxx

COPY frontend/package.json ./
RUN npm install --include=dev

COPY frontend/ .

RUN npm run build -- --no-lint

#Runtime stage
FROM node:18-alpine

WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.js ./next.config.js

EXPOSE 3000
CMD ["npm", "start"]