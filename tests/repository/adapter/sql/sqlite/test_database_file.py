from pycraftcore.repository.adapter.sql.sqlite import SqliteDatabaseFile


def test_the_file_is_named_after_the_database_in_its_directory(tmp_path):
    database = SqliteDatabaseFile(str(tmp_path), "main")

    assert database.path == tmp_path / "main.db"


def test_the_path_alone_creates_nothing(tmp_path):
    directory = tmp_path / "data"

    _ = SqliteDatabaseFile(str(directory), "main").path

    assert not directory.exists()


def test_prepare_creates_the_missing_directories_and_gives_the_path(tmp_path):
    directory = tmp_path / "data" / "sqlite"

    path = SqliteDatabaseFile(str(directory), "main").prepare()

    assert directory.is_dir()
    assert path == directory / "main.db"


def test_prepare_keeps_an_existing_directory_and_its_files(tmp_path):
    kept = tmp_path / "other.db"
    kept.write_text("x")

    SqliteDatabaseFile(str(tmp_path), "main").prepare()

    assert kept.read_text() == "x"
