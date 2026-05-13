"""Prune long-stale rows from the web_sessions table.

Removes rows where either:
  - absolute_expires_at < now() - <grace>   (expired sessions past grace window)
  - revoked_at         < now() - <grace>    (revoked sessions past grace window)

The grace window keeps recently-killed sessions for audit / forensics before
the row is physically deleted.

Intended to run on a schedule (cron / Azure Logic App / pg_cron). Example:

    # /etc/cron.daily/harnex-web-sessions-cleanup
    docker compose -f /opt/harnex/docker-compose.yml \\
                   -f /opt/harnex/docker-compose.prod.yml \\
        exec -T api uv run python scripts/cleanup_web_sessions.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from harnex_api.config import get_settings
from harnex_api.db.session import session_scope
from harnex_api.logging import configure_logging, get_logger
from harnex_api.services.web_session import WebSessionService, get_shared_http


async def _run(grace_seconds: int) -> int:
    settings = get_settings()
    async with session_scope() as db:
        svc = WebSessionService(db, settings, get_shared_http())
        deleted = await svc.delete_expired(grace_seconds=grace_seconds)
        await db.commit()
        return deleted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--grace-days",
        type=int,
        default=7,
        help="keep expired/revoked rows for this many days before deleting (default: 7)",
    )
    args = parser.parse_args()
    configure_logging(get_settings().log_level)
    log = get_logger("harnex_api.cleanup_web_sessions")
    grace = args.grace_days * 86400
    deleted = asyncio.run(_run(grace))
    log.info("web_sessions_cleanup_done", deleted=deleted, grace_days=args.grace_days)
    return 0


if __name__ == "__main__":
    sys.exit(main())
