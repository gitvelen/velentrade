FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_INDEX_URL=http://mirrors.cloud.aliyuncs.com/pypi/simple/ \
    PIP_TRUSTED_HOST=mirrors.cloud.aliyuncs.com \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=10 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml ./
COPY wheelhouse ./wheelhouse

RUN python -c 'import pathlib, tomllib; deps = tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["dependencies"]; pathlib.Path("/tmp/requirements.txt").write_text("\n".join(deps) + "\n")' \
    && if find wheelhouse -maxdepth 1 -type f \( -name "*.whl" -o -name "*.tar.gz" \) | grep -q .; then \
        python -m pip install --no-cache-dir --no-index --find-links=/app/wheelhouse -r /tmp/requirements.txt; \
      else \
        python -m pip install --no-cache-dir -r /tmp/requirements.txt; \
      fi

COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations
COPY scripts ./scripts
COPY frontend/dist ./frontend/dist
