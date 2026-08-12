from obsidian_crawler.autolinker import ObsidianAutoLinker
from obsidian_crawler.note import ObsidianNote
from obsidian_crawler.vault import ObsidianVault

note_task_2_1_test = ObsidianNote(
    "T1.2 test Task.md", fm={"tags": ["task"], "aliases": ["T1.2"]}
)

note_task_6_2_llm = ObsidianNote(
    "T6.2 Using LLM concepts.md", fm={"tags": ["task"], "aliases": ["T6.2"]}
)

note_concept_llm = ObsidianNote(
    "Large Language Model.md", fm={"tags": ["concept"], "aliases": ["LLM"]}
)


def test_single_note_from_vault(tmp_path):
    vault = ObsidianVault(tmp_path)

    ObsidianNote(".", fm={"tags": ["task"], "aliases": ["T1.2"]}).write(
        vault.vault_path / "T1.2 test Task.md"
    )

    linker = ObsidianAutoLinker()

    text = "This is a test for T1.2 and T6.2 and LLM."
    assert linker.run(text) == text

    linker.add_notes(vault.query().with_tag("task"))

    text = "This is a test for T1.2 and T6.2 and LLM."
    assert (
        linker.run(text)
        == "This is a test for [[T1.2 test Task|T1.2]] and T6.2 and LLM."
    )

    text = "This is a test for T1.2 and T6.2 and LLM. It also links to [[T5.4 some other task|T5.4]."
    assert (
        linker.run(text)
        == "This is a test for [[T1.2 test Task|T1.2]] and T6.2 and LLM. It also links to [[T5.4 some other task|T5.4]."
    )


def test_two_notes_from_vault(tmp_path):
    vault = ObsidianVault(tmp_path)

    ObsidianNote(".", fm={"tags": ["task"], "aliases": ["T1.2"]}).write(
        vault.vault_path / "T1.2 test Task.md"
    )

    ObsidianNote(".", fm={"tags": ["task"], "aliases": ["T6.2"]}).write(
        vault.vault_path / "T6.2 Using LLM concepts.md"
    )

    linker = ObsidianAutoLinker()
    linker.add_notes(vault.query().with_tag("task"))

    text = "This is a test for T1.2 and T6.2 and LLM."
    assert (
        linker.run(text)
        == "This is a test for [[T1.2 test Task|T1.2]] and [[T6.2 Using LLM concepts|T6.2]] and LLM."
    )


def test_one_note_with_alias(tmp_path):
    vault = ObsidianVault(tmp_path)

    ObsidianNote(".", fm={"tags": ["task"], "aliases": ["T1.2"]}).write(
        vault.vault_path / "T1.2 test Task.md"
    )

    linker = ObsidianAutoLinker()
    linker.add_notes(vault.query().with_tag("task"))

    text = "This is a test for T1.2, which is T1.2 test Task."
    assert (
        linker.run(text)
        == "This is a test for [[T1.2 test Task|T1.2]], which is [[T1.2 test Task]]."
    )


def test_two_notes_overlapping(tmp_path):
    vault = ObsidianVault(tmp_path)

    ObsidianNote(".", fm={"tags": ["task"], "aliases": ["T6.2"]}).write(
        vault.vault_path / "T6.2 Using LLM concepts.md"
    )

    ObsidianNote(".", fm={"tags": ["concept"], "aliases": ["LLM"]}).write(
        vault.vault_path / "Large Language Model.md"
    )

    linker = ObsidianAutoLinker()
    linker.add_notes(vault.query().with_tag("task"))
    linker.add_notes(vault.query().with_tag("concept"))

    text = "This is a test for T6.2, which is T6.2 Using LLM concepts."
    assert (
        linker.run(text)
        == "This is a test for [[T6.2 Using LLM concepts|T6.2]], which is [[T6.2 Using LLM concepts]]."
    )


def test_two_notes_overlapping_bad_order(tmp_path):
    vault = ObsidianVault(tmp_path)

    ObsidianNote(".", fm={"tags": ["task"], "aliases": ["T6.2"]}).write(
        vault.vault_path / "T6.2 Using LLM concepts.md"
    )

    ObsidianNote(".", fm={"tags": ["concept"], "aliases": ["LLM"]}).write(
        vault.vault_path / "Large Language Model.md"
    )

    linker = ObsidianAutoLinker()
    linker.add_notes(vault.query().with_tag("concept"))
    linker.add_notes(vault.query().with_tag("task"))

    text = "This is a test for T6.2, which is T6.2 Using LLM concepts."
    assert (
        linker.run(text)
        == "This is a test for [[T6.2 Using LLM concepts|T6.2]], which is [[T6.2 Using LLM concepts|T6.2]] Using [[Large Language Model|LLM]] concepts."
    )


def test_single_note_extra_delimiter(tmp_path):
    vault = ObsidianVault(tmp_path)

    ObsidianNote(".", fm={"tags": ["task"], "aliases": ["T1.2"]}).write(
        vault.vault_path / "T1.2 test Task.md"
    )
    text = "This is a test for T1.2 and T1.2.4"

    linker = ObsidianAutoLinker()
    linker.add_notes(vault.query().with_tag("task"))
    assert (
        linker.run(text)
        == "This is a test for [[T1.2 test Task|T1.2]] and [[T1.2 test Task|T1.2]].4"
    )  # This is not what I want

    linker = ObsidianAutoLinker()
    linker.add_notes(vault.query().with_tag("task"), extra_word_chars=".")
    assert linker.run(text) == "This is a test for [[T1.2 test Task|T1.2]] and T1.2.4"


def test_single_note_allowed_prefixes(tmp_path):
    vault = ObsidianVault(tmp_path)

    ObsidianNote(".", fm={"tags": ["task"], "aliases": ["T1.2"]}).write(
        vault.vault_path / "T1.2 test Task.md"
    )
    text = "This is a test for _T1.2"

    linker = ObsidianAutoLinker()
    linker.add_notes(vault.query().with_tag("task"))
    assert linker.run(text) == "This is a test for _T1.2"  # This is not what I want

    linker = ObsidianAutoLinker()
    linker.add_notes(vault.query().with_tag("task"), allowed_prefixes="_")
    assert linker.run(text) == "This is a test for _[[T1.2 test Task|T1.2]]"


def test_single_note_allowed_suffixes(tmp_path):
    vault = ObsidianVault(tmp_path)

    ObsidianNote(".", fm={"tags": ["concept"], "aliases": ["LLM"]}).write(
        vault.vault_path / "Large Language Model.md"
    )
    text = "We are gonna talk about LLMs"

    linker = ObsidianAutoLinker()
    linker.add_notes(vault.query().with_tag("concept"))
    assert linker.run(text) == "We are gonna talk about LLMs"  # This is not what I want

    linker = ObsidianAutoLinker()
    linker.add_notes(vault.query().with_tag("concept"), allowed_suffixes="s")
    assert linker.run(text) == "We are gonna talk about [[Large Language Model|LLM]]s"


def test_word_chars_none(tmp_path):
    vault = ObsidianVault(tmp_path)

    ObsidianNote(".", fm={"tags": ["concept"], "aliases": ["LLM"]}).write(
        vault.vault_path / "Large Language Model.md"
    )

    linker = ObsidianAutoLinker()
    linker.add_notes(vault.query().with_tag("concept"))

    text = "I want to use multiple Large Language Models (LLM) in my word."
    assert (
        linker.run(text)
        == "I want to use multiple Large Language Models ([[Large Language Model|LLM]]) in my word."
    )

    linker = ObsidianAutoLinker()
    linker.add_notes(vault.query().with_tag("concept"), whole_words=False)

    text = "I want to use multiple Large Language Models (LLM) in my word."
    assert (
        linker.run(text)
        == "I want to use multiple [[Large Language Model]]s ([[Large Language Model|LLM]]) in my word."
    )


def test_sort_by_key_length(tmp_path):
    vault = ObsidianVault(tmp_path)

    ObsidianNote(".", fm={"tags": ["concept"], "aliases": ["LLM"]}).write(
        vault.vault_path / "Large Language Model.md"
    )

    ObsidianNote(".", fm={"tags": ["task"], "aliases": ["T6.2"]}).write(
        vault.vault_path / "T6.2 Using LLM concepts.md"
    )

    linker = ObsidianAutoLinker()

    # If I first add the concepts and then the tasks...
    linker.add_notes(vault.query().with_tag("concept"))
    linker.add_notes(vault.query().with_tag("task"))

    text = "This is a summary about task T6.2 Using LLM concepts."

    # default behaviour is to follow order of insertion, so the concept is linked first
    # this gives two different links
    assert (
        linker.run(text)
        == "This is a summary about task [[T6.2 Using LLM concepts|T6.2]] Using [[Large Language Model|LLM]] concepts."
    )

    # setting sort_by_key_length to True will sort the rules by the length of the key
    # , so the longer key is linked first
    linker.sort_by_key_length()
    assert (
        linker.run(text) == "This is a summary about task [[T6.2 Using LLM concepts]]."
    )


def test_auto_sort_by_key_length(tmp_path):
    vault = ObsidianVault(tmp_path)

    ObsidianNote(".", fm={"tags": ["concept"], "aliases": ["LLM"]}).write(
        vault.vault_path / "Large Language Model.md"
    )

    ObsidianNote(".", fm={"tags": ["task"], "aliases": ["T6.2"]}).write(
        vault.vault_path / "T6.2 Using LLM concepts.md"
    )

    linker = ObsidianAutoLinker(auto_sort_by_key_length=True)

    # If I first add the concepts and then the tasks...
    linker.add_notes(vault.query().with_tag("concept"))
    linker.add_notes(vault.query().with_tag("task"))

    text = "This is a summary about task T6.2 Using LLM concepts."

    assert (
        linker.run(text) == "This is a summary about task [[T6.2 Using LLM concepts]]."
    )


def test_linker_note_with_block():

    note = ObsidianNote(
        "./Large Language Model.md", fm={"tags": ["concept"], "aliases": ["LLM"]}
    )

    linker = ObsidianAutoLinker()

    for trigger, link in note.to_links().items():
        linker.add_link(trigger, link)

    note = ObsidianNote(
        "./test.md",
        body="""This is a note about Large Language Models.
```python
def LLM():
    pass
```
This is more text about LLM.
""",
    )

    # Undesired behaviour: the LLM in the code block is linked, which is not what we want
    assert (
        linker.run(note.body)
        == """This is a note about Large Language Models.
```python
def [[Large Language Model|LLM]]():
    pass
```
This is more text about [[Large Language Model|LLM]].
"""
    )

    # When input is a note, however, it gives back an autolinked copy of the note
    # only text outside of blocks is autolinked
    assert (
        linker.run(note).body
        == """This is a note about Large Language Models.
```python
def LLM():
    pass
```
This is more text about [[Large Language Model|LLM]].
"""
    )


def test_url_link():

    note_llm = ObsidianNote(
        "./Large Language Model.md",
        fm={"tags": ["concept"], "aliases": ["LLM"]},
    )

    note_wp3 = ObsidianNote(
        "./WP3 Testing.md",
        fm={"tags": ["concept"], "aliases": ["WP3"]},
    )

    linker = ObsidianAutoLinker()

    for note in [note_llm, note_wp3]:
        for trigger, link in note.to_links().items():
            linker.add_link(trigger, link)

    text = "This is a summary about task LLM concepts, you can read more about it on [My blog about LLM right now](my.llm.blog)."

    assert (
        linker.run(text)
        == "This is a summary about task [[Large Language Model|LLM]] concepts, you can read more about it on [My blog about LLM right now](my.llm.blog)."
    )

    text_italic_broken = "_This is a summary about task LLM concepts, you can read more about it on (_[My blog about LLM right now](my.llm.blog)_)._."

    assert (
        linker.run(text_italic_broken)
        == "_This is a summary about task [[Large Language Model|LLM]] concepts, you can read more about it on (_[My blog about LLM right now](my.llm.blog)_)._."
    )

    text_url_has_text_with_spaces = "This is a summary about task LLM concepts, you can read more about it on [My blog about LLM right now](my.llm.blog.protected Original URL: https://my.llm.blog Click or tap if you trust this link.)"

    assert (
        linker.run(text_url_has_text_with_spaces)
        == "This is a summary about task [[Large Language Model|LLM]] concepts, you can read more about it on [My blog about LLM right now](my.llm.blog.protected Original URL: https://my.llm.blog Click or tap if you trust this link.)"
    )


def test_equation():

    note = ObsidianNote(
        "./Value function.md", fm={"tags": ["concept"], "aliases": ["value"]}
    )

    linker = ObsidianAutoLinker()

    for trigger, link in note.to_links().items():
        linker.add_link(trigger, link)

    # Wrong inline math region, gets linked
    assert (
        linker.run(
            "Define a Value function  f_{\\text{value}}: \\mathbb{N} \\to \\mathbb{R}$."
        )
        == "Define a [[Value function]]  f_{\\text{[[Value function|value]]}}: \\mathbb{N} \\to \\mathbb{R}$."
    )

    # Correct inline math region is protected
    assert (
        linker.run(
            "Define a Value function $f_{\\text{value}}: \\mathbb{N} \\to \\mathbb{R}$."
        )
        == "Define a [[Value function]] $f_{\\text{value}}: \\mathbb{N} \\to \\mathbb{R}$."
    )

    # Wrong full math region, gets linked
    assert (
        linker.run(
            "Define a Value function  f_{\\text{value}}: \\mathbb{N} \\to \\mathbb{R}$$."
        )
        == "Define a [[Value function]]  f_{\\text{[[Value function|value]]}}: \\mathbb{N} \\to \\mathbb{R}$$."
    )

    # Correct multiple math regions are protected
    assert (
        linker.run(
            "Define a Value function $$f_{\\text{value}}: \\mathbb{N} \\to \\mathbb{R}$$. Let's see some properties of $ f_{\\text{value}}$:"
        )
        == "Define a [[Value function]] $$f_{\\text{value}}: \\mathbb{N} \\to \\mathbb{R}$$. Let's see some properties of $ f_{\\text{value}}$:"
    )
