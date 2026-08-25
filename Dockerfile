FROM python:3.12-slim

ARG GIT_SHA=unknown

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin ados

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/docker-entrypoint.sh \
    && chown -R ados:ados /app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV GIT_SHA=${GIT_SHA}
ENV SOURCE_REVISION=${GIT_SHA}

EXPOSE 8080

USER ados

HEALTHCHECK --interval=15s --timeout=5s --start-period=90s --retries=5 \
    CMD curl -sf http://127.0.0.1:8080/liveness || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "bot.py"]
