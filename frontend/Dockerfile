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

# Build for static export
RUN npm run build -- --no-lint
RUN npx next export

#Runtime stage - Nginx
FROM nginx:alpine

# Copy nginx configuration
COPY nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf

# Copy static files from Next.js build
COPY --from=builder /app/out /usr/share/nginx/html
COPY --from=builder /app/public /usr/share/nginx/html

EXPOSE 80 443
CMD ["nginx", "-g", "daemon off;"]