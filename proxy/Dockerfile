FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /srv/proxy

RUN pip install --no-cache-dir cryptography uvloop PySocks

COPY proxy /srv/proxy

CMD ["python", "run_proxy.py"]
