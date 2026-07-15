from __future__ import annotations

import re
from dataclasses import dataclass

_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def _parse_links(text: str) -> list[ObsidianLink]:
    links = []

    for match in _LINK_RE.finditer(text):
        raw = match.group(1)

        target, alias = (raw.split("|", 1) + [None])[:2]

        heading = None
        block = None

        if "#" in target:
            target, heading = target.split("#", 1)
        elif "^" in target:
            target, block = target.split("^", 1)

        links.append(
            ObsidianLink(
                target=target,
                alias=alias,
                heading=heading,
                block=block,
            )
        )

    return links


@dataclass(frozen=True, slots=True)
class ObsidianLink:
    target: str
    alias: str | None = None
    heading: str | None = None
    block: str | None = None
