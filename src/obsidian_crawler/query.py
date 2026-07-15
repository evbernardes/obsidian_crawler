from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any, Iterable, Iterator

from .note import ObsidianNote


def _resolve_key(
    key: str | Callable[[ObsidianNote], Any],
) -> Callable[[ObsidianNote], Any]:
    if callable(key):
        return key
    return lambda note: note.fm.get(key)


class ObsidianQuery:
    def __init__(
        self,
        source: Callable[[], Iterable[ObsidianNote]],
        pipeline: tuple[Callable[[Iterable[Any]], Iterable[Any]], ...] = (),
    ):
        """
        source: callable returning a fresh iterable of notes
        pipeline: tuple of transformations
        """
        self._source = source
        self._pipeline = pipeline

    # --------------------------------------------------
    # Internal
    # --------------------------------------------------

    def _clone(self, operation) -> list[ObsidianQuery]:
        return ObsidianQuery(
            self._source,
            self._pipeline + (operation,),
        )

    def _iter(self) -> Iterator[ObsidianNote]:
        notes = self._source()

        for operation in self._pipeline:
            notes = operation(notes)

        return iter(notes)

    # --------------------------------------------------
    # Filtering
    # --------------------------------------------------

    def where(
        self,
        predicate: Callable[[ObsidianNote], bool],
    ) -> list[ObsidianQuery]:
        return self._clone(lambda notes: filter(predicate, notes))

    def with_tag(self, tag: str) -> list[ObsidianQuery]:
        return self.where(lambda n: tag in n.tags)

    def with_tags(self, *tags: str, require_all: bool = True) -> list[ObsidianQuery]:
        if require_all:
            return self.where(lambda n: all(tag in n.tags for tag in tags))

        return self.where(lambda n: any(tag in n.tags for tag in tags))

    # --------------------------------------------------
    # Projection
    # --------------------------------------------------

    def map(
        self,
        func: Callable[[ObsidianNote], Any],
    ) -> list[ObsidianQuery]:
        return self._clone(lambda notes: map(func, notes))

    # --------------------------------------------------
    # Ordering
    # --------------------------------------------------

    def sort(
        self, key: Callable[[ObsidianNote], Any] | None = None, reverse: bool = False
    ) -> list[ObsidianQuery]:
        return self._clone(lambda notes: sorted(notes, key=key, reverse=reverse))

    # --------------------------------------------------
    # Materialization
    # --------------------------------------------------

    def all(self) -> list[ObsidianNote]:
        return list(self._iter())

    def first(self) -> ObsidianNote | None:
        return next(self._iter(), None)

    def find(
        self,
        predicate: Callable[[ObsidianNote], bool],
    ) -> ObsidianNote | None:
        return next(filter(predicate, self._iter()), None)

    def count(self) -> int:
        return sum(1 for _ in self._iter())

    # --------------------------------------------------
    # Dictionaries
    # --------------------------------------------------

    def group_by(
        self,
        key: str | Callable[[ObsidianNote], Any],
    ) -> dict[Any, list[ObsidianNote]]:
        key_func = _resolve_key(key)

        groups = defaultdict(list)

        for note in self._iter():
            groups[key_func(note)].append(note)

        return dict(groups)

    def group_by_many(
        self,
        group_key: str | Callable[[ObsidianNote], Any],
        key_sort: Callable[[Any], Any] | None = None,
        item_sort: Callable[[ObsidianNote], Any] | None = None,
        reverse: bool = False,
    ) -> dict[Any, list[ObsidianNote]]:
        key_func = _resolve_key(group_key)
        groups = defaultdict(list)

        for note in self._iter():
            keys = key_func(note)

            if isinstance(keys, str):
                keys = [keys]

            for k in keys:
                groups[k].append(note)

        if item_sort:
            for items in groups.values():
                items.sort(key=item_sort, reverse=reverse)

        if key_sort:
            groups = dict(sorted(groups.items(), key=lambda item: key_sort(item[0])))

        return dict(groups)

    def index_by(
        self,
        key: str | Callable[[ObsidianNote], Any],
    ) -> dict[Any, ObsidianNote]:
        key_func = _resolve_key(key)

        result = {}

        for note in self._iter():
            k = key_func(note)

            if k in result:
                raise ValueError(
                    f"Duplicate index key '{k}' found:\n"
                    f"- {result[k].path}\n"
                    f"- {note.path}\n\n"
                    "index_by() expects unique keys. "
                    "Use group_by() if duplicate keys are expected."
                )

            result[k] = note

        return result

    # --------------------------------------------------
    # Python protocol
    # --------------------------------------------------

    def __iter__(self) -> Iterator[ObsidianNote]:
        return self._iter()

    def __repr__(self) -> str:
        return f"<ObsidianQuery operations={len(self._pipeline)}>"
