#!/usr/bin/env python3
"""
Tests for research-save-search.py.

Run directly (no dependencies required):
    ./test-research-save-search.py
    python3 test-research-save-search.py

Or under pytest:
    pytest test-research-save-search.py
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
_SCRIPT = Path(__file__).resolve().parent / "research-save-search.py"
_spec = importlib.util.spec_from_file_location("research_save_search", _SCRIPT)
sss = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sss)


GOOD_RESULTS = json.dumps(
    [
        {"title": "T1", "url": "https://a.com", "snippet": "S1"},
        {"title": "T2", "url": "https://b.com", "snippet": "S2"},
    ]
)

FIRECRAWL_OUTPUT = json.dumps(
    {
        "success": True,
        "data": {
            "web": [
                {
                    "url": "https://a.com",
                    "title": "T1",
                    "description": "D1",
                    "position": 1,
                },
                {
                    "url": "https://b.com",
                    "title": "T2",
                    "description": "D2",
                    "position": 2,
                },
            ]
        },
        "id": "abc",
        "creditsUsed": 2,
    }
)


class SaveSearchTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self._tmp.name) / "run"
        self.run_dir.mkdir()
        self.write_meta("running")

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
                code = sss.main(list(argv))
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else 2
        return code, err.getvalue()

    def write_results_file(self, content: str) -> Path:
        path = self.run_dir / "results.json"
        path.write_text(content, encoding="utf-8")
        return path

    def write_firecrawl_file(self, content: str) -> Path:
        path = self.run_dir / "firecrawl.json"
        path.write_text(content, encoding="utf-8")
        return path

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

    def test_valid_search_writes_entry(self) -> None:
        code, _ = self.run_cli(
            str(self.run_dir), "--query", "open source LLM", "--results", GOOD_RESULTS
        )
        self.assertEqual(code, 0)
        entries = self.read_entries()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["type"], "search")
        self.assertEqual(entry["query"], "open source LLM")
        self.assertEqual(len(entry["results"]), 2)
        self.assertEqual(entry["results"][0]["title"], "T1")
        self.assertIn("timestamp", entry)

    def test_empty_results_array_is_allowed(self) -> None:
        code, _ = self.run_cli(
            str(self.run_dir), "--query", "q", "--results", "[]"
        )
        self.assertEqual(code, 0)
        self.assertEqual(self.read_entries()[0]["results"], [])

    def test_appends_rather_than_overwrites(self) -> None:
        self.run_cli(str(self.run_dir), "--query", "q1", "--results", "[]")
        self.run_cli(str(self.run_dir), "--query", "q2", "--results", "[]")
        entries = self.read_entries()
        self.assertEqual([e["query"] for e in entries], ["q1", "q2"])

    def test_results_file_writes_entry(self) -> None:
        results_file = self.write_results_file(GOOD_RESULTS)
        code, _ = self.run_cli(
            str(self.run_dir),
            "--query",
            "open source LLM",
            "--results-file",
            str(results_file),
        )
        self.assertEqual(code, 0)
        entries = self.read_entries()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["query"], "open source LLM")
        self.assertEqual(len(entry["results"]), 2)
        self.assertEqual(entry["results"][0]["title"], "T1")

    def test_firecrawl_file_writes_entry(self) -> None:
        firecrawl_file = self.write_firecrawl_file(FIRECRAWL_OUTPUT)
        code, _ = self.run_cli(
            str(self.run_dir),
            "--query",
            "open source LLM",
            "--firecrawl-file",
            str(firecrawl_file),
        )
        self.assertEqual(code, 0)
        entries = self.read_entries()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["query"], "open source LLM")
        self.assertEqual(len(entry["results"]), 2)
        result = entry["results"][0]
        self.assertEqual(result["title"], "T1")
        self.assertEqual(result["url"], "https://a.com")
        # description is mapped to snippet; position is dropped.
        self.assertEqual(result["snippet"], "D1")
        self.assertNotIn("position", result)

    def test_firecrawl_empty_web_is_allowed(self) -> None:
        firecrawl_file = self.write_firecrawl_file(
            json.dumps({"data": {"web": []}})
        )
        code, _ = self.run_cli(
            str(self.run_dir),
            "--query",
            "q",
            "--firecrawl-file",
            str(firecrawl_file),
        )
        self.assertEqual(code, 0)
        self.assertEqual(self.read_entries()[0]["results"], [])

    # -- argument errors (exit 2) -----------------------------------------

    def test_both_results_options_fails(self) -> None:
        results_file = self.write_results_file(GOOD_RESULTS)
        code, err = self.run_cli(
            str(self.run_dir),
            "--query",
            "q",
            "--results",
            GOOD_RESULTS,
            "--results-file",
            str(results_file),
        )
        self.assertEqual(code, 2)
        self.assertEqual(self.read_entries(), [])

    def test_neither_results_option_fails(self) -> None:
        code, err = self.run_cli(str(self.run_dir), "--query", "q")
        self.assertEqual(code, 2)
        self.assertEqual(self.read_entries(), [])

    def test_missing_results_file_fails(self) -> None:
        missing = self.run_dir / "does-not-exist.json"
        code, err = self.run_cli(
            str(self.run_dir),
            "--query",
            "q",
            "--results-file",
            str(missing),
        )
        self.assertEqual(code, 2)
        self.assertIn("results file", err)
        self.assertEqual(self.read_entries(), [])

    def test_results_file_invalid_json_fails(self) -> None:
        results_file = self.write_results_file("not json")
        code, err = self.run_cli(
            str(self.run_dir),
            "--query",
            "q",
            "--results-file",
            str(results_file),
        )
        self.assertEqual(code, 2)
        self.assertIn("valid JSON", err)
        self.assertEqual(self.read_entries(), [])

    def test_firecrawl_with_results_fails(self) -> None:
        firecrawl_file = self.write_firecrawl_file(FIRECRAWL_OUTPUT)
        code, _ = self.run_cli(
            str(self.run_dir),
            "--query",
            "q",
            "--results",
            GOOD_RESULTS,
            "--firecrawl-file",
            str(firecrawl_file),
        )
        self.assertEqual(code, 2)
        self.assertEqual(self.read_entries(), [])

    def test_firecrawl_with_results_file_fails(self) -> None:
        results_file = self.write_results_file(GOOD_RESULTS)
        firecrawl_file = self.write_firecrawl_file(FIRECRAWL_OUTPUT)
        code, _ = self.run_cli(
            str(self.run_dir),
            "--query",
            "q",
            "--results-file",
            str(results_file),
            "--firecrawl-file",
            str(firecrawl_file),
        )
        self.assertEqual(code, 2)
        self.assertEqual(self.read_entries(), [])

    def test_missing_firecrawl_file_fails(self) -> None:
        missing = self.run_dir / "does-not-exist.json"
        code, err = self.run_cli(
            str(self.run_dir),
            "--query",
            "q",
            "--firecrawl-file",
            str(missing),
        )
        self.assertEqual(code, 2)
        self.assertIn("firecrawl file", err)
        self.assertEqual(self.read_entries(), [])

    def test_firecrawl_file_invalid_json_fails(self) -> None:
        firecrawl_file = self.write_firecrawl_file("not json")
        code, err = self.run_cli(
            str(self.run_dir),
            "--query",
            "q",
            "--firecrawl-file",
            str(firecrawl_file),
        )
        self.assertEqual(code, 2)
        self.assertIn("valid JSON", err)
        self.assertEqual(self.read_entries(), [])

    def test_firecrawl_missing_web_fails(self) -> None:
        firecrawl_file = self.write_firecrawl_file(json.dumps({"data": {}}))
        code, err = self.run_cli(
            str(self.run_dir),
            "--query",
            "q",
            "--firecrawl-file",
            str(firecrawl_file),
        )
        self.assertEqual(code, 2)
        self.assertIn("data.web", err)
        self.assertEqual(self.read_entries(), [])

    def test_firecrawl_empty_description_fails(self) -> None:
        firecrawl_file = self.write_firecrawl_file(
            json.dumps(
                {
                    "data": {
                        "web": [
                            {"url": "https://a.com", "title": "T1", "description": ""}
                        ]
                    }
                }
            )
        )
        code, err = self.run_cli(
            str(self.run_dir),
            "--query",
            "q",
            "--firecrawl-file",
            str(firecrawl_file),
        )
        self.assertEqual(code, 2)
        self.assertIn("snippet", err)
        self.assertEqual(self.read_entries(), [])

    # -- run-state / filesystem errors (exit 1) ---------------------------

    def test_run_not_running_fails(self) -> None:
        self.write_meta("complete")
        code, err = self.run_cli(
            str(self.run_dir), "--query", "q", "--results", GOOD_RESULTS
        )
        self.assertEqual(code, 1)
        self.assertIn("not running", err)
        self.assertEqual(self.read_entries(), [])

    def test_missing_meta_fails(self) -> None:
        (self.run_dir / "meta.json").unlink()
        code, err = self.run_cli(
            str(self.run_dir), "--query", "q", "--results", GOOD_RESULTS
        )
        self.assertEqual(code, 1)
        self.assertIn("meta.json", err)

    def test_malformed_meta_fails(self) -> None:
        (self.run_dir / "meta.json").write_text("{not json", encoding="utf-8")
        code, err = self.run_cli(
            str(self.run_dir), "--query", "q", "--results", GOOD_RESULTS
        )
        self.assertEqual(code, 1)
        self.assertIn("meta.json", err)

    def test_run_dir_not_a_directory_fails(self) -> None:
        missing = self.run_dir.parent / "does-not-exist"
        code, err = self.run_cli(
            str(missing), "--query", "q", "--results", GOOD_RESULTS
        )
        self.assertEqual(code, 1)
        self.assertIn("not a directory", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
