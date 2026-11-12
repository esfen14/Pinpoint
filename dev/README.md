# `dev/` — local development launchers

Two shell scripts that start the app on a developer machine. They are not used
in production, tests or CI.

| Script | Starts | Notes |
|---|---|---|
| `start-server.sh` | The Flask backend (`server/venv/bin/flask run`) on `127.0.0.1:${PORT:-5001}` | Sets `FLASK_DEBUG=0` so the Nagios poller starts. `NAGIOS_HOST` defaults to a team Nagios box on Tailscale; override it, e.g. `NAGIOS_HOST=192.168.130.10 dev/start-server.sh` |
| `start-client.sh` | The Vite dev server on port 5173 | Proxies `/api` to `API_PROXY_TARGET` (default `http://127.0.0.1:5001`) |

Run both from any folder. They expect a `server/venv` virtual environment and
`client/node_modules` already installed (see the [root README](../README.md#development-setup)).
To use Flask's default port 5000 instead of 5001, set `PORT=5000` for the server
and `API_PROXY_TARGET=http://127.0.0.1:5000` for the client.

For a plain `flask run` and `npm run dev` without the Nagios poller, follow the
[server](../server/README.md) and [client](../client/README.md) READMEs.
