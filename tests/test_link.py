from obsidian_crawler.link import ObsidianLink
from obsidian_crawler.note import ObsidianNote


def test_links_with_heading_and_block():
    note = ObsidianNote(
        "note.md",
        body="""
[[Task]]
[[Other|Alias]]
[[Capability#Heading]]
[[Reference^block]]
""",
    )

    links = note.links

    assert links[0].target == "Task"

    assert links[1].target == "Other"
    assert links[1].alias == "Alias"

    assert links[2].target == "Capability"
    assert links[2].heading == "Heading"

    assert links[3].target == "Reference"
    assert links[3].block == "block"


def test_simple():
    link = ObsidianLink("Task")

    assert link.to_markdown() == "[[Task]]"
    assert link.render() == "Task"


def test_alias():
    link = ObsidianLink(
        target="Task",
        alias="My Task",
    )

    assert link.to_markdown() == "[[Task|My Task]]"
    assert link.render() == "My Task"
    assert ObsidianLink.parse(link.to_markdown())[0] == link


def test_heading():
    link = ObsidianLink(
        target="Task",
        heading="Introduction",
    )

    assert link.to_markdown() == "[[Task#Introduction]]"
    assert link.render() == "Task#Introduction"
    assert ObsidianLink.parse(link.to_markdown())[0] == link


def test_block():
    link = ObsidianLink(
        target="Task",
        block="abc123",
    )

    assert link.to_markdown() == "[[Task^abc123]]"
    assert link.render() == "Task^abc123"
    assert ObsidianLink.parse(link.to_markdown())[0] == link


def test_heading_alias():
    link = ObsidianLink(
        target="Task",
        heading="Introduction",
        alias="Intro",
    )

    assert link.to_markdown() == "[[Task#Introduction|Intro]]"
    assert link.render() == "Intro"
    assert ObsidianLink.parse(link.to_markdown())[0] == link


def test_heading_block_alias():
    link = ObsidianLink(
        target="Task",
        heading="Introduction",
        block="123",
        alias="Intro",
    )

    assert link.to_markdown() == "[[Task#Introduction^123|Intro]]"
    assert link.render() == "Intro"
    assert ObsidianLink.parse(link.to_markdown())[0] == link


def test_parse_links():
    links = ObsidianLink.parse("See [[Task]], [[Other#Section]] and [[Third|Alias]].")

    assert links == [
        ObsidianLink("Task"),
        ObsidianLink("Other", heading="Section"),
        ObsidianLink("Third", alias="Alias"),
    ]
