#!/usr/bin/env python3
from obsidian_crawler.section import ObsidianDocument, ObsidianSection


def _round_trip(text: str, section_number: None | int = None):
    doc = ObsidianDocument.from_text(text)
    if section_number is None:
        return doc.to_markdown()
    return doc.sections[section_number].to_markdown()


def test_empty_document():
    document = ObsidianDocument.from_text("")

    assert document.preamble == ""
    assert document.sections == []
    assert document.to_markdown() == ""


def test_document_without_sections():
    text = "Just some text.\n\nAnd some more text.\n"

    document = ObsidianDocument.from_text(text)

    assert document.preamble == text
    assert document.sections == []
    assert document.to_markdown() == text


def test_single_section():
    text = "# Introduction\n\nHello world.\n"

    document = ObsidianDocument.from_text(text)

    assert len(document.sections) == 1

    section = document.sections[0]

    assert section.title == "Introduction"
    assert section.level == 1
    assert (
        section.content == "\nHello world.\n"
    )  # Only one extra space, the first one is already the header separation
    assert section.parent is None

    assert document.to_markdown() == text
    assert section.to_markdown() == text


def test_preamble_is_preserved():
    text = "Some introductory text.\n\nAnother paragraph.\n\n# Introduction\n\nHello.\n"

    document = ObsidianDocument.from_text(text)

    assert document.preamble == ("Some introductory text.\n\nAnother paragraph.\n")

    assert document.to_markdown() == text


def test_multiple_top_level_sections():
    text = "# First\n\nFirst content.\n\n# Second\n\nSecond content.\n"

    document = ObsidianDocument.from_text(text)

    assert len(document.sections) == 2

    assert document.sections[0].title == "First"
    assert document.sections[0].level == 1
    assert document.sections[0].content == "\nFirst content.\n"

    assert document.sections[1].title == "Second"
    assert document.sections[1].level == 1
    assert document.sections[1].content == "\nSecond content.\n"

    assert document.to_markdown() == text


def test_nested_sections():
    text = (
        "# Introduction\n"
        "\n"
        "Introduction content.\n"
        "\n"
        "## Background\n"
        "\n"
        "Background content.\n"
        "\n"
        "### History\n"
        "\n"
        "History content.\n"
        "\n"
        "## Goals\n"
        "\n"
        "Goals content.\n"
        "\n"
        "# Conclusion\n"
        "\n"
        "Conclusion content.\n"
    )

    document = ObsidianDocument.from_text(text)

    introduction = document.sections[0]
    conclusion = document.sections[1]

    assert introduction.title == "Introduction"
    assert conclusion.title == "Conclusion"

    assert len(introduction.children) == 2

    background = introduction.children[0]
    goals = introduction.children[1]

    assert background.title == "Background"
    assert background.level == 2
    assert background.parent is introduction

    assert len(background.children) == 1

    history = background.children[0]

    assert history.title == "History"
    assert history.level == 3
    assert history.parent is background

    assert goals.title == "Goals"
    assert goals.level == 2
    assert goals.parent is introduction

    assert document.to_markdown() == text


def test_section_content_preserves_whitespace():
    text = (
        "# Section  \n"
        "\n"
        "\n"
        "  Some content.  \n"
        "\n"
        "    Indented content.\n"
        "\n"
        "\n"
        "## Child\n"
        "\n"
        "Child content.\n"
    )

    document = ObsidianDocument.from_text(text)

    section = document.sections[0]

    assert section.title == "Section  "
    assert section.content == ("\n\n  Some content.  \n\n    Indented content.\n\n")
    assert document.to_markdown() == text


def test_header_whitespace_is_preserved():
    text = "#   Introduction   \n\nHello.\n\n## \tBackground\t\n\nDetails.\n"

    document = ObsidianDocument.from_text(text)

    assert document.sections[0].title == "  Introduction   "
    assert document.sections[0].children[0].title == "\tBackground\t"

    assert document.to_markdown() == text


def test_header_title_cannot_start_with_tab():
    text = "#\tIntroduction"

    document = ObsidianDocument.from_text(text)

    assert len(document.sections) == 0

    assert document.to_markdown() == text


def test_section_reconstruction_without_children():
    text = (
        "# Introduction\n"
        "\n"
        "Introduction content.\n"
        "\n"
        "## Background\n"
        "\n"
        "Background content.\n"
        "\n"
        "## Goals\n"
        "\n"
        "Goals content.\n"
    )

    document = ObsidianDocument.from_text(text)
    introduction = document.sections[0]

    own = introduction.to_markdown(include_children=False)

    assert own == ("# Introduction\n\nIntroduction content.\n")


def test_leaf_section_reconstruction():
    text = "# Introduction\n\nIntro.\n\n## Background\n\nBackground.\n"

    document = ObsidianDocument.from_text(text)

    background = document.sections[0].children[0]

    assert background.to_markdown() == ("## Background\n\nBackground.\n")

    assert background.to_markdown(include_children=False) == (
        "## Background\n\nBackground.\n"
    )


def test_find():
    text = "# Introduction\n\n## Background\n\n### History\n\n# Conclusion\n"

    document = ObsidianDocument.from_text(text)

    assert document.find("Introduction") is document.sections[0]
    assert document.find("Background") is document.sections[0].children[0]

    history = document.find("History")

    assert history is not None
    assert history.level == 3

    assert document.find("History", level=2) is None
    assert document.find("History", level=3) is history


def test_section_find():
    text = "# Introduction\n\n## Background\n\n### History\n"

    document = ObsidianDocument.from_text(text)

    introduction = document.find("Introduction")
    assert introduction is not None

    assert introduction.find("Background") is introduction.children[0]
    assert introduction.find("History") is introduction.children[0].children[0]


def test_duplicate_titles():
    text = "# Introduction\n\nFirst.\n\n# Introduction\n\nSecond.\n"

    document = ObsidianDocument.from_text(text)

    first = document.find("Introduction")

    assert first is document.sections[0]
    assert first.content == "\nFirst.\n"


# def test_exact_round_trip_with_no_trailing_newline():
#     text = "Preamble\n\n# Introduction\n\nContent\n\n## Details\n\nMore content"

#     document = ObsidianDocument.from_text(text)

#     assert document.to_markdown() == text


def test_exact_round_trip_with_multiple_trailing_newlines():
    text = "# Introduction\n\nContent\n\n\n\n"

    document = ObsidianDocument.from_text(text)

    assert document.to_markdown() == text


def test_exact_round_trip_with_no_content():
    text = "# Empty section"

    document = ObsidianDocument.from_text(text)

    section = document.sections[0]

    assert document.preamble == ""
    assert section.title == "Empty section"
    assert section.content == ""

    assert document.to_markdown() == text


def test_level_jump():

    text = (
        ""
        + "# Introduction\nBla\n"
        + "## Background\nBlabla\n"
        + "#### Detail\n\nDetails.\n"
    )

    document = ObsidianDocument.from_text(text)

    introduction = document.sections[0]
    assert introduction.level == 1
    assert introduction.title == "Introduction"
    assert introduction.content == "Bla"
    assert introduction.to_markdown(include_children=False) == "# Introduction\nBla"

    background = introduction.children[0]
    assert background.level == 2
    assert background.title == "Background"
    assert background.content == "Blabla"
    assert background.to_markdown(include_children=False) == "## Background\nBlabla"

    assert introduction.to_markdown(
        include_children=False
    ) + "\n" + background.to_markdown(
        include_children=True
    ) == introduction.to_markdown(include_children=True)

    detail = background.children[0]
    assert detail.level == 4
    assert detail.title == "Detail"
    assert detail.content == "\nDetails.\n"
    assert detail.to_markdown() == "#### Detail\n\nDetails.\n"

    assert background.to_markdown(include_children=False) + "\n" + detail.to_markdown(
        include_children=False
    ) == background.to_markdown(include_children=True)

    assert detail.parent is background

    assert document.to_markdown() == text


def test_level_jump_empty_section():

    text = (
        ""
        + "# Introduction\n\n"
        + "## Background\nBlabla\n"
        + "#### Detail\nDetails.\n"
    )

    document = ObsidianDocument.from_text(text)

    introduction = document.sections[0]
    background = introduction.children[0]

    assert introduction.title == "Introduction"
    assert background.title == "Background"

    assert introduction.content == ""
    assert background.content == "Blabla"

    assert document.to_markdown() == text


def test_manual_creation():

    section1_dict = {
        "title": "Top header" + "  ",  # Two trailing spaces after 'Top header'
        "level": 1,
        "content": "\nTesting header. \n\nTesting lines.\n\n\n\n\n",  # There is a trailing space after 'Testing header.'
    }
    section1_full = """# Top header  

Testing header. 

Testing lines.




"""
    section1 = ObsidianSection(**section1_dict)
    assert section1.to_markdown() == section1_full
    assert _round_trip(section1_full, 0) == section1_full

    section2_dict = {
        "title": "Sub header",
        "level": 2,
        "content": "\n\n\n\nContent. \n\nHere we have:\n- One\n- Two\n- Three\n",  # There is a trailing space after 'Content.'
    }
    section2_full = """## Sub header




Content. 

Here we have:
- One
- Two
- Three
"""

    section2 = ObsidianSection(**section2_dict)
    assert section2.to_markdown() == section2_full
    assert _round_trip(section2_full, 0) == section2_full

    doc = ObsidianDocument("", sections=[section1, section2])
    doc_full = """# Top header  

Testing header. 

Testing lines.





## Sub header




Content. 

Here we have:
- One
- Two
- Three
"""

    assert doc.to_markdown() == doc_full
