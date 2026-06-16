# standoff365-bb-notifier

Watches the [Standoff 365 Bug Bounty](https://bugbounty.standoff365.com/) catalogue
and sends a Telegram message whenever a new program is published.

It polls the same public API the website uses, keeps a local record of the
programs it has already seen, and notifies only on genuinely new ones.

## How it works

1. Fetch every program from `https://api.standoff365.com/api/bug-bounty/ui/program`
   (one request, full catalogue) and keep the ones with `status == "published"` —
   the set that is publicly visible on the site.
2. Diff their ids against `state/seen.json`.
3. For each new id, send a formatted Telegram message (program name, short
   description, reward range, link).
4. Persist the new ids so they are not reported again.

The first run records the current catalogue as a baseline **without** sending
anything (so you do not get ~80 messages on startup). Set
`NOTIFY_EXISTING_ON_FIRST_RUN=true` to override.

## Configuration

All settings come from environment variables (see `.env.example`):

| Variable | Required | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | yes | — | Bot token from [@BotFather](https://t.me/BotFather). |
| `TELEGRAM_CHAT_ID` | yes | — | Target chat/channel id (`-100…`) or `@channel`. |
| `POLL_INTERVAL` | no | `600` | Seconds between polls in loop mode. |
| `STATE_PATH` | no | `state/seen.json` | Where seen ids are stored. |
| `REQUEST_TIMEOUT` | no | `30` | Per-request timeout, seconds. |
| `NOTIFY_EXISTING_ON_FIRST_RUN` | no | `false` | Notify for existing programs on first run. |
| `TELEGRAM_PROXY` | no | — | Proxy for Telegram traffic only (e.g. `socks5://127.0.0.1:10808`) where api.telegram.org is blocked. Standoff 365 stays direct. |

### Telegram blocked on the host

Some hosts (e.g. behind a Russian ISP) can reach the Standoff 365 API but not
`api.telegram.org`. Point `TELEGRAM_PROXY` at a working SOCKS5/HTTP proxy; only
Telegram traffic is routed through it. If the proxy listens on the host loopback,
the container must use host networking to reach it — add a
`docker-compose.override.yml`:

```yaml
services:
  s365watch:
    network_mode: host
```

and set `TELEGRAM_PROXY=socks5://127.0.0.1:10808` in `.env`.

### Finding your chat id

Add the bot to the target chat/channel (as admin for channels), send a message,
then read it back:

```bash
curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
```

The `chat.id` field is what you put in `TELEGRAM_CHAT_ID`.

## Running

### Local (uv)

```bash
uv sync
cp .env.example .env   # fill in token + chat id
set -a; source .env; set +a
uv run s365watch           # loop forever
uv run s365watch --once    # single cycle (for cron)
```

### Docker

```bash
cp .env.example .env   # fill in token + chat id
docker compose up -d
docker compose logs -f
```

State persists in the `state` Docker volume, so it survives restarts and reboots.
Inspect it with `docker compose exec s365watch cat /app/state/seen.json`.

### Cron (one-shot mode)

```cron
*/10 * * * * cd /opt/standoff365-bb-notifier && /usr/bin/env $(cat .env | xargs) uv run s365watch --once
```

## Development

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```

## License

MIT
