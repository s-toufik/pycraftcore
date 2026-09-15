from pycraftcore.file_handler.enum.read_chunk_mode import ReadChunkMode


def test_line_member_value():
    assert ReadChunkMode.LINE == "line"


def test_line_member_is_str_enum_instance():
    assert isinstance(ReadChunkMode.LINE, str)
