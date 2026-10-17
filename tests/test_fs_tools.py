import tempfile
import unittest
from pathlib import Path
from fs_tools import read_file, list_files, write_file, search_in_file


class FileToolsTests(unittest.TestCase):
    def test_write_read_and_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "resume.txt"
            written = write_file(str(path), "Python developer with KOTLIN experience.")
            self.assertTrue(written["success"])
            read = read_file(str(path))
            self.assertTrue(read["success"])
            self.assertIn("Python", read["content"])
            result = search_in_file(str(path), "python")
            self.assertTrue(result["success"])
            self.assertEqual(result["match_count"], 1)
            self.assertIn("Python", result["matches"][0]["context"])

    def test_list_extension_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.txt").write_text("A", encoding="utf-8")
            Path(tmp, "b.pdf").write_bytes(b"not a real pdf")
            self.assertEqual(len(list_files(tmp, ".txt")), 1)

    def test_missing_file_error(self):
        result = read_file("/definitely/not/a/real/file.txt")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "file_not_found")

    def test_empty_keyword(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "a.txt")
            path.write_text("hello", encoding="utf-8")
            result = search_in_file(str(path), " ")
            self.assertFalse(result["success"])


if __name__ == "__main__":
    unittest.main()
