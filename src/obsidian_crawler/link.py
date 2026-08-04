from __future__ import annotations

import re
from dataclasses import dataclass

_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


@dataclass(frozen=True, slots=True)
class ObsidianLink:
    target: str
    alias: str | None = None
    heading: str | None = None
    block: str | None = None

    def to_markdown(self) -> str:
        target = self.target

        if self.heading is not None:
            target += f"#{self.heading}"

        if self.block is not None:
            target += f"^{self.block}"

        if self.alias is not None:
            target += f"|{self.alias}"

        return f"[[{target}]]"

    def render(self) -> str:
        """
        Return the text displayed by Obsidian in Reading View.
        """

        if self.alias is not None:
            return self.alias

        target = self.target

        if self.heading is not None:
            target += f"#{self.heading}"

        if self.block is not None:
            target += f"^{self.block}"

        return target

    @staticmethod
    def parse(text: str) -> list[ObsidianLink]:
        links = []

        for match in _LINK_RE.finditer(text):
            raw = match.group(1)

            target, alias = (raw.split("|", 1) + [None])[:2]

            heading = None
            block = None

            # Parse block first
            if "^" in target:
                target, block = target.split("^", 1)

            # Then heading
            if "#" in target:
                target, heading = target.split("#", 1)

            links.append(
                ObsidianLink(
                    target=target,
                    alias=alias,
                    heading=heading,
                    block=block,
                )
            )

        return links
