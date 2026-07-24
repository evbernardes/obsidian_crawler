from typing import Any

import yaml

from .block import MarkdownBlock


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


def parse_blocks(text: str) -> list[MarkdownBlock]:
    """
    Split Markdown into alternating text and fenced code blocks.

    Reconstruction is lossless:

        ''.join(block.to_markdown() for block in blocks) == text
    """

    lines = text.splitlines(keepends=True)

    blocks: list[MarkdownBlock] = []

    buffer: list[str] = []

    in_code = False
    code_type = ""

    for line in lines:
        if not in_code:
            if line.startswith("```"):
                if buffer:
                    blocks.append(
                        MarkdownBlock(
                            "text",
                            "".join(buffer),
                        )
                    )
                    buffer.clear()

                code_type = line[3:].strip()
                in_code = True

            else:
                buffer.append(line)

        else:
            if line.startswith("```"):
                blocks.append(
                    MarkdownBlock(
                        code_type,
                        "".join(buffer),
                    )
                )

                buffer.clear()
                in_code = False
                code_type = ""

            else:
                buffer.append(line)

    if buffer:
        blocks.append(
            MarkdownBlock(
                code_type if in_code else "text",
                "".join(buffer),
            )
        )

    return blocks


def fuse_blocks(blocks) -> str:
    full_text = ""
    N = len(blocks)
    for i, block in enumerate(blocks):
        if block.is_code:
            full_text += block.to_markdown()
            if i < N - 1:
                full_text += "\n"
        else:
            full_text += block.to_markdown()

    return full_text
