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


def test_single_note(tmp_path):
    vault = ObsidianVault(tmp_path)

    ObsidianNote(".", fm={"tags": ["task"], "aliases": ["T1.2"]}).write(
        vault.vault_path / "T1.2 test Task.md"
    )

    linker = ObsidianAutoLinker()
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


def test_two_notes(tmp_path):
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

    linker = ObsidianAutoLinker()
    linker.add_notes(vault.query().with_tag("task"))

    # This is not what I want
    text = "This is a test for T1.2 and T1.2.4"
    assert (
        linker.run(text)
        == "This is a test for [[T1.2 test Task|T1.2]] and [[T1.2 test Task|T1.2]].4"
    )

    linker = ObsidianAutoLinker()
    linker.add_notes(vault.query().with_tag("task"), extra_word_chars=".")

    # This is not what I want
    text = "This is a test for T1.2 and T1.2.4"
    assert linker.run(text) == "This is a test for [[T1.2 test Task|T1.2]] and T1.2.4"


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


def test_linker_note_with_block(tmp_path):
    vault = ObsidianVault(tmp_path)

    ObsidianNote(".", fm={"tags": ["concept"], "aliases": ["LLM"]}).write(
        vault.vault_path / "Large Language Model.md",
    )

    linker = ObsidianAutoLinker()
    linker.add_notes(vault.query().with_tag("concept"))

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
