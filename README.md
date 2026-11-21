# neckrez-cli

Command-line client for [Neckrez](https://neckrez.tech): rent a VPS, dedicated CPU, NVIDIA GPU or bare metal server, pay with crypto, and manage it from your terminal.

- One file, Python 3.8+, standard library only. Nothing to `pip install`.
- Works with the public [Neckrez REST API](https://neckrez.tech/docs).
- Servers run on Vultr, DigitalOcean, Linode and Hetzner, billed by the hour from one prepaid balance.

## Install

```bash
curl -fsSL https://neckrez.tech/cli/neckrez -o /usr/local/bin/neckrez
chmod +x /usr/local/bin/neckrez
neckrez --version
```

Or clone this repository and run `./neckrez`.

## Log in

Create an API key in the dashboard at [neckrez.tech/dashboard/api-keys](https://neckrez.tech/dashboard/api-keys), then:

```bash
neckrez login            # asks for the key, input is hidden
```

The key is saved to `~/.config/neckrez/config.json` (readable only by you). `NECKREZ_API_KEY` and `NECKREZ_API_URL` override the saved config, which is handy in CI.

## Quick start

```bash
neckrez plans --type vps                 # live prices, no key needed
neckrez locations                        # live locations, no key needed
neckrez deploy web-1 --plan ion --location AMS --ssh-key --wait
neckrez ls
neckrez ssh web-1
neckrez rm web-1                         # billing stops
```

## Commands

| Command | What it does |
|---|---|
| `login` / `logout` | Save or forget the API key |
| `balance` | Prepaid balance and recent transactions |
| `plans [--type vps\|dedicated\|gpu\|metal] [--provider P] [--max-price N] [--available]` | Plans with live prices |
| `locations [--provider P]` | Locations |
| `os [NAME] [--provider P]` | Operating systems and versions |
| `deploy NAME --plan ID --location CODE [options]` | Create a server, or up to 10 with `--count` |
| `ls` | Your servers |
| `show SERVER` | Full details of one server |
| `start` / `stop` / `reboot` / `swap-ip SERVER [--wait]` | Power actions and a new public IPv4 |
| `rm SERVER [-y]` | Delete a server |
| `ssh SERVER [-- ssh args]` | Open an SSH session |
| `backups ls\|create\|restore\|rm` | Snapshots kept for 7 days |

`SERVER` is an id, an id prefix or an exact name. Add `--json` to any command for machine-readable output.

Useful `deploy` options: `--provider vultr|digitalocean|linode|hetzner`, `--os ubuntu --os-version 24.04`, `--app docker`, `--ssh-key [FILE]`, `--cloud-init FILE`, `--count N`, `--wait`.

## Examples

Deploy three servers for a test and remove them afterwards:

```bash
neckrez deploy worker --count 3 --plan quark --location FRA --ssh-key --wait --json
neckrez ls --json | jq -r '.[] | select(.name | startswith("worker-")) | .id' | xargs -n1 neckrez rm -y
```

Find the cheapest GPU you can order right now:

```bash
neckrez plans --type gpu --available
```

## About Neckrez

[Neckrez](https://neckrez.tech) is a crypto-paid cloud host. Sign-up needs only an email, payment is in Bitcoin, USDT, Monero and 300+ other coins, and servers are billed by the hour with a monthly cap. It is a reseller: the machines run on Vultr, DigitalOcean, Linode and Hetzner.

- Website: https://neckrez.tech
- API docs: https://neckrez.tech/docs
- Terms: https://neckrez.tech/legal/terms
- Support: support@neckrez.tech

## License

MIT, see [LICENSE](LICENSE).
