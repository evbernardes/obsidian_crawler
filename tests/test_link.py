from obsidian_crawler.note import ObsidianNote

# from obsidian_crawler.link import ObsidianLink


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
