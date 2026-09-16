from pathlib import Path

from music_sync import __version__


def test_release_version_is_1_0_0():
    assert __version__ == "1.0.0"


def test_windows_version_resource_matches_package_version():
    resource = Path("build/windows_version.txt").read_text(encoding="utf-8")
    major, minor, patch = (int(part) for part in __version__.split("."))
    assert f"filevers=({major}, {minor}, {patch}, 0)" in resource
    assert f"prodvers=({major}, {minor}, {patch}, 0)" in resource
    assert f"FileVersion', '{major}.{minor}.{patch}.0'" in resource
    assert f"ProductVersion', '{major}.{minor}.{patch}.0'" in resource


def test_packaging_files_have_no_developer_paths():
    spec = Path("music_sync.spec").read_text(encoding="utf-8")
    workflow = Path(".github/workflows/build-windows.yml").read_text(encoding="utf-8")
    assert "E:\\Ava files" not in spec
    assert "E:\\Ava files" not in workflow
    assert "Ava files" not in spec
