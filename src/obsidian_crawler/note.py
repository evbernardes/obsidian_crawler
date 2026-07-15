from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from .vault import ObsidianVault

import yaml

from .link import ObsidianLink, _parse_links


def _remove_dataviewjs_blocks(text: str) -> str:
    return re.sub(r"```dataviewjs\s*[\s\S]*?```", "", text, flags=re.IGNORECASE).strip()


def _split_frontmatter(md_text: str) -> tuple[dict[str, Any], str]:
    """
    Extract YAML frontmatter from the beginning of a Markdown file.

    Returns
    -------
    (frontmatter: dict, body: str)

    Raises
    ------
    ValueError
        If the file does not begin with valid YAML frontmatter.
    """
    lines = md_text.splitlines(keepends=True)

    if not lines or lines[0].strip() != "---":
        raise ValueError("File does not start with YAML frontmatter.")

    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ValueError("Closing YAML delimiter not found.")

    yaml_text = "".join(lines[1:end])
    body = "".join(lines[end + 1 :])

    fm = yaml.safe_load(yaml_text) or {}

    return fm, body


def _join_frontmatter(fm: dict[str, Any], body: str) -> str:
    fm_yaml = yaml.dump(fm, sort_keys=False)
    return f"---\n{fm_yaml}---\n{body}"


class ObsidianNote:
    def _calculate_hash(self) -> str:
        # if content is None:
        return hashlib.sha256(
            _join_frontmatter(self.fm, self.body).encode("utf-8")
        ).hexdigest()

    def _update_snapshot(self) -> None:
        self._original_content = {"fm": deepcopy(self.fm), "body": self.body}
        self._hash = self._calculate_hash()
        self._links = _parse_links(self.body)

    def reset(self) -> None:
        self.fm = deepcopy(self._original_content["fm"])
        self.body = self._original_content["body"]

    def __init__(
        self,
        path: str | Path,
        fm: dict[str, Any] | None = None,
        body: str | None = None,
    ):
        self.path = path
        self.fm = {} if fm is None else fm
        self.body = "" if body is None else body

        self._update_snapshot()

    @classmethod
    def from_file(cls, path: str | Path) -> list[ObsidianNote]:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Note {path} does not exist.")
        content = path.read_text()
        try:
            fm, body = _split_frontmatter(content)
        except ValueError:
            # print(f"Error parsing {path}: {e}")
            fm = {}
            body = content
        return cls(path=path, fm=fm, body=body)

    def write(self, path: str | Path | None = None) -> bool:
        target = self.path if path is None else Path(path)

        if not self.modified and target == self.path:
            return False

        content = _join_frontmatter(self.fm, self.body)
        target.write_text(content, encoding="utf-8")

        self.path = target
        self._update_snapshot()

        return True

    def __repr__(self) -> str:
        return f"<ObsidianNote {self.title}>"

    @property
    def modified(self) -> bool:
        return self._calculate_hash() != self._hash

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, value: str | Path) -> None:
        self._path = Path(value)

    @property
    def fm(self) -> dict[str, Any]:
        return self._fm

    @fm.setter
    def fm(self, value: dict[str, Any]) -> None:
        if not isinstance(value, dict):
            raise TypeError("fm must be a dictionary")
        self._fm = value

    @property
    def body(self) -> str:
        return self._body

    @body.setter
    def body(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("body must be a string")
        self._body = value
        self._links = _parse_links(value)

    @property
    def body_without_dataview_blocks(self):
        return _remove_dataviewjs_blocks(self.body)

    @property
    def title(self) -> str:
        return self.path.stem

    @property
    def body_without_dataviewjs(self) -> str:
        return _remove_dataviewjs_blocks(self.body)

    @property
    def tags(self) -> list[str]:
        return self.fm.get("tags", [])

    @property
    def as_json(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "fm": self.fm,
            "body": self.body,
        }

    @property
    def links(self) -> list[ObsidianLink]:
        return self._links

    def linked_notes(
        self,
        vault: ObsidianVault,
    ) -> Iterator[ObsidianNote]:

        for link in self.links:
            note = vault.resolve_link(link)
            if note is not None:
                yield note

    def show(self) -> None:
        print(
            f"Frontmatter:\n{yaml.dump(self.fm, sort_keys=False)}\nBody:\n{self.body}"
        )
