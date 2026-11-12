"""Launcher contracts without loading/training any model."""
import ast
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

class LauncherTests(unittest.TestCase):
    def linux(self, backend=None):
        with tempfile.TemporaryDirectory() as folder:
            fake = Path(folder) / "python"
            fake.write_text('#!/bin/sh\nprintf "%s|%s|%s\\n" "$TEMPO_BACKEND" "$OMP_NUM_THREADS" "$*"\n')
            fake.chmod(0o755)
            env = dict(os.environ, TEMPO_PYTHON=str(fake), OMP_NUM_THREADS="2")
            env.pop("TEMPO_BACKEND", None)
            if backend is not None:
                env["TEMPO_BACKEND"] = backend
            return subprocess.check_output(["bash", str(ROOT / "jalankan_linux.sh")], env=env, text=True).splitlines()

    def test_linux_default_and_preflight(self):
        calls = self.linux()
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(line.startswith("e42-tail-grid|2|") for line in calls))
        self.assertIn("check_delivery.py", calls[0])
        self.assertIn("app.py", calls[1])

    def test_linux_explicit_override(self):
        calls = self.linux("micro-e14-qlora")
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0].startswith("micro-e14-qlora|2|"))

    def test_linux_preflight_failure_stops_server(self):
        with tempfile.TemporaryDirectory() as folder:
            fake = Path(folder) / "python"
            fake.write_text("#!/bin/sh\nexit 9\n")
            fake.chmod(0o755)
            env = dict(os.environ, TEMPO_PYTHON=str(fake), TEMPO_BACKEND="e42-tail-grid")
            result = subprocess.run(["bash", str(ROOT / "jalankan_linux.sh")], env=env)
            self.assertEqual(result.returncode, 9)

    def test_gunicorn_default_and_override(self):
        previous = Path.cwd()
        try:
            for backend in (None, "clip-indobert-tail-rich256", "invalid-backend"):
                env = {"OMP_NUM_THREADS": "2"}
                if backend is not None:
                    env["TEMPO_BACKEND"] = backend
                with patch.dict(os.environ, env, clear=True), patch("os.execv") as execute:
                    runpy.run_path(str(ROOT / "02_web_demo/serve_tail.py"))
                    self.assertEqual(os.environ["TEMPO_BACKEND"], backend or "e42-tail-grid")
                    self.assertEqual(os.environ["OMP_NUM_THREADS"], "2")
                    self.assertEqual(os.environ["HF_HUB_OFFLINE"], "1")
                    self.assertIn("gunicorn", execute.call_args.args[1])
                    self.assertEqual(execute.call_args.args[1][-1], "app:app")
        finally:
            os.chdir(previous)

    def test_windows_default_override_contract(self):
        source = (ROOT / "jalankan_windows.bat").read_text()
        self.assertIn('if not defined TEMPO_BACKEND set "TEMPO_BACKEND=e42-tail-grid"', source)
        self.assertIn('if /I not "%TEMPO_BACKEND%"=="e42-tail-grid" goto start_app', source)

    def test_direct_app_default_and_single_worker(self):
        tree = ast.parse((ROOT / "02_web_demo/app.py").read_text())
        assignment = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "BACKEND_NAME" for t in n.targets))
        self.assertEqual(assignment.value.args[1].value, "e42-tail-grid")
        cfg = runpy.run_path(str(ROOT / "02_web_demo/gunicorn_conf.py"))
        self.assertEqual(cfg["workers"], 1)
        self.assertEqual(cfg["threads"], 4)

if __name__ == "__main__":
    unittest.main()
