import json
import os
import urllib.request


application_id = os.environ["DISCORD_APPLICATION_ID"]
bot_token = os.environ["DISCORD_BOT_TOKEN"]
command = {
    "name": "ping",
    "description": "Refresh the dead-man switch heartbeat",
    "type": 1,
}
request = urllib.request.Request(
    f"https://discord.com/api/v10/applications/{application_id}/commands",
    data=json.dumps(command).encode("utf-8"),
    method="PUT",
    headers={
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json",
        "User-Agent": "activeme-deadman-vercel",
    },
)
with urllib.request.urlopen(request, timeout=10) as response:
    if response.status != 200:
        raise SystemExit(f"Discord returned HTTP {response.status}")
print("Registered /ping command")