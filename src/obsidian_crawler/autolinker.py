import hashlib
import re
from collections.abc import Iterable
from dataclasses import dataclass
from warnings import warn

from .link import ObsidianLink
from .note import ObsidianNote
from .query import ObsidianQuery


def _get_token(text: str) -> str:
    """Return a unique token for the given text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class AutoLinkRule:
    link: ObsidianLink
    whole_words: bool = True
    extra_word_chars: str = ""
    ignore_case: bool = False

    def apply_rule(self, text: str, old: str, new: str) -> str:
        """Replace whole word occurrences of 'old' with 'new' in 'text',
        respecting full words and additional word characters.

        word_chars: characters that should not appear immediately
        before or after the match.

        if word_chars is None, then words are replaced regardless of what characters are around them.
        """

        if not self.whole_words:
            return text.replace(old, new)

        flags = re.IGNORECASE if self.ignore_case else 0

        extra = re.escape(self.extra_word_chars)
        pattern = rf"(?<![\w{extra}]){re.escape(old)}(?![\w{extra}])"

        return re.sub(pattern, new, text, flags=flags)


class ObsidianAutoLinker:
    def __init__(self):
        self._link_rules: dict[str, AutoLinkRule] = {}

    def _add_link(
        self,
        key: str,
        link: ObsidianLink,
        whole_words: bool = True,
        extra_word_chars: str = "",
    ) -> None:

        if key in self._link_rules:
            warn(
                f"Duplicate auto-link trigger '{key}'. "
                f"'{self._link_rules[key].link.to_markdown()}' "
                f"will be replaced by "
                f"'{link.to_markdown()}'."
            )
        self._link_rules[key] = AutoLinkRule(link, whole_words, extra_word_chars)

    def add_notes(
        self,
        notes: Iterable[ObsidianNote] | ObsidianQuery,
        title: bool = True,
        aliases: bool = True,
        lowercase_title: bool = False,
        verbose: bool = False,
        whole_words: bool = True,
        extra_word_chars: str = "",
    ) -> None:
        """
        Register notes as auto-link targets.

        Rules are applied in the order they are added.
        Earlier rules take precedence over later ones when they overlap.
        """

        if isinstance(notes, ObsidianQuery):
            notes = notes.all()

        if not whole_words and extra_word_chars != "":
            warn(
                "extra_word_chars is ignored when whole_words is False. "
                "Set whole_words to True to use extra_word_chars."
            )

        if title:
            for note in notes:
                self._add_link(
                    note.title, ObsidianLink(note.title), whole_words, extra_word_chars
                )

                if lowercase_title:
                    title_lower = note.title.lower()
                    self._add_link(
                        title_lower,
                        ObsidianLink(note.title, alias=title_lower),
                        whole_words,
                        extra_word_chars,
                    )

        if aliases:
            for note in notes:
                if (aliases := note.fm.get("aliases", [])) is None:
                    if verbose:
                        warn(f"Note '{note.title}' has no aliases.")
                    continue

                for alias in aliases:
                    self._add_link(
                        alias,
                        ObsidianLink(note.title, alias),
                        whole_words,
                        extra_word_chars,
                    )

    def run(self, text: str | ObsidianNote) -> str:
        """
        Replace known text by Obsidian links.

        Existing links are left untouched.

        Rules are applied in insertion order.
        This allows callers to control priority when multiple rules
        could match the same text.
        """

        if isinstance(text, ObsidianNote):
            text = text.body

        protected: dict[str, str] = {}

        # protect existing links beforehand
        for link in ObsidianLink.parse(text):
            markdown = link.to_markdown()
            token = _get_token(markdown)
            protected[token] = markdown
            text = text.replace(markdown, token)

        # create a token for each link to be replaced, and replace it in the text
        for source, link_rule in self._link_rules.items():
            # markdown = link.to_markdown()
            token = _get_token(link_rule.link.to_markdown())
            protected[token] = link_rule.link.to_markdown()
            text = link_rule.apply_rule(text, source, token)

        for token, markdown in protected.items():
            text = text.replace(token, markdown)

        return text
