"""Offline tests for the neckrez CLI: no network, no API key, standard library only."""

import importlib.machinery
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "neckrez")


def load():
    loader = importlib.machinery.SourceFileLoader("neckrez_cli", SCRIPT)
    spec = importlib.util.spec_from_loader("neckrez_cli", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


cli = load()

SERVERS = [
    {"id": "a1b2c3d4e5", "name": "web-1", "status": "running", "ip": "203.0.113.5",
     "plan": {"id": "ion", "price_hour": 0.0247}, "location": {"code": "AMS"}, "provider": "vultr"},
    {"id": "a1ffee0000", "name": "web-2", "status": "stopped", "ip": None,
     "plan": {"id": "quark", "price_hour": 0.0137}, "location": {"code": "FRA"}, "provider": "linode"},
    {"id": "b9c8d7e6f5", "name": "db", "status": "running", "ip": "198.51.100.7",
     "plan": {"id": "photon"}, "location": {"code": "EWR"}, "provider": "digitalocean"},
]


class EntryPoint(unittest.TestCase):
    def run_cli(self, *args):
        env = dict(os.environ, NECKREZ_API_KEY="", NECKREZ_API_URL="http://127.0.0.1:9")
        return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True, env=env, timeout=30)

    def test_version(self):
        r = self.run_cli("--version")
        self.assertEqual(r.returncode, 0)
        self.assertIn(cli.VERSION, r.stdout + r.stderr)

    def test_help_lists_commands(self):
        r = self.run_cli("--help")
        self.assertEqual(r.returncode, 0)
        for cmd in ("login", "plans", "deploy", "ls", "ssh", "backups"):
            self.assertIn(cmd, r.stdout)

    def test_no_command_is_an_error(self):
        self.assertNotEqual(self.run_cli().returncode, 0)


class Parser(unittest.TestCase):
    def setUp(self):
        self.p = cli.build_parser()

    def test_deploy_defaults_and_options(self):
        a = self.p.parse_args(["deploy", "web-1", "--plan", "ion", "--location", "AMS"])
        self.assertEqual((a.name, a.plan, a.location, a.provider, a.os, a.count), ("web-1", "ion", "AMS", "vultr", "ubuntu", 1))
        a = self.p.parse_args(["deploy", "w", "--plan", "quark", "--location", "FRA", "--provider", "linode",
                               "--count", "3", "--ssh-key", "--wait"])
        self.assertEqual((a.provider, a.count, a.ssh_key, a.wait), ("linode", 3, "auto", True))

    def test_every_provider_is_accepted(self):
        for prov in ("vultr", "digitalocean", "linode", "hetzner"):
            self.assertEqual(self.p.parse_args(["plans", "--provider", prov]).provider, prov)

    def test_unknown_provider_is_rejected(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.p.parse_args(["plans", "--provider", "aws"])

    def test_deploy_requires_plan_and_location(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.p.parse_args(["deploy", "web-1"])

    def test_json_flag_everywhere(self):
        self.assertTrue(self.p.parse_args(["ls", "--json"]).json)
        self.assertTrue(self.p.parse_args(["balance", "--json"]).json)


class Helpers(unittest.TestCase):
    def test_money(self):
        self.assertEqual(cli.money(10), "$10.00")
        self.assertEqual(cli.money("3.456"), "$3.46")
        self.assertEqual(cli.money(None), "None")

    def test_server_row(self):
        row = cli.server_row(SERVERS[0])
        self.assertEqual(row[:2], ["a1b2c3d4", "web-1"])
        self.assertEqual(row[-1], "$0.0247/h")
        self.assertEqual(cli.server_row(SERVERS[1])[3], "-")
        self.assertEqual(len(row), len(cli.SERVER_HEADER))

    def test_gen_password(self):
        pw = cli.gen_password()
        self.assertEqual(len(pw), 24)
        self.assertTrue(pw.isalnum())
        self.assertNotEqual(pw, cli.gen_password())

    def test_explain_adds_hints(self):
        self.assertIn("neckrez login", cli.explain(401, {"detail": "bad key"}))
        self.assertIn("top up", cli.explain(402, {"detail": "no money"}))
        self.assertEqual(cli.explain(500, {"detail": "boom"}), "500: boom")
        self.assertIn("field required", cli.explain(422, {"detail": [{"msg": "field required"}]}))

    def test_read_ssh_key_from_file_and_literal(self):
        with tempfile.NamedTemporaryFile("w", suffix=".pub", delete=False) as f:
            f.write("ssh-ed25519 AAAATEST user@host\n")
        try:
            self.assertEqual(cli.read_ssh_key(f.name), "ssh-ed25519 AAAATEST user@host")
        finally:
            os.unlink(f.name)
        self.assertEqual(cli.read_ssh_key("ssh-ed25519 AAAALITERAL x"), "ssh-ed25519 AAAALITERAL x")


class FindServer(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(cli, "get", return_value={"servers": SERVERS})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_exact_name_and_id(self):
        self.assertEqual(cli.find_server("db")["id"], "b9c8d7e6f5")
        self.assertEqual(cli.find_server("a1ffee0000")["name"], "web-2")

    def test_unique_prefix(self):
        self.assertEqual(cli.find_server("b9")["name"], "db")

    def test_ambiguous_prefix(self):
        with self.assertRaises(cli.CliError) as e:
            cli.find_server("a1")
        self.assertIn("matches 2 servers", str(e.exception))

    def test_no_match(self):
        with self.assertRaises(cli.CliError):
            cli.find_server("zzz")


class Config(unittest.TestCase):
    def test_env_overrides_and_missing_key(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(cli, "CONFIG", os.path.join(d, "config.json")):
            with mock.patch.dict(os.environ, {"NECKREZ_API_URL": "https://example.test/", "NECKREZ_API_KEY": ""}):
                self.assertEqual(cli.base_url(), "https://example.test")
                with self.assertRaises(cli.CliError) as e:
                    cli.api_key()
                self.assertEqual(e.exception.code, 2)

    def test_saved_config_is_private(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(cli, "CONFIG", os.path.join(d, "sub", "config.json")):
            cli.save_config({"key": "nek_test", "url": "https://neckrez.tech"})
            self.assertEqual(cli.load_config()["key"], "nek_test")
            if os.name == "posix":
                self.assertEqual(os.stat(cli.CONFIG).st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
