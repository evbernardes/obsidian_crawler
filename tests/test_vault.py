from pathlib import Path

import pytest

from obsidian_crawler import ObsidianVault

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def create_note(path: Path, title: str, **fm):
    path.mkdir(parents=True, exist_ok=True)

    note = path / f"{title}.md"

    frontmatter = "\n".join(f"{k}: {v}" for k, v in fm.items())

    note.write_text(
        f"---\n{frontmatter}\n---\n\nBody",
        encoding="utf-8",
    )

    return note


# ---------------------------------------------------------
# Loading
# ---------------------------------------------------------


def test_load(tmp_path):
    create_note(tmp_path, "A")
    create_note(tmp_path, "B")

    vault = ObsidianVault(tmp_path)

    notes = list(vault.notes())

    assert len(notes) == 2


def test_read_note(tmp_path):
    create_note(tmp_path, "Task")

    vault = ObsidianVault(tmp_path)

    note = vault.read_note("Task.md")

    assert note.title == "Task"


# ---------------------------------------------------------
# Query
# ---------------------------------------------------------


def test_query(tmp_path):
    create_note(tmp_path, "A", tags=["task"])
    create_note(tmp_path, "B", tags=["capability"])

    vault = ObsidianVault(tmp_path)

    tasks = vault.query().with_tag("task").all()

    assert len(tasks) == 1
    assert tasks[0].title == "A"


# ---------------------------------------------------------
# Cache
# ---------------------------------------------------------


def test_read_returns_same_object_when_cached(tmp_path):
    create_note(tmp_path, "Task")

    vault = ObsidianVault(tmp_path).load()

    a = vault.read_note("Task.md")
    b = vault.read_note("Task.md")

    assert a is b


def test_refresh_creates_new_objects(tmp_path):
    create_note(tmp_path, "Task")

    vault = ObsidianVault(tmp_path).load()

    first = vault.read_note("Task.md")

    vault.refresh()

    second = vault.read_note("Task.md")

    assert first is not second


def test_modifying_cached_note_is_visible_everywhere(tmp_path):
    create_note(tmp_path, "Task")

    vault = ObsidianVault(tmp_path).load()

    a = vault.read_note("Task.md")
    b = vault.resolve_link("Task")

    a.fm["status"] = "done"

    assert b.fm["status"] == "done"


# ---------------------------------------------------------
# Move
# ---------------------------------------------------------


def test_move(tmp_path):
    create_note(tmp_path, "Task")

    vault = ObsidianVault(tmp_path).load()

    note = vault.read_note("Task.md")

    vault.move(note, "Folder/Task.md")

    assert (tmp_path / "Folder" / "Task.md").exists()
    assert not (tmp_path / "Task.md").exists()

    loaded = vault.read_note("Folder/Task.md")

    assert loaded is note


# ---------------------------------------------------------
# Rename
# ---------------------------------------------------------


def test_rename(tmp_path):
    create_note(tmp_path, "Task")

    vault = ObsidianVault(tmp_path).load()

    note = vault.read_note("Task.md")

    vault.rename(note, "NewTask")

    assert (tmp_path / "NewTask.md").exists()
    assert note.title == "NewTask"


# ---------------------------------------------------------
# Delete
# ---------------------------------------------------------


def test_delete(tmp_path):
    create_note(tmp_path, "Task")

    vault = ObsidianVault(tmp_path).load()

    note = vault.read_note("Task.md")

    vault.delete(note)

    assert not (tmp_path / "Task.md").exists()


# ---------------------------------------------------------
# Resolve
# ---------------------------------------------------------


def test_resolve(tmp_path):
    create_note(tmp_path, "Task")

    vault = ObsidianVault(tmp_path)

    note = vault.resolve_link("Task")

    assert note is not None
    assert note.title == "Task"


def test_resolve_unknown_returns_none(tmp_path):
    vault = ObsidianVault(tmp_path)

    assert vault.resolve_link("Missing") is None


# ---------------------------------------------------------
# Duplicate titles
# ---------------------------------------------------------


def test_duplicate_titles_warning(tmp_path):
    create_note(tmp_path, "Task")

    folder = tmp_path / "Other"
    create_note(folder, "Task")

    vault = ObsidianVault(tmp_path)

    with pytest.warns(RuntimeWarning):
        vault.resolve_link("Task")


# ---------------------------------------------------------
# Update
# ---------------------------------------------------------


def test_update_detects_new_note(tmp_path):
    create_note(tmp_path, "A")

    vault = ObsidianVault(tmp_path).load()

    create_note(tmp_path, "B")

    vault.update()

    assert vault.resolve_link("B") is not None


def test_update_detects_deleted_note(tmp_path):
    create_note(tmp_path, "A")

    vault = ObsidianVault(tmp_path).load()

    (tmp_path / "A.md").unlink()

    vault.update()

    assert vault.resolve_link("A") is None


def test_update_detects_modified_note(tmp_path):
    create_note(tmp_path, "Task", status="old")

    vault = ObsidianVault(tmp_path).load()

    (tmp_path / "Task.md").write_text("---\nstatus: new\n---\n\nBody")

    vault.update()

    note = vault.resolve_link("Task")

    assert note.fm["status"] == "new"
