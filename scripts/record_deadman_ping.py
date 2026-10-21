import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: record_deadman_ping.py STATE_FILE DISCORD_USER_ID")

    state_file = Path(sys.argv[1])
    user_id = sys.argv[2]
    if not user_id.isdigit():
        raise SystemExit("discord user id must be numeric")

    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        json.dumps(
            {
                "last_ping_at": datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
                "discord_user_id": user_id,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()