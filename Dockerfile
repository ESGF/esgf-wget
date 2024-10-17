# Makes updating the base image simple                                                                                                                                                                                                                   
# docker build -t wgetapi --build-arg=BASE_IMAGE=debian:buster-slim .
ARG BASE_IMAGE
FROM $BASE_IMAGE
WORKDIR /wgetApi
# Combine calls reduces size/layers of image
# Use non-standard username and set uid/gid to non-normal value
RUN apt update && \
      apt install -y --no-install-recommends python3 python3-pip && \
      rm -rf /var/lib/apy/lists && \
      useradd -M -u 10000 -U wgetapi && \
      pip3 install gunicorn requests "django>=3.0,<3.1"
USER wgetapi
COPY --chown=10000:10000 esgf_wget esgf_wget
COPY --chown=10000:10000 manage.py .

EXPOSE 8000
ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8000", "esgf_wget.wsgi", "--worker-tmp-dir", "/dev/shm", "--workers", "2", "--threads", "2", "--worker-class", "gthread"]
