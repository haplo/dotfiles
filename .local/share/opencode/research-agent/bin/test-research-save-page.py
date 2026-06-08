#!/usr/bin/env python3
"""
Tests for research-save-page.py.

Run directly (no dependencies required):
    ./test-research-save-page.py
    python3 test-research-save-page.py

Or under pytest:
    pytest test-research-save-page.py
"""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

# Load the script-under-test by path, since its hyphenated filename is not a
# valid Python module name for a normal import.
_SCRIPT = Path(__file__).resolve().parent / "research-save-page.py"
_spec = importlib.util.spec_from_file_location("research_save_page", _SCRIPT)
ssp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ssp)


class SavePageTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self._tmp.name) / "run"
        self.pages_dir = self.run_dir / "pages"
        self.pages_dir.mkdir(parents=True)
        self.write_meta("running")
        # A non-empty page file ready to be referenced.
        (self.pages_dir / "page1.html").write_text("hello", encoding="utf-8")
        (self.pages_dir / "empty.html").write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # -- helpers -----------------------------------------------------------

    def write_meta(self, status: str) -> None:
        meta = {"run_id": "x", "status": status}
        (self.run_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

    def run_cli(self, *argv: str) -> tuple[int, str]:
        """Invoke main() with argv; return (exit_code, stderr_text).

        argparse-level errors raise SystemExit instead of returning a code;
        normalize those into the same (code, stderr) contract.
        """
        err = io.StringIO()
        with redirect_stderr(err):
            try:
                code = ssp.main(list(argv))
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else 2
        return code, err.getvalue()

    def read_entries(self) -> list[dict]:
        path = self.run_dir / "searches.jsonl"
        if not path.exists():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    # -- success cases -----------------------------------------------------

    def test_ok_writes_success_entry(self) -> None:
        code, _ = self.run_cli(
            str(self.run_dir),
            "--url",
            "https://example.com/a?b=c",
            "--file",
            "page1.html",
            "--ok",
        )
        self.assertEqual(code, 0)
        entries = self.read_entries()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["type"], "fetch")
        self.assertEqual(entry["status"], "ok")
        self.assertEqual(entry["url"], "https://example.com/a?b=c")
        self.assertEqual(entry["file"], "page1.html")
        self.assertEqual(entry["byte_count"], 5)
        self.assertIn("timestamp", entry)

    def test_error_writes_error_entry(self) -> None:
        code, _ = self.run_cli(
            str(self.run_dir),
            "--url",
            "https://example.com/x",
            "--error",
            "404 Not Found",
        )
        self.assertEqual(code, 0)
        entry = self.read_entries()[0]
        self.assertEqual(entry["type"], "fetch")
        self.assertEqual(entry["status"], "error")
        self.assertEqual(entry["error"], "404 Not Found")
        self.assertNotIn("file", entry)

    def test_appends_rather_than_overwrites(self) -> None:
        self.run_cli(
            str(self.run_dir), "--url", "https://a.com", "--file", "page1.html", "--ok"
        )
        self.run_cli(str(self.run_dir), "--url", "https://b.com", "--error", "boom")
        entries = self.read_entries()
        self.assertEqual([e["status"] for e in entries], ["ok", "error"])

    # -- argument errors (exit 2) -----------------------------------------

    def test_ok_without_file_fails(self) -> None:
        code, err = self.run_cli(
            str(self.run_dir), "--url", "https://example.com", "--ok"
        )
        self.assertEqual(code, 2)
        self.assertIn("--file", err)
        self.assertEqual(self.read_entries(), [])

    def test_error_with_file_fails(self) -> None:
        code, err = self.run_cli(
            str(self.run_dir),
            "--url",
            "https://example.com",
            "--file",
            "page1.html",
            "--error",
            "boom",
        )
        self.assertEqual(code, 2)
        self.assertIn("--file", err)
        self.assertEqual(self.read_entries(), [])

    def test_empty_error_message_fails(self) -> None:
        code, err = self.run_cli(
            str(self.run_dir), "--url", "https://example.com", "--error", "   "
        )
        self.assertEqual(code, 2)
        self.assertIn("--error", err)

    def test_both_ok_and_error_fails(self) -> None:
        code, _ = self.run_cli(
            str(self.run_dir),
            "--url",
            "https://example.com",
            "--ok",
            "--error",
            "boom",
        )
        self.assertEqual(code, 2)

    def test_neither_ok_nor_error_fails(self) -> None:
        code, _ = self.run_cli(
            str(self.run_dir), "--url", "https://example.com"
        )
        self.assertEqual(code, 2)

    # -- validation / filesystem errors (exit 1) --------------------------

    def test_invalid_url_fails(self) -> None:
        code, err = self.run_cli(
            str(self.run_dir), "--url", "ht!tp://no", "--file", "page1.html", "--ok"
        )
        self.assertEqual(code, 1)
        self.assertIn("invalid URL", err)
        self.assertEqual(self.read_entries(), [])

    def test_missing_page_file_fails(self) -> None:
        code, err = self.run_cli(
            str(self.run_dir), "--url", "https://example.com", "--file", "nope.html", "--ok"
        )
        self.assertEqual(code, 1)
        self.assertIn("not found", err)

    def test_empty_page_file_fails(self) -> None:
        code, err = self.run_cli(
            str(self.run_dir), "--url", "https://example.com", "--file", "empty.html", "--ok"
        )
        self.assertEqual(code, 1)
        self.assertIn("empty", err)

    def test_run_not_running_fails(self) -> None:
        self.write_meta("complete")
        code, err = self.run_cli(
            str(self.run_dir), "--url", "https://example.com", "--file", "page1.html", "--ok"
        )
        self.assertEqual(code, 1)
        self.assertIn("not running", err)
        self.assertEqual(self.read_entries(), [])

    def test_missing_meta_fails(self) -> None:
        (self.run_dir / "meta.json").unlink()
        code, err = self.run_cli(
            str(self.run_dir), "--url", "https://example.com", "--error", "boom"
        )
        self.assertEqual(code, 1)
        self.assertIn("meta.json", err)

    def test_malformed_meta_fails(self) -> None:
        (self.run_dir / "meta.json").write_text("{not json", encoding="utf-8")
        code, err = self.run_cli(
            str(self.run_dir), "--url", "https://example.com", "--error", "boom"
        )
        self.assertEqual(code, 1)
        self.assertIn("meta.json", err)

    def test_run_dir_not_a_directory_fails(self) -> None:
        missing = self.run_dir.parent / "does-not-exist"
        code, err = self.run_cli(
            str(missing), "--url", "https://example.com", "--error", "boom"
        )
        self.assertEqual(code, 1)
        self.assertIn("not a directory", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
