#!/usr/bin/env python3
from dataclasses import dataclass


@dataclass(frozen=False, slots=True)
class MarkdownBlock:
    """
    Represents a block of Markdown.

    A block is either plain text (type="text") or a fenced code block
    such as python, dataview, dataviewjs, etc.
    """

    type: str
    content: str

    @property
    def is_code(self) -> bool:
        return self.type != "text"

    def to_markdown(self) -> str:
        if self.type == "text":
            return self.content

        return f"```{self.type}\n{self.content}```"
