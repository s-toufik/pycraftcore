from pycraftcore.app_configuration.enum.connector_type import ConnectorType
from pycraftcore.app_configuration.enum.file_operation_action import FileOperationAction
from pycraftcore.app_configuration.model.connector import FileConnector
from pycraftcore.app_configuration.model.cronjob import CronJob
from pycraftcore.app_configuration.model.operation import FileOperation
from pycraftcore.authentication.model.auth_type import AuthType
from pycraftcore.authentication.model.no_auth import NoAuth


def test_cronjob_holds_name_cron_expression_and_operation():
    connector = FileConnector(
        name="files",
        type=ConnectorType.file,
        auth=NoAuth(type=AuthType.none),
        base_path="/var/files",
    )
    operation = FileOperation(
        name="cleanup",
        connector=connector,
        action=FileOperationAction.delete,
        parameters={},
    )

    job = CronJob(name="nightly-cleanup", cron="0 0 * * *", operation=operation)

    assert job.name == "nightly-cleanup"
    assert job.cron == "0 0 * * *"
    assert job.operation is operation
