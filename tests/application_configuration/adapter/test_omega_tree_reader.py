import pytest
from omegaconf.errors import InterpolationResolutionError

from pycraftcore.application_configuration.adapter import OmegaTreeReader


def write(path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_the_root_file_is_read_under_its_key(tmp_path):
    root = write(tmp_path / "agent.yml", "agent:\n  name: chat\n  turns: [direct]\n")

    assert OmegaTreeReader(root).read("agent") == {"name": "chat", "turns": ["direct"]}


def test_the_folders_are_merged_and_the_root_refers_to_them(tmp_path):
    root = write(tmp_path / "agent.yml", "agent:\n  name: chat\n  skills: ${skills}\n")
    write(tmp_path / "skills" / "b.yml", "skills:\n  answer: {id: answer}\n")
    write(tmp_path / "skills" / "a.yml", "skills:\n  explain: {id: explain}\n")

    tree = OmegaTreeReader(root, [tmp_path / "skills"]).read("agent")

    assert tree["skills"] == {"answer": {"id": "answer"}, "explain": {"id": "explain"}}


def test_the_root_file_wins_over_a_folder(tmp_path):
    root = write(tmp_path / "agent.yml", "agent:\n  name: root\n")
    write(tmp_path / "extra" / "x.yml", "agent:\n  name: folder\n  kept: true\n")

    assert OmegaTreeReader(root, [tmp_path / "extra"]).read("agent") == {
        "name": "root",
        "kept": True,
    }


def test_environment_variables_are_resolved(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_NAME", "observation")
    root = write(tmp_path / "agent.yml", "agent:\n  name: ${oc.env:AGENT_NAME}\n")

    assert OmegaTreeReader(root).read("agent") == {"name": "observation"}


def test_a_missing_environment_variable_fails(tmp_path, monkeypatch):
    monkeypatch.delenv("NOT_SET_ANYWHERE", raising=False)
    root = write(tmp_path / "agent.yml", "agent:\n  name: ${oc.env:NOT_SET_ANYWHERE}\n")

    with pytest.raises(InterpolationResolutionError):
        OmegaTreeReader(root).read("agent")


def test_a_missing_folder_is_no_files(tmp_path):
    root = write(tmp_path / "agent.yml", "agent:\n  name: chat\n")

    assert OmegaTreeReader(root, [tmp_path / "nowhere"]).read("agent") == {"name": "chat"}


def test_a_missing_root_file_is_named(tmp_path):
    with pytest.raises(FileNotFoundError, match="agent.yml"):
        OmegaTreeReader(tmp_path / "agent.yml").read("agent")


def test_a_missing_key_is_named(tmp_path):
    root = write(tmp_path / "agent.yml", "other: {}\n")

    with pytest.raises(KeyError, match="no 'agent' section"):
        OmegaTreeReader(root).read("agent")


def test_a_key_that_is_not_a_mapping_is_refused(tmp_path):
    root = write(tmp_path / "agent.yml", "agent: chat\n")

    with pytest.raises(ValueError, match="must be a mapping"):
        OmegaTreeReader(root).read("agent")
