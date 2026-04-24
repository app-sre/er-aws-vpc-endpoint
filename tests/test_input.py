import pytest
from pydantic import ValidationError

from er_aws_vpc_endpoint.input import AppInterfaceInput


def test_basic_input(base_input: dict) -> None:
    ai_input = AppInterfaceInput.model_validate(base_input)
    assert ai_input.data.identifier == "myservice-endpoint"
    assert (
        ai_input.data.endpoint_service_name
        == "com.amazonaws.vpce.us-east-1.vpce-svc-0123456789abcdef0"
    )
    assert ai_input.data.vpc_id == "vpc-0123456789abcdef0"
    assert ai_input.data.region == "us-east-1"
    assert ai_input.data.subnet_ids == ["subnet-aaaa", "subnet-bbbb"]


def test_data_fields(base_input: dict) -> None:
    ai_input = AppInterfaceInput.model_validate(base_input)
    assert ai_input.data.region == "us-east-1"
    assert ai_input.data.identifier == "myservice-endpoint"
    assert (
        ai_input.data.endpoint_service_name
        == "com.amazonaws.vpce.us-east-1.vpce-svc-0123456789abcdef0"
    )
    assert ai_input.data.vpc_id == "vpc-0123456789abcdef0"
    assert ai_input.data.tags == base_input["data"]["tags"]


def test_empty_subnet_ids(base_input: dict) -> None:
    base_input["data"]["subnet_ids"] = []
    ai_input = AppInterfaceInput.model_validate(base_input)
    assert ai_input.data.subnet_ids == []


def test_default_subnet_ids(base_input: dict) -> None:
    del base_input["data"]["subnet_ids"]
    ai_input = AppInterfaceInput.model_validate(base_input)
    assert ai_input.data.subnet_ids == []


def test_default_tags(base_input: dict) -> None:
    del base_input["data"]["tags"]
    ai_input = AppInterfaceInput.model_validate(base_input)
    assert ai_input.data.tags == {}


def test_missing_required_field(base_input: dict) -> None:
    del base_input["data"]["endpoint_service_name"]
    with pytest.raises(ValidationError):
        AppInterfaceInput.model_validate(base_input)


def test_missing_vpc_id(base_input: dict) -> None:
    del base_input["data"]["vpc_id"]
    with pytest.raises(ValidationError):
        AppInterfaceInput.model_validate(base_input)
