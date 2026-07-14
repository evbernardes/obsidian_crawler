import warnings
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
        self._title_cache = None

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

    def _cache_note(self, entry: CachedNote):
        """
        Insert or replace a note in every cache/index.
        """
        self._cache[entry.note.path.resolve()] = entry

        if self._title_cache is not None:
            self._title_cache[entry.note.title] = entry.note

    def _load_notes(self):
        """Load the entire vault."""
        return {
            path.resolve(): self._load_note(path)
            for path in self.vault_path.rglob("*.md")
        }

    def load(self):
        """
        Explicitly populate the cache.
        """
        if self._cache is None:
            self._cache = self._load_notes()
        return self

    def _build_title_cache(self):
        self.load()

        title_cache = {}

        for entry in self._cache.values():
            note = entry.note

            if note.title in title_cache:
                warnings.warn(
                    f"Duplicate note title '{note.title}'. "
                    "Keeping the first occurrence for link resolution.",
                    RuntimeWarning,
                )
                continue

            title_cache[note.title] = note

        self._title_cache = title_cache

    def refresh(self):
        self._cache = None
        self._title_cache = None

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

    def resolve(self, link):
        if self._title_cache is None:
            self._build_title_cache()

        target = link.target if hasattr(link, "target") else str(link)

        return self._title_cache.get(target)

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
            self._cache_note(entry)
            return entry.note

        current_mtime = path.stat().st_mtime_ns
        if current_mtime != entry.mtime:
            entry = self._load_note(path)
            self._cache_note(entry)

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
            self._cache_note(
                CachedNote(
                    note=note,
                    mtime=path.stat().st_mtime_ns,
                )
            )
