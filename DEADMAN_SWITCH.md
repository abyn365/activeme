# Discord dead-man switch

The scheduled workflow only creates an automated commit when a recent Discord heartbeat exists. By default, a heartbeat is valid for 7 days. A missing or stale heartbeat stops the automated commit without exposing any secret to Discord.

## Vercel setup

1. Create a Discord application and bot. Copy the application's **Public Key**; no privileged intents are required.
2. Create a fine-grained GitHub token for this repository with **Actions: Read and write** permission. Store it only as `DEADMAN_GITHUB_TOKEN` in Vercel.
3. Deploy this repository to Vercel. Set these Vercel environment variables for Production:

   - `DISCORD_PUBLIC_KEY`: Discord application's Public Key.
   - `DEADMAN_GITHUB_TOKEN`: fine-grained token from step 2; never commit it.
   - `GITHUB_REPOSITORY`: `owner/repository`.
   - `DEADMAN_ALLOWED_USER_IDS`: comma-separated Discord user IDs.
   - `DEADMAN_ALLOWED_GUILD_IDS`: optional comma-separated server IDs. If set, `/ping` is rejected outside those servers.

4. In Discord Developer Portal, set the **Interactions Endpoint URL** to `https://YOUR_VERCEL_DOMAIN/api/discord` and save. Discord will reject the URL unless its signature verification succeeds.
5. Register the command once from a trusted shell, with the bot token supplied only through the environment:

   `DISCORD_APPLICATION_ID=... DISCORD_BOT_TOKEN=... python3 scripts/register_discord_command.py`

6. In the repository, set the `DEADMAN_MAX_AGE_DAYS` Actions variable if 7 days is not appropriate.

The Vercel function verifies Discord's Ed25519 signature and rejects requests older than five minutes before parsing the command. It only submits a `repository_dispatch` event; it never receives a GitHub write token capable of changing repository contents. The GitHub workflow writes `.deadman/last_ping.json` using its short-lived workflow token and records the current GitHub runner time, rather than trusting a Discord-provided timestamp. Secrets are never placed in workflow files or repository contents.