import re
from pathlib import Path

import yaml


def _remove_dataviewjs_blocks(text):
    return re.sub(r"```dataviewjs\s*[\s\S]*?```", "", text, flags=re.IGNORECASE).strip()


def _split_frontmatter(md_text: str):
    """Extract YAML frontmatter delimited by --- ... --- at the top of the file."""
    if not md_text.lstrip().startswith("---"):
        raise ValueError("File does not start with YAML frontmatter '---'")

    # Match first frontmatter block at top of file
    m = re.match(r"^\s*---\s*\n(.*?)\n---\s*\n(.*)$", md_text, flags=re.DOTALL)
    if not m:
        raise ValueError(
            "Could not parse YAML frontmatter. Ensure it is delimited by --- on its own lines."
        )

    yaml_text = m.group(1)
    body_text = m.group(2).strip()
    fm = yaml.safe_load(yaml_text) or {}
    return fm, body_text


def _join_frontmatter(fm, body, spaces=1):
    fm_yaml = yaml.dump(fm, sort_keys=False)
    return f"---\n{fm_yaml}---" + "\n" * spaces + f"{body}"


class ObsidianNote:
    def __init__(self, path, fm=None, body=None):
        self._path = path
        self.fm = {} if fm is None else fm
        self.body = "" if body is None else body
        # self.raw_content = raw_content if raw_content is not None else ""

    @classmethod
    def from_file(cls, path):
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

    def write(self, path=None, spaces=1):
        if path is None:
            path = self.path
        else:
            path = Path(path)
        content = _join_frontmatter(self.fm, self.body, spaces)
        self.path.write_text(content, encoding="utf-8")

    def __repr__(self):
        return f"<ObsidianNote {self.title}>"

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = Path(value)

    @property
    def fm(self):
        return self._fm

    @fm.setter
    def fm(self, value):
        if not isinstance(value, dict):
            raise TypeError("fm must be a dictionary")
        self._fm = value

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, value):
        if not isinstance(value, str):
            raise TypeError("body must be a string")
        self._body = value

    @property
    def body_without_dataview_blocks(self):
        return _remove_dataviewjs_blocks(self.body)

    @property
    def title(self):
        return self.path.stem

    @property
    def body_without_dataviewjs(self):
        return _remove_dataviewjs_blocks(self.body)

    @property
    def tags(self):
        return self.fm.get("tags", [])

    @property
    def as_json(self):
        return {
            "path": str(self.path),
            "fm": self.fm,
            "body": self.body,
        }

    def show(self):
        print(
            f"Frontmatter:\n{yaml.dump(self.fm, sort_keys=False)}\nBody:\n{self.body}"
        )
