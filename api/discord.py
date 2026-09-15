import json
import os
import re
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey


MAX_BODY_BYTES = 1_000_000
MAX_SIGNATURE_AGE_SECONDS = 300
REPOSITORY_PATTERN = re.compile(r"^[^/\s]+/[^/\s]+$")


def configured_ids(name):
    return {
        value.strip()
        for value in os.environ.get(name, "").split(",")
        if value.strip()
    }


def verify_discord_request(body, timestamp, signature, public_key, now=None):
    if not timestamp or not signature or not public_key:
        return False
    try:
        timestamp_value = int(timestamp)
        if abs((time.time() if now is None else now) - timestamp_value) > MAX_SIGNATURE_AGE_SECONDS:
            return False
        VerifyKey(bytes.fromhex(public_key)).verify(
            timestamp.encode("ascii") + body,
            bytes.fromhex(signature),
        )
    except (ValueError, TypeError, UnicodeEncodeError, BadSignatureError):
        return False
    return True


def discord_response(content, ephemeral=True):
    flags = 64 if ephemeral else 0
    return {"type": 4, "data": {"content": content, "flags": flags}}


def send_github_ping(user_id):
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("DEADMAN_GITHUB_TOKEN", "")
    if not token or not REPOSITORY_PATTERN.fullmatch(repository):
        raise RuntimeError("GitHub dispatch configuration is invalid")

    payload = json.dumps(
        {
            "event_type": "deadman_ping",
            "client_payload": {"discord_user_id": str(user_id)},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/dispatches",
        data=payload,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "activeme-deadman-vercel",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=2) as response:
        if response.status != 204:
            raise RuntimeError("GitHub dispatch failed")


def command_user(payload):
    member = payload.get("member") or {}
    return (member.get("user") or payload.get("user") or {}).get("id")


def authorized(payload):
    user_id = command_user(payload)
    allowed_users = configured_ids("DEADMAN_ALLOWED_USER_IDS")
    allowed_guilds = configured_ids("DEADMAN_ALLOWED_GUILD_IDS")
    return (
        bool(user_id)
        and str(user_id) in allowed_users
        and (not allowed_guilds or str(payload.get("guild_id")) in allowed_guilds)
    )


class handler(BaseHTTPRequestHandler):
    def log_message(self, format_string, *args):
        return

    def send_json(self, status, value):
        body = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            self.send_json(400, {"error": "invalid request"})
            return
        if content_length < 0 or content_length > MAX_BODY_BYTES:
            self.send_json(413, {"error": "request too large"})
            return

        body = self.rfile.read(content_length)
        if not verify_discord_request(
            body,
            self.headers.get("X-Signature-Timestamp", ""),
            self.headers.get("X-Signature-Ed25519", ""),
            os.environ.get("DISCORD_PUBLIC_KEY", ""),
        ):
            self.send_json(401, {"error": "invalid request"})
            return

        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_json(400, {"error": "invalid request"})
            return

        if payload.get("type") == 1:
            self.send_json(200, {"type": 1})
            return
        command = payload.get("data") or {}
        if (
            payload.get("type") != 2
            or command.get("type") != 1
            or command.get("name") != "ping"
        ):
            self.send_json(404, {"error": "unknown command"})
            return
        if not authorized(payload):
            self.send_json(200, discord_response("Not authorized."))
            return

        try:
            send_github_ping(command_user(payload))
        except (OSError, urllib.error.URLError, RuntimeError):
            self.send_json(200, discord_response("Heartbeat could not be recorded."))
            return
        self.send_json(200, discord_response("Heartbeat recorded."))

    def do_GET(self):
        self.send_json(405, {"error": "method not allowed"})