from pycraftcore.file_handler.adapter.extension.svg.svg_reader import SvgFileReader

SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><circle r="4"/></svg>\n'


def test_read_returns_the_svg_markup_as_string(tmp_path):
    file_path = tmp_path / "plot.svg"
    file_path.write_text(SVG, encoding="utf-8")

    result = SvgFileReader.read(str(file_path))

    assert result == SVG


def test_read_returns_empty_string_for_empty_file(tmp_path):
    file_path = tmp_path / "empty.svg"
    file_path.write_text("")

    result = SvgFileReader.read(str(file_path))

    assert result == ""
