import json
from pathlib import Path
from unittest.mock import patch

import pytest
from external_resources_io.config import EnvVar

from er_aws_vpc_endpoint.__main__ import get_ai_input, main
from er_aws_vpc_endpoint.input import AppInterfaceInput


@pytest.fixture(autouse=True)
def prepare_test_env(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    base_input: dict,
) -> None:
    input_json = tmp_path / "input.json"
    input_json.write_text(json.dumps(base_input))
    monkeypatch.setenv(EnvVar.INPUT_FILE, str(input_json.absolute()))


def test_get_ai_input(ai_input: AppInterfaceInput) -> None:
    result = get_ai_input()
    assert isinstance(result, AppInterfaceInput)
    assert result == ai_input


def test_main() -> None:
    with (
        patch("er_aws_vpc_endpoint.__main__.create_backend_tf_file") as mock_backend,
        patch("er_aws_vpc_endpoint.__main__.create_tf_vars_json") as mock_tfvars,
    ):
        main()

    mock_backend.assert_called_once()
    mock_tfvars.assert_called_once()
    tf_data = mock_tfvars.call_args[0][0]
    assert tf_data.identifier == "myservice-endpoint"
    assert tf_data.vpc_id == "vpc-0123456789abcdef0"
    assert tf_data.subnet_ids == ["subnet-aaaa", "subnet-bbbb"]
    assert (
        tf_data.endpoint_service_name
        == "com.amazonaws.vpce.us-east-1.vpce-svc-0123456789abcdef0"
    )
