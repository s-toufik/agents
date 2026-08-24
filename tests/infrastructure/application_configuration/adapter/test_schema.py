from agentic_core.infrastructure.application_configuration.adapter.schema import (
    ApplicationConfigurationSchema,
    MapperDomainSchema,
)
from agentic_core.infrastructure.application_configuration.enum.run_type_application import (
    RunTypeApplication,
)
from agentic_core.infrastructure.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from agentic_core.infrastructure.application_configuration.model.configuration import (
    ApplicationConfiguration,
)


def test_map_builds_application_configuration_field_for_field():
    schema = ApplicationConfigurationSchema(
        env=RunTypeEnvironment.develop,
        run=RunTypeApplication.asynchronous,
        connector={},
        operation={},
    )

    configuration = MapperDomainSchema.map(schema)

    assert isinstance(configuration, ApplicationConfiguration)
    assert configuration.env == RunTypeEnvironment.develop
    assert configuration.run == RunTypeApplication.asynchronous
    assert configuration.connector == {}
    assert configuration.operation == {}
