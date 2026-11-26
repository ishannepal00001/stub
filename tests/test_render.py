import unittest
from datetime import datetime

from stub.models import RenderContext, TemplateSpec
from stub.render import render


def context(message=None):
    return RenderContext.create(
        language="cpp",
        name="demo",
        filename="demo.cpp",
        message=message,
        now=datetime(2026, 11, 26, 14, 32, 7),
    )


class RenderTests(unittest.TestCase):
    def test_message_line_is_formatted(self):
        spec = TemplateSpec(
            name="cpp",
            extension="cpp",
            body="${MESSAGE_COMMENT}\nint main() {\n}\n",
        )
        self.assertEqual(render(spec, context("Extra message")), "// Extra message\nint main() {\n}\n")

    def test_message_line_is_dropped_when_empty(self):
        spec = TemplateSpec(
            name="cpp",
            extension="cpp",
            body="${MESSAGE_COMMENT}\nint main() {\n}\n",
        )
        self.assertEqual(render(spec, context()), "int main() {\n}\n")

    def test_cpp_braces_are_untouched(self):
        spec = TemplateSpec(
            name="cpp", extension="cpp", body="// ${DATE}\nint main() {\n    return 0;\n}\n"
        )
        self.assertIn("int main() {\n    return 0;\n}", render(spec, context()))


if __name__ == "__main__":
    unittest.main()
