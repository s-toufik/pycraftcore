import pytest

from pycraftcore.file_handler.adapter.extension.xls.xls_writer import XlsFileWriter


def test_write_raises_not_implemented(tmp_path):
    file_path = tmp_path / "data.xls"

    with pytest.raises(NotImplementedError):
        XlsFileWriter.write(str(file_path), [{"name": "test"}])
