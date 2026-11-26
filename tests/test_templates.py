import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stub import templates
from stub.models import StubError


class TemplateTests(unittest.TestCase):
    def test_load_bundled_templates(self):
        spec = templates.load_template("cpp")
        self.assertEqual(spec.extension, "cpp")
        self.assertIn("int main()", spec.body)
        note = templates.load_markdown_template()
        self.assertEqual(note.extension, "md")
        self.assertIn("${MESSAGE_MD}", note.body)

    def test_list_templates(self):
        names = templates.list_templates()
        self.assertIn("cpp", names)
        self.assertIn("markdown", names)

    def test_unknown_template_raises_stub_error(self):
        with self.assertRaises(StubError):
            templates.load_template("not-a-language")

    def test_scaffold_template_and_reject_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"STUB_TEMPLATES_DIR": directory}):
                path = templates.scaffold_template("rust", extension="rs")
                self.assertTrue(path.is_file())
                self.assertEqual(templates.load_template("rust").extension, "rs")
                self.assertIn("${FILENAME}", path.read_text())
                with self.assertRaises(StubError):
                    templates.scaffold_template("rust")


if __name__ == "__main__":
    unittest.main()
