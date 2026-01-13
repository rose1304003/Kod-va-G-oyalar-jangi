import os


def _parse_admin_ids() -> set[int]:
    raw = os.getenv("ADMIN_IDS", "")
    ids = set()
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        try:
            ids.add(int(entry))
        except ValueError:
            continue
    return ids


BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = _parse_admin_ids()
