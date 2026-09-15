import json
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 17:
        sys.exit(1)

    (
        file_name,
        now,
        owner,
        repository,
        branch,
        last_commit,
        last_sha,
        next_commit_at,
        days_since,
        days_until,
        status,
        event,
        reason,
        scheduled_delay,
        commit_sha,
        commit_message,
    ) = sys.argv[1:17]

    history_limit = int(sys.argv[17]) if len(sys.argv) > 17 else 100

    file = Path(file_name)
    if file.exists():
        try:
            data = json.loads(file.read_text())
        except (json.JSONDecodeError, OSError):
            data = {}
    else:
        data = {}

    data.setdefault("version", 2)
    data.setdefault("history", [])

    data.update({
        "repository": repository,
        "owner": owner,
        "branch": branch,
        "last_commit": last_commit,
        "last_commit_sha": last_sha,
        "next_commit_at": next_commit_at,
        "days_since_last_commit": int(days_since),
        "days_until_next_commit": int(days_until),
        "status": status,
        "last_checked": now,
        "scheduler": {
            "min_delay_days": int(data.get("scheduler", {}).get("min_delay_days", scheduled_delay or 0)),
            "max_delay_days": int(data.get("scheduler", {}).get("max_delay_days", scheduled_delay or 0)),
            "selected_delay_days": int(scheduled_delay or 0)
        }
    })

    entry = {
        "date": now,
        "event": event,
        "reason": reason,
        "next_commit_at": next_commit_at
    }

    if commit_sha:
        entry["commit_sha"] = commit_sha
    if commit_message:
        entry["commit_message"] = commit_message
    if scheduled_delay:
        entry["delay_days"] = int(scheduled_delay)

    data["history"].append(entry)
    data["history"] = data["history"][-history_limit:]

    file.write_text(json.dumps(data, indent=2) + "\n")

if __name__ == "__main__":
    main()
