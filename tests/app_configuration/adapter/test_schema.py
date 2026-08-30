from pycraftcore.application_configuration.adapter.schema import (
    ApplicationConfigurationSchema,
    MapperDomainSchema,
)
from pycraftcore.application_configuration.enum.run_type_application import RunTypeApplication
from pycraftcore.application_configuration.enum.run_type_environment import RunTypeEnvironment
from pycraftcore.application_configuration.model.configuration import ApplicationConfiguration


def test_map_converts_schema_into_domain_model():
    schema = ApplicationConfigurationSchema(
        env=RunTypeEnvironment.debug,
        run=RunTypeApplication.asynchronous,
        connector={},
        operation={},
        cronjob=[],
    )

    result = MapperDomainSchema.map(schema)

    assert isinstance(result, ApplicationConfiguration)
    assert result.env == RunTypeEnvironment.debug
    assert result.run == RunTypeApplication.asynchronous
    assert result.connector == {}
    assert result.operation == {}
    assert result.cronjob == []
