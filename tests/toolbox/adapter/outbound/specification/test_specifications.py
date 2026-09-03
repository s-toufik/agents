from toolbox.adapter.outbound.specification import python_sandbox, user_database


def test_python_sandbox_specification_declares_a_required_code_parameter() -> None:
    spec = python_sandbox.SPECIFICATION

    assert spec.name == "python_executor"
    assert len(spec.parameters) == 1
    assert spec.parameters[0].name == "code"
    assert spec.parameters[0].required is True
    assert str(python_sandbox.TIMEOUT_SECONDS) in spec.description


def test_user_database_specification_declares_query_and_optional_dialect() -> None:
    spec = user_database.SPECIFICATION

    assert spec.name == "users_tables"
    names = {p.name: p.required for p in spec.parameters}
    assert names == {"query": True, "dialect": False}
    assert user_database.DIALECT in spec.description
