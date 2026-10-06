from pycraftcore.file_handler.adapter.extension.svg.svg_writer import SvgFileWriter

SVG = '<svg xmlns="http://www.w3.org/2000/svg"><text>Salaire €</text></svg>'


def test_write_writes_the_svg_markup_as_utf8(tmp_path):
    file_path = tmp_path / "plot.svg"

    SvgFileWriter.write(str(file_path), SVG)

    assert file_path.read_text(encoding="utf-8") == SVG


def test_write_writes_empty_string_when_data_is_empty(tmp_path):
    file_path = tmp_path / "plot.svg"

    SvgFileWriter.write(str(file_path), "")

    assert file_path.read_text(encoding="utf-8") == ""
