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
