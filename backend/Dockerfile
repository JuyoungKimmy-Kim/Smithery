# Build Stage
FROM python:3.9-slim AS builder

#Proxy settings for build stage
ENV https_proxy=""
ENV no_proxy=""
COPY ./Certs/ca.crt /usr/local/share/ca-certificates/ca.crt 
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/ca.crt
RUN update-ca-certificates

WORKDIR /app
COPY backend/requirements.txt .
COPY apt.conf /etc/apt/apt.conf

#Configure pip proxy with fallback to official PyPI
RUN mkdir -p /root/.pip
RUN echo "[global]" > /root/.pip/pip.conf
RUN echo "proxy = " >> /root/.pip/pip.conf
RUN echo "index-url = internal url" >> /root/.pip/pip.conf
RUN echo "extra-index-url = https://pypi.python.org/simple" >> /root/.pip/pip.conf
RUN echo "trusted-host = repo.internal.net.python.org" >> /root/.pip/pip.conf
RUN echo "cert = /usr/local/share/ca-certificates/ca.crt" >> /root/.pip/pip.conf

RUN apt-get update -y && apt-get install -y gcc python3-dev libpq-dev
RUN pip install --no-cache-dir -r requirements.txt

#Runtime stage
FROM python:3.9-slim

#Proxy settings for runtime stage
ENV https_proxy=""
ENV no_proxy=""
COPY ./Certs/ca.crt /usr/local/share/ca-certificates/ca.crt 
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/ca.crt
RUN update-ca-certificates

WORKDIR /app
RUN apt-get update -y && apt-get install -y --no-install-recommends git
RUN git config --global http.sslVerify false
RUN git config --global http.sslCAInfo /usr/local/share/ca-certificates/ca.crt

ENV PYTHONPATH=/app:/app/backend

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy backend code
COPY backend/ ./backend/

ENV PATH=/usr/local/bin:$PATH
RUN echo "Asia/Seoul" > /etc/timezone

EXPOSE 10001
CMD ["python", "-m", "backend.main"]