from __future__ import annotations

import re
from dataclasses import dataclass, field

_HEADER_RE = re.compile(r"^(#{1,6}) +(.+?)[ \t]*$", re.MULTILINE)


@dataclass(slots=True)
class ObsidianSection:
    title: str
    level: int
    content: str = ""
    children: list[ObsidianSection] = field(default_factory=list)
    parent: ObsidianSection | None = None

    def add_child(self, section: ObsidianSection) -> None:
        section.parent = self
        self.children.append(section)

    @property
    def header(self) -> str:
        return f"{'#' * self.level} {self.title}"

    def to_markdown(self, include_children: bool = True) -> str:
        parts = [self.header, self.content]

        if include_children:
            parts.extend(
                child.to_markdown(include_children=True) for child in self.children
            )

        if parts[-1] == "":
            parts = parts[:-1]

        return "\n".join(parts)

    def find(self, title: str, level: int | None = None) -> ObsidianSection | None:
        if self.title == title and (level is None or self.level == level):
            return self

        for child in self.children:
            result = child.find(title, level)
            if result is not None:
                return result

        return None


@dataclass(slots=True)
class ObsidianDocument:
    preamble: str = ""
    sections: list[ObsidianSection] = field(default_factory=list)

    def from_text(text: str) -> ObsidianDocument:
        matches = list(_HEADER_RE.finditer(text))

        if not matches:
            return ObsidianDocument(preamble=text)

        # document = ObsidianDocument(preamble=text[: matches[0].start()].rstrip())
        preamble = text[: matches[0].start()]
        preamble = preamble.removesuffix("\n")
        document = ObsidianDocument(preamble=preamble)

        stack: list[ObsidianSection] = []

        for index, match in enumerate(matches):
            level = len(match.group(1))

            title = match.group(0)[level + 1 : match.end()]

            is_last_item = index + 1 == len(matches)

            content_start = match.end() + 1
            content_end = (
                len(text) if index + 1 == len(matches) else matches[index + 1].start()
            )

            content = text[content_start:content_end]  # .strip()
            if not is_last_item:
                content = content[:-1]

            section = ObsidianSection(
                title=title,
                level=level,
                content=content,
            )

            while stack and stack[-1].level >= level:
                stack.pop()

            if stack:
                stack[-1].add_child(section)
            else:
                document.sections.append(section)

            stack.append(section)

        return document

    def to_markdown(self) -> str:
        parts = []

        if self.preamble:
            parts.append(self.preamble)

        parts.extend(section.to_markdown() for section in self.sections)

        if len(parts) == 0:
            return ""

        if parts[-1] == "":
            parts = parts[:-1]

        return "\n".join(parts)

    def find(self, title: str, level: int | None = None) -> ObsidianSection | None:
        for section in self.sections:
            result = section.find(title, level)
            if result is not None:
                return result

        return None

    def section(self, title: str) -> str:
        section = self.find(title)

        if section is None:
            raise KeyError(f"Section {title!r} not found.")

        return section.to_markdown()
