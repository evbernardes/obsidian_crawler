import hashlib
import re
from collections.abc import Iterable
from warnings import warn

from .link import ObsidianLink
from .note import ObsidianNote
from .query import ObsidianQuery


def _replace_word(text, old, new, ignore_case=False, extra_boundary_chars=""):
    """Replace whole word occurrences of 'old' with 'new' in 'text',
    respecting full words and additional boundary characters.

    extra_boundary_chars: characters that should not appear immediately
    before or after the match.
    """
    flags = re.IGNORECASE if ignore_case else 0

    extra = re.escape(extra_boundary_chars)
    pattern = rf"(?<![\w{extra}]){re.escape(old)}(?![\w{extra}])"

    return re.sub(pattern, new, text, flags=flags)


class ObsidianAutoLinker:
    def __init__(self):
        self._links: dict[str, ObsidianLink] = {}
        self._extra_boundary_chars: dict[str, str] = {}

    def _add_link(
        self, key: str, link: ObsidianLink, extra_boundary_chars: str = ""
    ) -> None:
        self._links[key] = link
        self._extra_boundary_chars[key] = extra_boundary_chars

    def add_notes(
        self,
        notes: Iterable[ObsidianNote] | ObsidianQuery,
        title: bool = True,
        aliases: bool = True,
        lowercase_title: bool = False,
        verbose: bool = False,
        extra_boundary_chars: str = "",
    ) -> None:

        if isinstance(notes, ObsidianQuery):
            notes = notes.all()

        if title:
            for note in notes:
                self._add_link(
                    note.title, ObsidianLink(note.title), extra_boundary_chars
                )

                if lowercase_title:
                    title_lower = note.title.lower()
                    self._add_link(
                        title_lower,
                        ObsidianLink(note.title, alias=title_lower),
                        extra_boundary_chars,
                    )

        if aliases:
            for note in notes:
                if (aliases := note.fm.get("aliases", [])) is None:
                    if verbose:
                        warn(f"Note '{note.title}' has no aliases.")
                    continue

                for alias in aliases:
                    self._add_link(
                        alias, ObsidianLink(note.title, alias), extra_boundary_chars
                    )

    def run(self, text: str | ObsidianNote) -> str:
        """
        Replace known text by Obsidian links.

        Existing links are left untouched.
        """

        if isinstance(text, ObsidianNote):
            text = text.body

        protected: dict[str, str] = {}

        # protect existing links beforehand
        for link in ObsidianLink.parse(text):
            markdown = link.to_markdown()
            token = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
            protected[token] = markdown
            text = text.replace(markdown, token)

        # create a token for each link to be replaced, and replace it in the text
        for source, link in self._links.items():
            # markdown = link.to_markdown()
            token = hashlib.sha256(source.encode("utf-8")).hexdigest()
            protected[token] = link.to_markdown()
            text = _replace_word(
                text,
                source,
                token,
                extra_boundary_chars=self._extra_boundary_chars[source],
            )

        for token, markdown in protected.items():
            text = text.replace(token, markdown)

        return text
