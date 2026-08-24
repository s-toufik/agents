import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from agentic_core.infrastructure.runtime.python.adapter import ALLOWLIST, SafeCode


def test_parse_code_embeds_sorted_allowlist_and_repr_of_code():
    safe_code = SafeCode(code="result = 1 + 1", max_memory_mb=128)

    source = safe_code._parse_code()

    assert repr("result = 1 + 1") in source
    assert "_ALLOWED_IMPORTS = set(" in source
    assert str(sorted(ALLOWLIST)) in source
    assert "128" in source


@pytest.mark.asyncio
async def test_execute_runs_real_sandboxed_code_and_returns_json_result():
    safe_code = SafeCode(code="result = 2 + 2", code_timeout=10)

    output = await safe_code.execute()

    assert output.stderr == ""
    assert '"result": 4' in output.stdout


@pytest.mark.asyncio
async def test_execute_returns_timeout_message_on_timeout_expired():
    safe_code = SafeCode(code="result = 1", code_timeout=5)

    with patch(
        "agentic_core.infrastructure.runtime.python.adapter.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="python", timeout=5),
    ):
        output = await safe_code.execute()

    assert output.stdout == ""
    assert "timed out after 5s" in output.stderr


@pytest.mark.asyncio
async def test_execute_returns_subprocess_error_message_on_unexpected_exception():
    safe_code = SafeCode(code="result = 1")

    with patch(
        "agentic_core.infrastructure.runtime.python.adapter.subprocess.run",
        side_effect=OSError("no such file"),
    ):
        output = await safe_code.execute()

    assert output.stdout == ""
    assert "Subprocess error" in output.stderr
    assert "no such file" in output.stderr


@pytest.mark.asyncio
async def test_execute_on_nonzero_returncode_embeds_stderr_text_not_returncode():
    """Regression test documenting a real bug: the non-zero-returncode branch formats
    `f"Process exited with code {proc.stderr}."`, embedding stderr text where the
    numeric return code was almost certainly intended."""
    safe_code = SafeCode(code="result = 1")
    fake_proc = MagicMock(returncode=1, stdout="", stderr="Traceback (most recent call last)")

    with patch(
        "agentic_core.infrastructure.runtime.python.adapter.subprocess.run",
        return_value=fake_proc,
    ):
        output = await safe_code.execute()

    assert output.stderr == "Process exited with code Traceback (most recent call last)."


@pytest.mark.asyncio
async def test_execute_always_removes_temporary_script(tmp_path):
    created_paths = []
    original_create = SafeCode._create_temporary_script

    def spying_create(runner_src):
        path = original_create(runner_src)
        created_paths.append(path)
        return path

    safe_code = SafeCode(code="result = 1")
    with patch.object(SafeCode, "_create_temporary_script", staticmethod(spying_create)):
        await safe_code.execute()

    assert created_paths
    assert not os.path.exists(created_paths[0])
