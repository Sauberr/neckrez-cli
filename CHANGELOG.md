# Changelog

## 0.1.2 — 2026-11-21
- `--provider` accepts `linode` in `plans`, `locations`, `os` and `deploy` (Linode is live on Neckrez).
- Offline unit tests and a GitHub Actions workflow (Python 3.8–3.13, Linux, macOS, Windows).

## 0.1.1 — 2026-10-27
- `--wait` also waits until SSH (RDP on Windows) answers; `--no-port-wait` skips that.
- `balance` shows the transaction kind and description the API returns.

## 0.1.0 — 2026-10-27
- First release: `login`, `balance`, `plans`, `locations`, `os`, `deploy` (with `--count`, `--ssh-key`, `--cloud-init`, `--wait`), `ls`, `show`, `start`/`stop`/`reboot`/`swap-ip`, `rm`, `ssh`, `backups`.
- One file, Python 3.8+, standard library only. `--json` on every command.
