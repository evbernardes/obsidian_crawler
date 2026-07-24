from typing import Any

import yaml


def _find_fence(
    lines: list[str],
    start: int,
    fence: str,
) -> int:
    for i in range(start, len(lines)):
        if lines[i].strip() == fence:
            return i

    raise ValueError(f"Closing '{fence}' delimiter not found.")


def parse_content(md_text: str) -> tuple[dict[str, Any], str]:
    """
    Extract YAML frontmatter and body.

    Returns
    -------
    (frontmatter, body)
    """
    lines = md_text.splitlines(keepends=True)

    if not lines or lines[0].strip() != "---":
        raise ValueError("File does not start with YAML frontmatter.")

    end = _find_fence(lines, 1, "---")

    fm = yaml.safe_load("".join(lines[1:end])) or {}
    body = "".join(lines[end + 1 :])

    return fm, body


def fuse_content(fm: dict[str, Any], body: str) -> str:
    fm_yaml = yaml.dump(fm, sort_keys=False)
    return f"---\n{fm_yaml}---\n{body}"
