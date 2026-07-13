from pathlib import Path

from .note import ObsidianNote
from .query import ObsidianQuery


class ObsidianVault:
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path)

    def notes(self):
        for path in self.vault_path.rglob("*.md"):
            yield ObsidianNote.from_file(path)

    def query(self):
        return ObsidianQuery(self.notes)

    def show_note(self, note_path):
        note = self.read_note(note_path)
        note.show()

    def read_note(self, note_path):
        return ObsidianNote.from_file(self.vault_path / note_path)

    def write_note(self, note_path, fm, body, spaces=1):
        note = ObsidianNote(path=self.vault_path / note_path, fm=fm, body=body)
        note.to_file(spaces)
