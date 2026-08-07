#!/usr/bin/env python3
import hashlib
import re
from collections.abc import Iterable
from dataclasses import dataclass
from warnings import warn

from .link import ObsidianLink
from .note import ObsidianNote
from .parsers import fuse_blocks
from .query import ObsidianQuery


def _create_token(text: str) -> str:
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
    def __init__(self, auto_sort_by_key_length: bool = False):
        self._link_rules: dict[str, AutoLinkRule] = {}
        self._auto_sort_by_key_length: bool = auto_sort_by_key_length
        self._sorted: bool = False

    def add(
        self,
        trigger: str,
        link: ObsidianLink,
        whole_words: bool = True,
        extra_word_chars: str = "",
        verbose: bool = False,
        ignore_case: bool = False,
    ) -> None:
        """
        Register a single auto-link rule.
        """
        if verbose:
            print(f"Adding auto-link rule: '{trigger}' -> '{link.to_markdown()}'")

        if trigger in self._link_rules:
            warn(
                f"Duplicate auto-link trigger '{trigger}'. "
                f"'{self._link_rules[trigger].link.to_markdown()}' "
                f"will be replaced by "
                f"'{link.to_markdown()}'."
            )

        self._link_rules[trigger] = AutoLinkRule(
            link, whole_words, extra_word_chars, ignore_case
        )
        self._sorted = False

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
                self.add(
                    note.title,
                    ObsidianLink(note.title),
                    whole_words,
                    extra_word_chars,
                    verbose,
                )

                if lowercase_title:
                    title_lower = note.title.lower()
                    self.add(
                        title_lower,
                        ObsidianLink(note.title, alias=title_lower),
                        whole_words,
                        extra_word_chars,
                        verbose,
                    )

        if aliases:
            for note in notes:
                if (aliases := note.fm.get("aliases", [])) is None:
                    if verbose:
                        warn(f"Note '{note.title}' has no aliases.")
                    continue

                for alias in aliases:
                    if alias == note.title:
                        if verbose:
                            warn(
                                f"Note '{note.title}' has an alias that is the same as its title. "
                                "This alias will be ignored."
                            )
                        continue

                    self.add(
                        alias,
                        ObsidianLink(note.title, alias),
                        whole_words,
                        extra_word_chars,
                        verbose,
                    )

    def sort_by_key_length(self) -> None:
        """
        Set whether to sort the auto-link rules by key length.

        When enabled, longer keys will be matched first.
        This is useful when multiple rules could match the same text.
        """
        if not self._sorted:
            link_rules_list = list(self._link_rules.items())
            link_rules_list.sort(key=lambda x: len(x[0]), reverse=True)
            self._link_rules = dict(link_rules_list)
            self._sorted = True

    def run(self, text: str | ObsidianNote) -> str | ObsidianNote:
        """
        Replace known text by Obsidian links.

        Existing links are left untouched.

        If not sorted, rules are applied in insertion order.
        This allows callers to control priority when multiple rules
        could match the same text.
        """

        # sort_by_key_length = self._auto_sort_by_key_length

        if isinstance(text, ObsidianNote):
            note = text.copy()
            blocks = text.blocks
            for i, block in enumerate(blocks):
                if block.is_code:
                    continue
                block.content = self.run(block.content)
            note.body = fuse_blocks(blocks)
            return note

        protected: dict[str, str] = {}

        # protect existing links beforehand
        for link in ObsidianLink.parse(text):
            markdown = link.to_markdown()
            token = _create_token(markdown)
            protected[token] = markdown
            text = text.replace(markdown, token)

        # create a token for each link to be replaced, and replace it in the text
        if self._auto_sort_by_key_length:
            self.sort_by_key_length()

        for source, link_rule in self._link_rules.items():
            markdown = link_rule.link.to_markdown()
            token = _create_token(markdown)
            protected[token] = markdown
            text = link_rule.apply_rule(text, source, token)

        for token, markdown in protected.items():
            text = text.replace(token, markdown)

        return text
