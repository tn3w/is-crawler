from pathlib import Path

from is_crawler import __version__


def test_version():
    assert isinstance(__version__, str)


def test_version_falls_back_when_package_metadata_is_missing(monkeypatch):
    import importlib
    import importlib.metadata

    import is_crawler as mod

    real_version = importlib.metadata.version

    def fake_version(name: str) -> str:
        if name == "is-crawler":
            raise importlib.metadata.PackageNotFoundError
        return real_version(name)

    monkeypatch.setattr(importlib.metadata, "version", fake_version)
    reloaded = importlib.reload(mod)

    try:
        assert reloaded.__version__ == "0+unknown"
    finally:
        monkeypatch.setattr(importlib.metadata, "version", real_version)
        importlib.reload(reloaded)


def test_all_exports():
    import is_crawler as mod

    assert set(mod.__all__) == {
        "is_crawler",
        "crawler_name",
        "crawler_version",
        "crawler_url",
        "crawler_signals",
        "crawler_info",
        "crawler_has_tag",
        "is_search_engine",
        "is_ai_crawler",
        "is_seo",
        "is_social_preview",
        "is_advertising",
        "is_archiver",
        "is_feed_reader",
        "is_monitoring",
        "is_scanner",
        "is_academic",
        "is_http_library",
        "is_browser_automation",
        "is_good_crawler",
        "is_bad_crawler",
        "iter_crawlers",
        "robots_agents_for_tags",
        "build_robots_txt",
        "build_ai_txt",
        "assert_crawler",
        "crawler_contact",
        "CrawlerInfo",
        "__version__",
    }


def test_unknown_attribute_raises():
    import pytest

    import is_crawler as mod

    with pytest.raises(AttributeError):
        mod.does_not_exist


def test_regex_usage_restricted_to_database():
    import ast

    package_dir = Path(__file__).parent.parent / "is_crawler"
    blocked = {"re", "regex"}

    for path in package_dir.glob("*.py"):
        module = path.name
        source = path.read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if module != "database.py":
                        assert root not in blocked, f"{module} imports {root}"
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".")[0]
                if module != "database.py":
                    assert root not in blocked, f"{module} imports {root}"
