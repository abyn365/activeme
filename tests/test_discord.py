import importlib.util
import json
import os
import time
import unittest
from pathlib import Path

from nacl.signing import SigningKey


MODULE_PATH = Path(__file__).parents[1] / "api" / "discord.py"
SPEC = importlib.util.spec_from_file_location("discord_endpoint", MODULE_PATH)
discord_endpoint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(discord_endpoint)


class DiscordEndpointTests(unittest.TestCase):
    def test_signature_accepts_current_payload_and_rejects_replay(self):
        signing_key = SigningKey.generate()
        public_key = signing_key.verify_key.encode().hex()
        timestamp = str(int(time.time()))
        body = b'{"type":1}'
        signature = signing_key.sign(timestamp.encode() + body).signature.hex()

        self.assertTrue(
            discord_endpoint.verify_discord_request(
                body, timestamp, signature, public_key
            )
        )
        self.assertFalse(
            discord_endpoint.verify_discord_request(
                body,
                timestamp,
                signature,
                public_key,
                now=int(timestamp) + 301,
            )
        )

    def test_signature_rejects_modified_body(self):
        signing_key = SigningKey.generate()
        public_key = signing_key.verify_key.encode().hex()
        timestamp = str(int(time.time()))
        signature = signing_key.sign(timestamp.encode() + b"original").signature.hex()

        self.assertFalse(
            discord_endpoint.verify_discord_request(
                b"modified", timestamp, signature, public_key
            )
        )

    def test_command_user_supports_guild_interactions(self):
        payload = {
            "member": {"user": {"id": "123"}},
            "data": {"id": "456", "name": "ping", "type": 1},
        }
        old_value = os.environ.get("DEADMAN_ALLOWED_USER_IDS")
        os.environ["DEADMAN_ALLOWED_USER_IDS"] = "123"
        try:
            self.assertEqual(discord_endpoint.command_user(payload), "123")
            self.assertTrue(discord_endpoint.authorized(payload))
        finally:
            if old_value is None:
                os.environ.pop("DEADMAN_ALLOWED_USER_IDS", None)
            else:
                os.environ["DEADMAN_ALLOWED_USER_IDS"] = old_value


if __name__ == "__main__":
    unittest.main()