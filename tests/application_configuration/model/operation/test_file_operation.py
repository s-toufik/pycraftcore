from pycraftcore.application_configuration.enum.file_operation_action import (
    FileOperationAction,
)
from pycraftcore.application_configuration.enum.operation_type import OperationType
from pycraftcore.application_configuration.model import FileOperation
from tests.application_configuration.model.connectors import file_connector


def test_file_operation_holds_action_and_parameters():
    operation = FileOperation(
        name="export",
        type=OperationType.file,
        connector=file_connector(),
        action=FileOperationAction.write,
        parameters={"path": "str"},
    )

    assert operation.action == FileOperationAction.write
    assert operation.parameters == {"path": "str"}
