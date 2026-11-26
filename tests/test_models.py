import unittest
from datetime import datetime

from stub.models import RenderContext, StubError, TemplateSpec, format_stem, safe_stem


class RenderContextTests(unittest.TestCase):
    def test_mapping_formats_message_and_metadata(self):
        context = RenderContext.create(
            language="cpp",
            name="demo",
            filename="demo.cpp",
            message="Extra message",
            now=datetime(2026, 11, 26, 14, 32, 7),
        )
        values = context.mapping()
        self.assertEqual(context.date, "2026-11-26")
        self.assertEqual(values["DATE"], "2026-11-26")
        self.assertEqual(values["TIME"], "14:32:07")
        self.assertEqual(values["TITLE"], "2026-11-26 cpp")
        self.assertEqual(values["MESSAGE_MD"], "_Extra message_")
        self.assertEqual(values["MESSAGE_COMMENT"], "// Extra message")

    def test_mapping_without_message_is_empty(self):
        context = RenderContext.create(
            language="cpp", name="demo", filename="demo.cpp", now=datetime(2026, 11, 26)
        )
        self.assertEqual(context.mapping()["MESSAGE_MD"], "")
        self.assertEqual(context.mapping()["MESSAGE_COMMENT"], "")


class HelperTests(unittest.TestCase):
    def test_safe_stem(self):
        self.assertEqual(safe_stem("  my note.md "), "my_note.md")
        self.assertEqual(safe_stem("../demo"), "demo")
        with self.assertRaises(StubError):
            safe_stem("   ")

    def test_format_stem(self):
        self.assertEqual(
            format_stem(
                "{date}_{language}", date="2026-11-26", language="cpp", name="demo"
            ),
            "2026-11-26_cpp",
        )
        with self.assertRaises(StubError):
            format_stem("{unknown}", date="2026-11-26", language="cpp", name="demo")


class TemplateSpecTests(unittest.TestCase):
    def test_from_mapping_normalises_extension(self):
        spec = TemplateSpec.from_mapping(
            {"name": "cpp", "extension": ".cpp", "body": "int main() {}"}
        )
        self.assertEqual(spec.extension, "cpp")
        self.assertEqual(spec.filename, "{date}_{language}")

    def test_from_mapping_rejects_missing_key(self):
        with self.assertRaises(StubError):
            TemplateSpec.from_mapping({"name": "cpp", "extension": "cpp"})


if __name__ == "__main__":
    unittest.main()
