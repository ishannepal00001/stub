import tempfile
import unittest
from pathlib import Path

from stub.models import Paths, StubError
from stub.writer import link_note, write_file, write_generation


class WriterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_write_file_does_not_overwrite(self):
        path = write_file(self.root / "a.txt", "hello\n")
        self.assertEqual(path.read_text(), "hello\n")
        with self.assertRaises(FileExistsError):
            write_file(path, "again\n")

    def test_link_note_is_idempotent_and_rejects_conflicts(self):
        target = write_file(self.root / "target.md", "note\n")
        link = link_note(self.root / "link.md", target)
        self.assertEqual(link_note(link, target), link)

        other = write_file(self.root / "other.md", "other\n")
        with self.assertRaises(FileExistsError):
            link_note(link, other)
        regular = write_file(self.root / "regular.md", "regular\n")
        with self.assertRaises(FileExistsError):
            link_note(regular, target)

    def test_write_generation_writes_files_and_symlink(self):
        learnings, vault = self.root / "Learnings", self.root / "Vault"
        note = learnings / "note.md"
        result = write_generation(
            paths=Paths(learnings=learnings, vault=vault),
            files={learnings / "demo.cpp": "int main() {}\n", note: "_hello_\n"},
            note_path=note,
            symlink=True,
        )
        self.assertEqual(len(result.files), 2)
        self.assertEqual(len(result.symlinks), 1)
        self.assertEqual(result.symlinks[0].resolve(), note)
        self.assertEqual(note.read_text(), "_hello_\n")

    def test_write_generation_rejects_missing_vault_or_note(self):
        learnings = self.root / "Learnings"
        outputs = {learnings / "demo.cpp": "code\n"}
        with self.assertRaises(StubError):
            write_generation(
                paths=Paths(learnings=learnings),
                files=outputs,
                note_path=learnings / "note.md",
                symlink=True,
            )
        with self.assertRaises(StubError):
            write_generation(paths=Paths(learnings=learnings), files=outputs, symlink=True)

    def test_write_generation_does_not_partially_write(self):
        learnings = self.root / "Learnings"
        first = learnings / "first.cpp"
        second = learnings / "second.cpp"
        write_file(first, "old\n")
        with self.assertRaises(StubError):
            write_generation(
                paths=Paths(learnings=learnings),
                files={first: "new\n", second: "new\n"},
            )
        self.assertFalse(second.exists())
        self.assertEqual(first.read_text(), "old\n")


if __name__ == "__main__":
    unittest.main()
