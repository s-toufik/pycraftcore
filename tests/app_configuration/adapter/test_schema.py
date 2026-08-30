from pycraftcore.app_configuration.adapter.schema import AppConfigurationSchema, MapperDomainSchema
from pycraftcore.app_configuration.enum.run_type_application import RunTypeApplication
from pycraftcore.app_configuration.enum.run_type_environment import RunTypeEnvironment
from pycraftcore.app_configuration.model.configuration import AppConfiguration


def test_map_converts_schema_into_domain_model():
    schema = AppConfigurationSchema(
        env=RunTypeEnvironment.debug,
        run=RunTypeApplication.asynchronous,
        connector={},
        operation={},
        cronjob=[],
    )

    result = MapperDomainSchema.map(schema)

    assert isinstance(result, AppConfiguration)
    assert result.env == RunTypeEnvironment.debug
    assert result.run == RunTypeApplication.asynchronous
    assert result.connector == {}
    assert result.operation == {}
    assert result.cronjob == []
