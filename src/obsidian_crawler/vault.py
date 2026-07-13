from pathlib import Path

from .note import ObsidianNote
from .query import ObsidianQuery


class ObsidianVault:
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path)
        self._cache = None

    def _load_notes(self):
        return {
            path.resolve(): ObsidianNote.from_file(path)
            for path in self.vault_path.rglob("*.md")
        }

    def refresh(self):
        self._cache = None

    def load(self):
        """
        Explicitly populate the cache.
        """
        if self._cache is None:
            self._cache = self._load_notes()

        return self

    def notes(self):
        self.load()
        yield from self._cache.values()
        # for path in self.vault_path.rglob("*.md"):
        #     yield ObsidianNote.from_file(path)

    def query(self):
        return ObsidianQuery(self.notes)

    def show_note(self, note_path):
        note = self.read_note(note_path)
        note.show()

    def read_note(self, note_path):
        # return ObsidianNote.from_file(self.vault_path / note_path)

        path = (self.vault_path / note_path).resolve()

        if self._cache is not None:
            if path in self._cache:
                return self._cache[path]

        note = ObsidianNote.from_file(path)

        # Add to cache if cache is active
        if self._cache is not None:
            self._cache[path] = note

        return note

    def write_note(self, note_path, fm, body, spaces=1):
        path = self.vault_path / note_path

        note = ObsidianNote(
            path=path,
            fm=fm,
            body=body,
        )

        note.write(spaces=spaces)

        if self._cache is not None:
            self._cache[path.resolve()] = note
