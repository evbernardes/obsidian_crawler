from __future__ import annotations

import time
import warnings
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, Iterator

from .link import ObsidianLink
from .note import ObsidianNote
from .query import ObsidianQuery


class VaultChange(Enum):
    NEW = auto()
    MODIFIED = auto()
    REMOVED = auto()


@dataclass(slots=True)
class CachedNote:
    note: ObsidianNote
    mtime: int


class ObsidianVault:
    def __init__(self, vault_path: str | Path, auto_update: bool = True):
        self._last_scan: int
        self.vault_path = Path(vault_path)
        self._auto_update: bool = auto_update
        self._cache: dict[Path, CachedNote] | None = None
        self._title_cache: dict[str, ObsidianNote] | None = None

    # ---------------------------------------------------------
    # Cache management
    # ---------------------------------------------------------
    def _load_note(self, path: str | Path) -> CachedNote:
        """Load a single note and its metadata."""
        path = Path(path).resolve()

        return CachedNote(
            note=ObsidianNote.from_file(path),
            mtime=path.stat().st_mtime_ns,
        )

    def _cache_note(self, entry: CachedNote) -> None:
        """
        Insert or replace a note in every cache/index.
        """
        # self._cache[entry.note.path.resolve()] = entry

        # if self._title_cache is not None:
        #     self._title_cache[entry.note.title] = entry.note

        path = entry.note.path.resolve()

        old_entry = self._cache.get(path)

        if old_entry and self._title_cache is not None:
            if old_entry.note.title != entry.note.title:
                self._title_cache.pop(old_entry.note.title, None)

        self._cache[path] = entry

        if self._title_cache is not None:
            self._title_cache[entry.note.title] = entry.note

    def _remove_cached_note(self, entry: CachedNote) -> None:

        if self._cache is not None:
            self._cache.pop(entry.note.path.resolve(), None)

        if self._title_cache is not None:
            self._title_cache.pop(entry.note.title, None)

    def _load_notes(self) -> dict[Path, CachedNote]:
        """Load the entire vault."""
        return {
            path.resolve(): self._load_note(path)
            for path in self.vault_path.rglob("*.md")
        }

    def load(self) -> list[ObsidianVault]:
        """
        Explicitly populate the cache.
        """
        if self._cache is None:
            self._cache = self._load_notes()
        return self

    def _build_title_cache(self) -> None:
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

    def refresh(self) -> None:
        self._cache = None
        self._title_cache = None

    def _detect_changes(self) -> dict[Path, VaultChange]:
        """Returns paths of notes that changed on the disk"""
        if self._cache is None:
            raise RuntimeError(
                "Cannot scan for changes if the Vault has not yet been loaded"
            )

        remaining = set(self._cache)

        times_new = {
            path.resolve(): path.stat().st_mtime_ns
            for path in self.vault_path.rglob("*.md")
        }

        changes = {}
        for path, time in times_new.items():
            if path not in self._cache:
                changes[path] = VaultChange.NEW
                continue

            remaining.remove(path)

        if self._cache[path].mtime != time:
            changes[path] = VaultChange.MODIFIED

        for path in remaining:
            changes[path] = VaultChange.REMOVED

        return changes

    def update(self) -> dict[Path, VaultChange]:

        try:
            changes = self._detect_changes()
        except RuntimeError:
            warnings.warn(
                "Tried updating before loading for the first time, loading vault now...",
                RuntimeWarning,
            )
            self.load()
            return

        for path, diff in changes.items():
            if diff == VaultChange.NEW or diff == VaultChange.MODIFIED:
                entry = self._load_note(path)
                self._cache_note(entry)
            if diff == VaultChange.REMOVED:
                self._remove_cached_note(self._cache[path])

        return changes

    def _ensure_updated(self) -> None:
        now = time.monotonic_ns()

        if now - self._last_scan > 500_000_000:  # 0.5 s
            self.update()
            self._last_scan = now

    # ---------------------------------------------------------
    # Notes / Queries
    # ---------------------------------------------------------
    def notes(self) -> Iterator[ObsidianNote]:
        """
        Iterate over all notes.

        Cached notes are automatically reloaded if the
        underlying file has changed on disk.
        """
        self.load()
        if self._auto_update:
            self._ensure_updated()
        yield from (entry.note for entry in self._cache.values())

    def query(self) -> ObsidianQuery:
        return ObsidianQuery(self.notes)

    def resolve_link(
        self,
        link: ObsidianLink | str,
    ) -> ObsidianNote | None:
        self.load()
        if self._auto_update:
            self._ensure_updated()

        if self._title_cache is None:
            self._build_title_cache()

        target = link.target if hasattr(link, "target") else str(link)

        return self._title_cache.get(target)

    # ---------------------------------------------------------
    # Individual note access
    # ---------------------------------------------------------
    def show_note(self, note_path: str | Path) -> None:
        self.read_note(note_path).show()

    def read_note(
        self,
        note_path: str | Path,
    ) -> ObsidianNote:
        """
        Read a note.

        If the note is cached, its modification time is checked.
        The note is transparently reloaded if the file changed.
        """
        self.load()
        if self._auto_update:
            self._ensure_updated()

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

    def by_title(self, title: str) -> ObsidianNote:
        note = self.resolve_link(title)

        if note is None:
            raise KeyError(f"No note named '{title}'.")

        return note

    # ---------------------------------------------------------
    # Note writing and modification
    # ---------------------------------------------------------

    def write(
        self,
        note_path: str | Path,
        fm: dict[str, Any],
        body: str,
    ) -> None:
        path = self.vault_path / note_path

        note = ObsidianNote(
            path=path,
            fm=fm,
            body=body,
        )

        note.write()

        if self._cache is not None:
            self._cache_note(
                CachedNote(
                    note=note,
                    mtime=path.stat().st_mtime_ns,
                )
            )

    def move(
        self,
        note: ObsidianNote,
        new_path: str | Path,
    ) -> ObsidianNote:
        """
        Move a note to another location in the vault.
        """
        old_path = note.path.resolve()

        new_path = (
            new_path
            if isinstance(new_path, Path) and new_path.is_absolute()
            else self.vault_path / new_path
        ).resolve()

        if not old_path.exists():
            raise FileNotFoundError(old_path)

        if new_path.exists():
            raise FileExistsError(new_path)

        new_path.parent.mkdir(parents=True, exist_ok=True)

        entry = None
        if self._cache is not None:
            entry = self._cache.pop(old_path, None)
        if entry is not None:
            self._remove_cached_note(entry)

        old_path.rename(new_path)
        note.path = new_path

        if self._cache is not None:
            self._cache_note(
                CachedNote(
                    note=note,
                    mtime=new_path.stat().st_mtime_ns,
                )
            )

        return note

    def rename(
        self,
        note: ObsidianNote,
        new_name: str,
    ) -> ObsidianNote:
        """
        Rename a note while keeping it in the same folder.

        Parameters
        ----------
        note_path:
            Existing note path relative to the vault.
        new_name:
            New filename. Can include or omit .md.
        """
        # old_path = (self.vault_path / note_path).resolve()

        if not new_name.endswith(".md"):
            new_name += ".md"

        return self.move(note, note.path.with_name(new_name))

    def delete(
        self,
        note: ObsidianNote,
    ) -> None:
        """
        Delete a note from the vault.
        """
        path = note.path.resolve()

        if not path.exists():
            raise FileNotFoundError(path)

        if self._cache is not None:
            entry = self._cache.get(path)
            if entry is not None:
                self._remove_cached_note(entry)

        path.unlink()
