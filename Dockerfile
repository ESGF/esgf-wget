FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

RUN groupadd -r -g 1000 wgetapi && \
      useradd -r -m -u 1000 -g wgetapi wgetapi

RUN apt-get update && \
      apt-get install -y python3 python3-pip && \
      apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
      rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --upgrade pip && \
      pip3 install --upgrade setuptools && \
      pip3 install gunicorn && \
      pip3 install -r requirements.txt

COPY --chown=1000:1000 esgf_wget esgf_wget
COPY --chown=1000:1000 manage.py .
COPY --chown=1000:1000 gunicorn_conf.py .
COPY --chown=1000:1000 esgf-wget-config.cfg.globus esgf-wget-config.cfg

ENV ESGF_WGET_CONFIG=/app/esgf-wget-config.cfg

USER wgetapi
EXPOSE 3000

ENTRYPOINT ["/usr/local/bin/gunicorn", "-c", "gunicorn_conf.py", "esgf_wget.wsgi", "--chdir=/app"]

# WORKDIR /wgetApi
# # Combine calls reduces size/layers of image
# # Use non-standard username and set uid/gid to non-normal value
# RUN apt update && \
#       apt install -y --no-install-recommends python3 python3-pip && \
#       rm -rf /var/lib/apy/lists && \
#       useradd -M -u 10000 -U wgetapi && \
#       pip3 install gunicorn "django>=3.0,<3.1"
# USER wgetapi
# COPY --chown=10000:10000 esgf_wget esgf_wget
# COPY --chown=10000:10000 manage.py .
# 
# EXPOSE 8000
# ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8000", "esgf_wget.wsgi", "--worker-tmp-dir", "/dev/shm", "--workers", "2", "--threads", "2", "--worker-class", "gthread"]
