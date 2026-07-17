from pathlib import Path

import pytest

from obsidian_crawler.note import ObsidianNote


def test_create_note():

    note = ObsidianNote(
        path="test.md",
        fm={
            "tags": ["task", "test"],
            "status": "ready",
        },
        body="Hello",
    )

    assert note.path == Path("test.md")
    assert note.fm == {
        "tags": ["task", "test"],
        "status": "ready",
    }
    assert note.body == "Hello"


def test_modified_flag():
    note = ObsidianNote(
        path="test.md",
        fm={},
        body="Hello",
    )

    assert not note.modified

    note.body = "Changed"

    assert note.modified


def test_reset_restores_original():
    note = ObsidianNote(
        path="test.md",
        fm={"a": 1},
        body="Hello",
    )

    note.fm["a"] = 2
    note.body = "Changed"

    assert note.modified

    note.reset()

    assert note.fm == {"a": 1}
    assert note.body == "Hello"
    assert not note.modified


def test_path_is_always_path():
    note = ObsidianNote(
        path="test.md",
        fm={},
        body="",
    )

    assert isinstance(note.path, Path)

    note.path = "other.md"

    assert isinstance(note.path, Path)
    assert note.path == Path("other.md")


def test_fm_must_be_dict():
    note = ObsidianNote(
        path="test.md",
        fm={},
        body="",
    )

    with pytest.raises(TypeError):
        note.fm = []


def test_reset_restores_nested_fm():
    note = ObsidianNote(
        "note.md",
        fm={"tags": ["a", "b"]},
    )

    note.fm["tags"].append("c")

    assert note.modified

    note.reset()

    assert note.fm == {"tags": ["a", "b"]}


def test_body_must_be_string():
    note = ObsidianNote(
        path="test.md",
        fm={},
        body="",
    )

    with pytest.raises(TypeError):
        note.body = 123


def test_as_json():
    note = ObsidianNote(
        path="test.md",
        fm={"a": 1},
        body="Hello",
    )

    assert note.as_json == {
        "path": "test.md",
        "fm": {"a": 1},
        "body": "Hello",
    }


def test_links():
    note = ObsidianNote(
        path="test.md",
        body="See [[Task]] and [[Other|Alias]].",
    )

    links = note.links

    assert len(links) == 2

    assert links[0].target == "Task"
    assert links[0].alias is None

    assert links[1].target == "Other"
    assert links[1].alias == "Alias"


# ---------------------------------------------------------
# Properties
# ---------------------------------------------------------


def test_tags_property():
    note = ObsidianNote(
        path="test.md",
        fm={
            "tags": ["task", "python"],
            "status": "ready",
        },
        body="",
    )

    assert note.tags == ["task", "python"]


def test_tags_defaults_to_empty():
    note = ObsidianNote("note.md")

    assert note.tags == []


def test_title():
    note = ObsidianNote("/tmp/My Note.md")

    assert note.title == "My Note"


def test_repr():
    note = ObsidianNote("Example.md")

    assert "Example" in repr(note)


# ---------------------------------------------------------
# I/O
# ---------------------------------------------------------


def test_write_read(tmp_path):
    path = tmp_path / "note.md"

    note = ObsidianNote(
        path=path,
        fm={"tags": ["task"]},
        body="Hello",
    )

    assert note.write()
    assert path.exists()
    loaded = ObsidianNote.from_file(path)

    assert loaded.fm == note.fm
    assert loaded.body == note.body
    assert not loaded.modified

    path2 = tmp_path / "note2.md"
    assert note.write(path2)
    assert path.exists()

    loaded2 = ObsidianNote.from_file(path2)
    assert loaded2.fm == note.fm
    assert loaded2.body == note.body

    assert path != path2


def test_write_updates_modified_flag(tmp_path):
    path = tmp_path / "note.md"

    note = ObsidianNote(
        path=path,
        fm={},
        body="Hello",
    )

    note.write()

    note.body = "Changed"

    assert note.modified

    note.write()

    assert not note.modified


def test_from_file_without_frontmatter(tmp_path):
    path = tmp_path / "note.md"
    path.write_text("Just some text")

    note = ObsidianNote.from_file(path)

    assert note.fm == {}
    assert note.body == "Just some text"


def test_preserve_spacing_after_frontmatter(tmp_path):
    path = tmp_path / "note.md"

    path.write_text("---\na: 1\n---\n\n\nBody")
    note = ObsidianNote.from_file(path)

    assert note.body == "\n\nBody"
