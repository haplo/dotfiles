#!/usr/bin/env python3
"""
Tests for research-run-validate.py.

Run directly (no dependencies required):
    ./test-research-run-validate.py
    python3 test-research-run-validate.py

Or under pytest:
    pytest test-research-run-validate.py
"""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

# Load the script-under-test by path, since its hyphenated filename is not a
# valid Python module name for a normal import.
_SCRIPT = Path(__file__).resolve().parent / "research-run-validate.py"
_spec = importlib.util.spec_from_file_location("research_run_validate", _SCRIPT)
rrv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rrv)


GOOD_SEARCHES = "\n".join(
    [
        json.dumps(
            {
                "type": "search",
                "query": "q",
                "results": [
                    {"title": "T1", "url": "https://a.com", "snippet": "S1"},
                    {"title": "T2", "url": "https://b.com", "snippet": "S2"},
                ],
            }
        ),
        json.dumps(
            {"type": "fetch", "status": "ok", "url": "https://a.com", "file": "p.html"}
        ),
        json.dumps(
            {"type": "fetch", "status": "error", "url": "https://b.com", "error": "404"}
        ),
    ]
)


class RunValidateTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self._tmp.name) / "run"
        self.run_dir.mkdir()
        self.write_meta("running")
        # Mandatory + recommended content for a well-formed run.
        (self.run_dir / "notes.md").write_text("# notes\n", encoding="utf-8")
        (self.run_dir / "searches.jsonl").write_text(
            GOOD_SEARCHES + "\n", encoding="utf-8"
        )
        (self.run_dir / "pages").mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # -- helpers -----------------------------------------------------------

    def write_meta(self, status: str) -> None:
        meta = {"run_id": "x", "status": status}
        (self.run_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        """Invoke main() with argv; return (exit_code, stdout_text, stderr_text).

        argparse-level errors raise SystemExit instead of returning a code;
        normalize those into the same contract.
        """
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = rrv.main(list(argv))
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else 2
        return code, out.getvalue(), err.getvalue()

    def read_meta(self) -> dict:
        return json.loads((self.run_dir / "meta.json").read_text(encoding="utf-8"))

    # -- success path ------------------------------------------------------

    def test_valid_run_finalizes_complete_with_counts(self) -> None:
        code, out, _ = self.run_cli(str(self.run_dir))
        self.assertEqual(code, 0)
        summary = json.loads(out)
        self.assertEqual(summary["status"], "complete")
        self.assertEqual(summary["query_count"], 1)
        self.assertEqual(summary["result_count"], 2)
        self.assertEqual(summary["fetch_count"], 2)
        self.assertEqual(summary["fetch_error_count"], 1)
        meta = self.read_meta()
        self.assertEqual(meta["status"], "complete")
        self.assertIsNotNone(meta["finalized_at"])
        self.assertIsNone(meta["error"])

    def test_no_pages_warning_when_well_formed(self) -> None:
        code, _, err = self.run_cli(str(self.run_dir))
        self.assertEqual(code, 0)
        self.assertNotIn("pages", err)

    # -- pages/ warnings (non-fatal) --------------------------------------

    def test_missing_pages_dir_warns_but_completes(self) -> None:
        (self.run_dir / "pages").rmdir()
        code, _, err = self.run_cli(str(self.run_dir))
        self.assertEqual(code, 0)
        self.assertIn("missing recommended directory: pages", err)
        self.assertEqual(self.read_meta()["status"], "complete")

    def test_empty_file_in_pages_warns_for_each(self) -> None:
        (self.run_dir / "pages" / "a.html").write_text("", encoding="utf-8")
        (self.run_dir / "pages" / "b.html").write_text("", encoding="utf-8")
        (self.run_dir / "pages" / "c.html").write_text("ok", encoding="utf-8")
        code, _, err = self.run_cli(str(self.run_dir))
        self.assertEqual(code, 0)
        self.assertIn("empty file in pages/: a.html", err)
        self.assertIn("empty file in pages/: b.html", err)
        self.assertNotIn("c.html", err)
        self.assertEqual(self.read_meta()["status"], "complete")

    def test_empty_pages_dir_does_not_warn(self) -> None:
        # pages/ exists but contains no files at all -> no per-file warning.
        code, _, err = self.run_cli(str(self.run_dir))
        self.assertEqual(code, 0)
        self.assertNotIn("empty file in pages/", err)

    # -- --mark-failed -----------------------------------------------------

    def test_mark_failed_sets_failed_status(self) -> None:
        code, _, err = self.run_cli(
            str(self.run_dir), "--mark-failed", "--error", "boom"
        )
        self.assertEqual(code, 0)
        meta = self.read_meta()
        self.assertEqual(meta["status"], "failed")
        self.assertEqual(meta["error"], "boom")
        self.assertIn("failed", err)

    # -- validation failures (exit 1) -------------------------------------

    def test_missing_notes_fails_and_marks_failed(self) -> None:
        (self.run_dir / "notes.md").unlink()
        code, _, err = self.run_cli(str(self.run_dir))
        self.assertEqual(code, 1)
        self.assertIn("notes.md", err)
        self.assertEqual(self.read_meta()["status"], "failed")

    def test_empty_notes_fails(self) -> None:
        (self.run_dir / "notes.md").write_text("", encoding="utf-8")
        code, _, err = self.run_cli(str(self.run_dir))
        self.assertEqual(code, 1)
        self.assertIn("empty", err)

    def test_malformed_searches_line_fails(self) -> None:
        (self.run_dir / "searches.jsonl").write_text("{not json\n", encoding="utf-8")
        code, _, err = self.run_cli(str(self.run_dir))
        self.assertEqual(code, 1)
        self.assertIn("invalid JSON", err)

    def test_already_complete_fails(self) -> None:
        self.write_meta("complete")
        code, _, err = self.run_cli(str(self.run_dir))
        self.assertEqual(code, 1)
        self.assertIn("already validated", err)

    # -- argument / filesystem errors (exit 2 / 1) ------------------------

    def test_not_a_directory_fails(self) -> None:
        missing = self.run_dir.parent / "does-not-exist"
        code, _, err = self.run_cli(str(missing))
        self.assertEqual(code, 2)
        self.assertIn("not a directory", err)

    def test_missing_meta_fails(self) -> None:
        (self.run_dir / "meta.json").unlink()
        code, _, err = self.run_cli(str(self.run_dir))
        self.assertEqual(code, 1)
        self.assertIn("meta.json", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
