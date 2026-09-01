from pathlib import Path
from unittest.mock import MagicMock

from pycraftcore.application_configuration.adapter.load_application_configuration import (
    LoadApplicationConfiguration,
)
from pycraftcore.application_configuration.adapter.omega_configuration_reader import (
    OmegaConfigurationReader,
)
from pycraftcore.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.application_configuration.port.configuration import Configuration
from pycraftcore.application_configuration.port.configuration_reader import (
    ConfigurationReader,
)


def test_load_application_configuration_satisfies_configuration():
    loader: Configuration = LoadApplicationConfiguration(MagicMock(), MagicMock())

    assert isinstance(loader, Configuration)


def test_omega_configuration_reader_satisfies_configuration_reader():
    reader: ConfigurationReader = OmegaConfigurationReader(RunTypeEnvironment.debug, Path("config"))

    assert isinstance(reader, ConfigurationReader)
