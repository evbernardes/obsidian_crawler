# Obsidian Crawler

A lightweight Python library for reading, querying and modifying notes in Obsidian vaults.

## Installation

```bash
git clone https://github.com/evbernardes/obsidian-crawler.git
cd obsidian-crawler
pip install -e .
```

## Basic usage

```python
from obsidian_crawler import ObsidianVault

vault = ObsidianVault("~/Obsidian")
```

### Querying

```python
tasks = (
    vault.query()
         .with_tag("task")
         .sort(key=lambda n: n.fm.get("code"))
         .all()
)
```

### Indexing

```python
tasks = (
    vault.query()
         .with_tag("task")
         .index_by("code")
)
```

### Grouping

```python
tasks = (
    vault.query()
         .with_tag("task")
         .group_by_many("capability")
)
```

### Writing

```python
note = vault.read_note("Tasks/T001.md")
note.fm["lead"] = "Alice"
note.write()
```

This project is licensed under the GNU General Public License v3.0.
See [LICENSE](LICENSE) for details.
