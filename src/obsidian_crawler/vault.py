from dataclasses import dataclass
from pathlib import Path

from .note import ObsidianNote
from .query import ObsidianQuery


@dataclass(slots=True)
class CachedNote:
    note: ObsidianNote
    mtime: int


class ObsidianVault:
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path)
        self._cache = None

    # ---------------------------------------------------------
    # Cache management
    # ---------------------------------------------------------
    def _load_note(self, path):
        """Load a single note and its metadata."""
        path = Path(path).resolve()

        return CachedNote(
            note=ObsidianNote.from_file(path),
            mtime=path.stat().st_mtime_ns,
        )

    def _load_notes(self):
        """Load the entire vault."""
        return {
            path.resolve(): self._load_note(path)
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

    # ---------------------------------------------------------
    # Notes / Queries
    # ---------------------------------------------------------
    def notes(self):
        """
        Iterate over all notes.

        Cached notes are automatically reloaded if the
        underlying file has changed on disk.
        """
        self.load()
        for path in list(self._cache):
            yield self.read_note(path)

    def query(self):
        return ObsidianQuery(self.notes)

    # ---------------------------------------------------------
    # Individual note access
    # ---------------------------------------------------------
    def show_note(self, note_path):
        self.read_note(note_path).show()

    def read_note(self, note_path):
        """
        Read a note.

        If the note is cached, its modification time is checked.
        The note is transparently reloaded if the file changed.
        """

        path = (self.vault_path / note_path).resolve()

        if self._cache is None:
            return ObsidianNote.from_file(path)

        entry = self._cache.get(path)

        if entry is None:
            entry = self._load_note(path)
            self._cache[path] = entry
            return entry.note

        current_mtime = path.stat().st_mtime_ns
        if current_mtime != entry.mtime:
            entry = self._load_note(path)
            self._cache[path] = entry
        return entry.note

    def write_note(self, note_path, fm, body, spaces=1):
        path = self.vault_path / note_path

        note = ObsidianNote(
            path=path,
            fm=fm,
            body=body,
        )

        note.write(spaces=spaces)

        if self._cache is not None:
            self._cache[path.resolve()] = CachedNote(
                note=note,
                mtime=path.stat().st_mtime_ns,
            )
