#!/bin/sh
set -e
cd /app
if [ -z "${DATABASE_URL}" ]; then
  export DATABASE_URL="$(
python - <<'PY'
import os
from urllib.parse import quote_plus

user = os.environ.get("POSTGRES_USER", "harnex")
password = quote_plus(os.environ.get("POSTGRES_PASSWORD", ""))
host = os.environ.get("POSTGRES_HOST", "postgres")
port = os.environ.get("POSTGRES_PORT", "5432")
db = os.environ.get("POSTGRES_DB", "harnex")
print(f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}")
PY
  )"
fi
alembic upgrade head
exec "$@"
