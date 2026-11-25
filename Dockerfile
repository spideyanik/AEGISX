FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AEGISX_HOME=/data

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY aegisx ./aegisx
RUN pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 aegisx && mkdir /data && chown aegisx:aegisx /data
USER aegisx
VOLUME ["/data"]

ENTRYPOINT ["aegisx"]
CMD ["--help"]
