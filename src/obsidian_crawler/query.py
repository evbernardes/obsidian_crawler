from collections import defaultdict


def _resolve_key(key):
    if callable(key):
        return key
    return lambda note: note.fm.get(key)


class ObsidianQuery:
    def __init__(self, source, pipeline=()):
        """
        source: callable returning a fresh iterable of notes
        pipeline: tuple of transformations
        """
        self._source = source
        self._pipeline = pipeline

    # --------------------------------------------------
    # Internal
    # --------------------------------------------------

    def _clone(self, operation):
        return ObsidianQuery(
            self._source,
            self._pipeline + (operation,),
        )

    def _iter(self):
        notes = self._source()

        for operation in self._pipeline:
            notes = operation(notes)

        return iter(notes)

    # --------------------------------------------------
    # Filtering
    # --------------------------------------------------

    def where(self, predicate):
        return self._clone(lambda notes: filter(predicate, notes))

    def with_tag(self, tag):
        return self.where(lambda n: tag in n.tags)

    def with_tags(self, *tags, require_all=True):
        if require_all:
            return self.where(lambda n: all(tag in n.tags for tag in tags))

        return self.where(lambda n: any(tag in n.tags for tag in tags))

    # --------------------------------------------------
    # Projection
    # --------------------------------------------------

    def map(self, func):
        return self._clone(lambda notes: map(func, notes))

    # --------------------------------------------------
    # Ordering
    # --------------------------------------------------

    def sort(self, key=None, reverse=False):
        return self._clone(lambda notes: sorted(notes, key=key, reverse=reverse))

    # --------------------------------------------------
    # Materialization
    # --------------------------------------------------

    def all(self):
        return list(self._iter())

    def first(self):
        return next(self._iter(), None)

    def find(self, predicate):
        return next(filter(predicate, self._iter()), None)

    def count(self):
        return sum(1 for _ in self._iter())

    # --------------------------------------------------
    # Dictionaries
    # --------------------------------------------------

    def group_by(self, key):
        key_func = _resolve_key(key)

        groups = defaultdict(list)

        for note in self._iter():
            groups[key_func(note)].append(note)

        return dict(groups)

    def group_by_many(self, group_key, key_sort=None, item_sort=None, reverse=False):
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

    def index_by(self, key):
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

    def __iter__(self):
        return self._iter()

    def __repr__(self):
        return f"<ObsidianQuery operations={len(self._pipeline)}>"
