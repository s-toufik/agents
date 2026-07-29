import pytest

from hypothesis import given, strategies as st

from agentic.infrastructure.repository.sql.adapter import SQLExpressionHandler

# ============================================================================
# Strategies
# ============================================================================

identifiers = st.text(
    alphabet="bcdfghjklmnpqrstvwxz",
    min_size=1,
    max_size=20,
)


@st.composite
def select_queries(draw):
    table = draw(identifiers)

    return f"""
        SELECT *
        FROM {table}
    """


@st.composite
def cte_select_queries(draw):
    table = draw(identifiers)

    return f"""
        WITH filtered AS (
            SELECT *
            FROM {table}
        )
        SELECT *
        FROM filtered
    """


@st.composite
def insert_queries(draw):
    table = draw(identifiers)
    value = draw(st.integers())

    return f"""
        INSERT INTO {table}(id)
        VALUES ({value})
    """


@st.composite
def update_queries(draw):
    table = draw(identifiers)
    column = draw(identifiers)
    value = draw(st.integers())

    return f"""
        UPDATE {table}
        SET {column} = {value}
    """


@st.composite
def delete_queries(draw):
    table = draw(identifiers)

    return f"""
        DELETE FROM {table}
    """


@st.composite
def drop_queries(draw):
    table = draw(identifiers)

    return f"""
        DROP TABLE {table}
    """


# ============================================================================
# Parse tests
# ============================================================================


def test_empty_sql_is_invalid():
    handler = SQLExpressionHandler(
        "",
        "sqlite",
    )

    with pytest.raises(ValueError):
        handler.parse()


@given(select_queries())
def test_random_select_queries_can_be_parsed(query):
    handler = SQLExpressionHandler(
        query,
        "sqlite",
    )

    expressions = handler.parse()

    assert len(expressions) == 1


@given(select_queries())
def test_multiple_select_statements_can_be_parsed(query):
    handler = SQLExpressionHandler(
        f"""
        {query};

        {query};
        """,
        "sqlite",
    )

    expressions = handler.parse()

    assert len(expressions) == 2


# ============================================================================
# Read-only validation tests
# ============================================================================


@given(select_queries())
def test_all_select_queries_are_allowed(query):
    handler = SQLExpressionHandler(
        query,
        "sqlite",
    )

    expressions = handler.parse()

    handler.validate_read_only(expressions)


@given(cte_select_queries())
def test_cte_select_queries_are_allowed(query):
    handler = SQLExpressionHandler(
        query,
        "sqlite",
    )

    expressions = handler.parse()

    handler.validate_read_only(expressions)


@given(
    st.one_of(
        insert_queries(),
        update_queries(),
        delete_queries(),
        drop_queries(),
    )
)
def test_all_write_operations_are_rejected(query):
    handler = SQLExpressionHandler(
        query,
        "sqlite",
    )

    expressions = handler.parse()

    with pytest.raises(ValueError):
        handler.validate_read_only(expressions)


@given(
    select_queries(),
    insert_queries(),
)
def test_mixed_safe_and_unsafe_statements_are_rejected(
    safe_query,
    unsafe_query,
):
    handler = SQLExpressionHandler(
        f"""
        {safe_query};

        {unsafe_query};
        """,
        "sqlite",
    )

    expressions = handler.parse()

    with pytest.raises(ValueError):
        handler.validate_read_only(expressions)


# ============================================================================
# Hidden mutation tests
# ============================================================================


@given(identifiers)
def test_delete_hidden_after_cte_is_rejected(table):
    query = f"""
        WITH data AS (
            SELECT *
            FROM {table}
        )
        DELETE FROM {table}
    """

    handler = SQLExpressionHandler(
        query,
        "sqlite",
    )

    expressions = handler.parse()

    with pytest.raises(ValueError):
        handler.validate_read_only(expressions)


@given(identifiers)
def test_multiple_statements_with_drop_are_rejected(table):
    query = f"""
        SELECT *
        FROM {table};

        DROP TABLE {table};
    """

    handler = SQLExpressionHandler(
        query,
        "sqlite",
    )

    expressions = handler.parse()

    with pytest.raises(ValueError):
        handler.validate_read_only(expressions)


# ============================================================================
# Transpile tests
# ============================================================================


def test_transpile_returns_sqlite_sql():
    handler = SQLExpressionHandler(
        """
        SELECT *
        FROM users
        LIMIT 10
        """,
        "postgres",
    )

    result = handler.transpile()

    assert "SELECT" in result
    assert "users" in result


@given(select_queries())
def test_transpile_accepts_safe_queries(query):
    handler = SQLExpressionHandler(
        query,
        "postgres",
    )

    result = handler.transpile()

    assert isinstance(result, str)


@given(
    st.one_of(
        insert_queries(),
        update_queries(),
        delete_queries(),
        drop_queries(),
    )
)
def test_transpile_rejects_unsafe_queries(query):
    handler = SQLExpressionHandler(
        query,
        "sqlite",
    )

    with pytest.raises(ValueError):
        handler.transpile()
