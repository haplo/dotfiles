#!/usr/bin/env python3
"""
Tests for research-run-init.py.

Run directly (no dependencies required):
    ./test-research-run-init.py
    python3 test-research-run-init.py

Or under pytest:
    pytest test-research-run-init.py
"""

import importlib.util
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

# Load the script-under-test by path, since its hyphenated filename is not a
# valid Python module name for a normal import.
_SCRIPT = Path(__file__).resolve().parent / "research-run-init.py"
_spec = importlib.util.spec_from_file_location("research_run_init", _SCRIPT)
rri = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rri)


RUN_ID_RE = re.compile(r"^\d{8}-\d{6}-[a-z0-9-]+$")


class RunInitTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base_dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # -- helpers -----------------------------------------------------------

    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        """Invoke main() with argv; return (exit_code, stdout_text, stderr_text).

        argparse-level errors raise SystemExit instead of returning a code;
        normalize those into the same contract.
        """
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = rri.main(list(argv))
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else 2
        return code, out.getvalue(), err.getvalue()

    def read_meta(self, run_dir: Path) -> dict:
        return json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))

    # -- success cases -----------------------------------------------------

    def test_creates_run_dir_and_prints_path(self) -> None:
        code, out, _ = self.run_cli(
            "--dir", str(self.base_dir),
            "--slug", "my-topic",
            "--user-prompt", "find things",
            "--researcher-prompt", "find things thoroughly",
        )
        self.assertEqual(code, 0)
        printed = out.strip()
        run_dir = Path(printed)
        self.assertTrue(run_dir.is_dir())
        self.assertEqual(run_dir.parent, self.base_dir / "runs")
        self.assertTrue(RUN_ID_RE.match(run_dir.name))
        self.assertTrue(run_dir.name.endswith("-my-topic"))

    def test_runs_subdir_created_when_absent(self) -> None:
        code, out, _ = self.run_cli(
            "--dir", str(self.base_dir),
            "--slug", "topic",
            "--user-prompt", "p",
            "--researcher-prompt", "p",
        )
        self.assertEqual(code, 0)
        run_dir = Path(out.strip())
        self.assertEqual(run_dir.parent.name, "runs")
        self.assertTrue((self.base_dir / "runs").is_dir())

    def test_runs_not_double_nested_when_dir_ends_in_runs(self) -> None:
        runs_dir = self.base_dir / "runs"
        runs_dir.mkdir()
        code, out, _ = self.run_cli(
            "--dir", str(runs_dir),
            "--slug", "topic",
            "--user-prompt", "p",
            "--researcher-prompt", "p",
        )
        self.assertEqual(code, 0)
        run_dir = Path(out.strip())
        self.assertEqual(run_dir.parent, runs_dir)
        self.assertFalse((runs_dir / "runs").exists())

    def test_creates_pages_subdir(self) -> None:
        code, out, _ = self.run_cli(
            "--dir", str(self.base_dir),
            "--slug", "topic",
            "--user-prompt", "p",
            "--researcher-prompt", "p",
        )
        self.assertEqual(code, 0)
        run_dir = Path(out.strip())
        self.assertTrue((run_dir / "pages").is_dir())

    def test_writes_initial_meta(self) -> None:
        code, out, _ = self.run_cli(
            "--dir", str(self.base_dir),
            "--slug", "topic",
            "--user-prompt", "the user prompt",
            "--researcher-prompt", "the researcher prompt",
        )
        self.assertEqual(code, 0)
        run_dir = Path(out.strip())
        meta = self.read_meta(run_dir)
        self.assertEqual(meta["run_id"], run_dir.name)
        self.assertEqual(meta["user_prompt"], "the user prompt")
        self.assertEqual(meta["researcher_prompt"], "the researcher prompt")
        self.assertEqual(meta["status"], "running")
        self.assertIsNone(meta["finalized_at"])
        self.assertIsNone(meta["error"])
        self.assertIn("created_at", meta)
        self.assertNotIn("research_prompt", meta)

    def test_slug_is_sanitized(self) -> None:
        code, out, _ = self.run_cli(
            "--dir", str(self.base_dir),
            "--slug", "My Topic!! Foo",
            "--user-prompt", "p",
            "--researcher-prompt", "p",
        )
        self.assertEqual(code, 0)
        run_dir = Path(out.strip())
        self.assertTrue(run_dir.name.endswith("-my-topic-foo"))

    def test_collision_creates_distinct_dirs(self) -> None:
        # Force a collision by pinning the timestamp so both runs share a base.
        fixed = "20260101-120000"
        orig = rri.utc_now_compact
        rri.utc_now_compact = lambda: fixed
        try:
            _, out1, _ = self.run_cli(
                "--dir", str(self.base_dir), "--slug", "dup",
                "--user-prompt", "p", "--researcher-prompt", "p",
            )
            _, out2, _ = self.run_cli(
                "--dir", str(self.base_dir), "--slug", "dup",
                "--user-prompt", "p", "--researcher-prompt", "p",
            )
        finally:
            rri.utc_now_compact = orig
        run1, run2 = Path(out1.strip()), Path(out2.strip())
        self.assertNotEqual(run1.name, run2.name)
        self.assertTrue(run1.is_dir())
        self.assertTrue(run2.is_dir())
        # First gets the bare id; second gets a random suffix appended.
        self.assertEqual(run1.name, f"{fixed}-dup")
        self.assertTrue(run2.name.startswith(f"{fixed}-dup-"))

    # -- argument / validation errors (exit 2) -----------------------------

    def test_missing_dir_arg_fails(self) -> None:
        code, _, err = self.run_cli(
            "--slug", "topic", "--user-prompt", "p", "--researcher-prompt", "p"
        )
        self.assertEqual(code, 2)
        self.assertIn("--dir", err)

    def test_dir_does_not_exist_fails(self) -> None:
        missing = self.base_dir / "nope"
        code, _, err = self.run_cli(
            "--dir", str(missing), "--slug", "topic",
            "--user-prompt", "p", "--researcher-prompt", "p",
        )
        self.assertEqual(code, 2)
        self.assertIn("does not exist", err)

    def test_dir_not_a_directory_fails(self) -> None:
        a_file = self.base_dir / "afile"
        a_file.write_text("x", encoding="utf-8")
        code, _, err = self.run_cli(
            "--dir", str(a_file), "--slug", "topic",
            "--user-prompt", "p", "--researcher-prompt", "p",
        )
        self.assertEqual(code, 2)
        self.assertIn("not a directory", err)

    def test_slug_empty_after_sanitization_fails(self) -> None:
        code, _, err = self.run_cli(
            "--dir", str(self.base_dir), "--slug", "!!!",
            "--user-prompt", "p", "--researcher-prompt", "p",
        )
        self.assertEqual(code, 2)
        self.assertIn("slug", err)

    def test_empty_user_prompt_fails(self) -> None:
        code, _, err = self.run_cli(
            "--dir", str(self.base_dir), "--slug", "topic",
            "--user-prompt", "   ", "--researcher-prompt", "p",
        )
        self.assertEqual(code, 2)
        self.assertIn("--user-prompt", err)

    def test_empty_researcher_prompt_fails(self) -> None:
        code, _, err = self.run_cli(
            "--dir", str(self.base_dir), "--slug", "topic",
            "--user-prompt", "p", "--researcher-prompt", "   ",
        )
        self.assertEqual(code, 2)
        self.assertIn("--researcher-prompt", err)

    def test_missing_slug_arg_fails(self) -> None:
        code, _, err = self.run_cli(
            "--dir", str(self.base_dir),
            "--user-prompt", "p", "--researcher-prompt", "p",
        )
        self.assertEqual(code, 2)
        self.assertIn("--slug", err)

    def test_missing_user_prompt_arg_fails(self) -> None:
        code, _, err = self.run_cli(
            "--dir", str(self.base_dir), "--slug", "topic",
            "--researcher-prompt", "p",
        )
        self.assertEqual(code, 2)
        self.assertIn("--user-prompt", err)

    def test_missing_researcher_prompt_arg_fails(self) -> None:
        code, _, err = self.run_cli(
            "--dir", str(self.base_dir), "--slug", "topic",
            "--user-prompt", "p",
        )
        self.assertEqual(code, 2)
        self.assertIn("--researcher-prompt", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
