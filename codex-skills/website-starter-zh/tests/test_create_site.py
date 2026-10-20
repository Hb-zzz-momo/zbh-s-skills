import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("creator", Path(__file__).resolve().parents[1] / "scripts" / "create_site.py")
creator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(creator)


class CreateSiteTests(unittest.TestCase):
    def test_portable_copy_and_title_escaping(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "new site 中文"
            creator.create_site(out, '<img src=x onerror="alert(1)">')
            text = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("&lt;img", text)
            self.assertNotIn('<img src=x', text)
            self.assertNotIn("__SITE_TITLE__", text)
            self.assertEqual({p.name for p in out.iterdir()}, {"index.html", "styles.css", "app.js"})
            for i, value in enumerate(("中" * 80, "👩‍💻")):
                valid = Path(tmp) / str(i)
                creator.create_site(valid, value)
                self.assertIn(value, (valid / "index.html").read_text(encoding="utf-8"))

    def test_existing_data_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "existing"
            out.mkdir()
            marker = out / "keep.txt"
            marker.write_bytes(b"unchanged")
            with self.assertRaises(FileExistsError):
                creator.create_site(out, "hello")
            self.assertEqual(marker.read_bytes(), b"unchanged")
            self.assertEqual(list(out.iterdir()), [marker])

    def test_invalid_title_creates_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            for value in (" ", "a" * 81, "bad\nname", "\nname", "name\n", "\tname", "a\x7fb", "a\x85b", "a\u2028b", "a\u2029b", "\u200b", "a\u202eb"):
                with self.assertRaises(ValueError):
                    creator.create_site(out, value)
                self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
