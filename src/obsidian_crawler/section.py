from __future__ import annotations

import re
from dataclasses import dataclass, field

_HEADER_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)


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
        parts = [self.header]

        if self.content:
            parts.append(self.content)

        if include_children:
            parts.extend(
                child.to_markdown(include_children=True) for child in self.children
            )

        return "\n\n".join(parts)

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

        document = ObsidianDocument(preamble=text[: matches[0].start()].rstrip())

        stack: list[ObsidianSection] = []

        for index, match in enumerate(matches):
            level = len(match.group(1))
            title = match.group(2).strip()

            content_start = match.end()
            content_end = (
                matches[index + 1].start() if index + 1 < len(matches) else len(text)
            )

            content = text[content_start:content_end].strip()

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

        return "\n\n".join(parts)

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
