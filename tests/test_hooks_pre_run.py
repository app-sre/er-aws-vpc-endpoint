from collections.abc import Iterator
from unittest.mock import MagicMock, call, patch

import pytest

from er_aws_vpc_endpoint.input import AppInterfaceInput
from hooks.pre_run import VpcEndpointPreRunValidator, service_region


@pytest.fixture
def mock_aws_api() -> Iterator[MagicMock]:
    with patch("hooks.pre_run.AWSApi") as mock:
        yield mock


def test_service_region_extraction() -> None:
    assert service_region("com.amazonaws.vpce.us-east-1.vpce-svc-0123") == "us-east-1"
    assert service_region("com.amazonaws.vpce.eu-west-1.vpce-svc-abcd") == "eu-west-1"


def test_validate_service_exists(
    ai_input: AppInterfaceInput,
    mock_aws_api: MagicMock,
) -> None:
    mock_aws_api.return_value.check_endpoint_service_exists.return_value = True
    validator = VpcEndpointPreRunValidator(ai_input)
    assert validator.validate()
    assert not validator.errors
    mock_aws_api.return_value.check_endpoint_service_exists.assert_called_once_with(
        "com.amazonaws.vpce.us-east-1.vpce-svc-0123456789abcdef0"
    )


def test_validate_service_not_found(
    ai_input: AppInterfaceInput,
    mock_aws_api: MagicMock,
) -> None:
    mock_aws_api.return_value.check_endpoint_service_exists.return_value = False
    validator = VpcEndpointPreRunValidator(ai_input)
    assert not validator.validate()
    assert len(validator.errors) == 1
    assert (
        "com.amazonaws.vpce.us-east-1.vpce-svc-0123456789abcdef0" in validator.errors[0]
    )


def test_validator_usesservice_region(
    ai_input: AppInterfaceInput,
    mock_aws_api: MagicMock,
) -> None:
    """Validator must call AWSApi with the service's region, not the consumer's."""
    mock_aws_api.return_value.check_endpoint_service_exists.return_value = True
    VpcEndpointPreRunValidator(ai_input)
    mock_aws_api.assert_called_once_with(config_options={"region_name": "us-east-1"})


def test_validate_private_dns_not_checked_when_disabled(
    ai_input: AppInterfaceInput,
    mock_aws_api: MagicMock,
) -> None:
    mock_aws_api.return_value.check_endpoint_service_exists.return_value = True
    validator = VpcEndpointPreRunValidator(ai_input)
    assert validator.validate()
    assert not validator.warnings
    mock_aws_api.return_value.get_private_dns_verification_state.assert_not_called()


def test_validate_private_dns_verified(
    ai_input: AppInterfaceInput,
    mock_aws_api: MagicMock,
) -> None:
    ai_input.data.private_dns_enabled = True
    mock_aws_api.return_value.check_endpoint_service_exists.return_value = True
    mock_aws_api.return_value.get_vpc_dns_attributes.return_value = (True, True)
    mock_aws_api.return_value.get_private_dns_verification_state.return_value = (
        "verified"
    )
    validator = VpcEndpointPreRunValidator(ai_input)
    assert validator.validate()
    assert not validator.warnings


def test_validate_private_dns_pending_warns(
    ai_input: AppInterfaceInput,
    mock_aws_api: MagicMock,
) -> None:
    ai_input.data.private_dns_enabled = True
    mock_aws_api.return_value.check_endpoint_service_exists.return_value = True
    mock_aws_api.return_value.get_vpc_dns_attributes.return_value = (True, True)
    mock_aws_api.return_value.get_private_dns_verification_state.return_value = (
        "pendingVerification"
    )
    validator = VpcEndpointPreRunValidator(ai_input)
    assert validator.validate()
    assert len(validator.warnings) == 1
    assert "pendingVerification" in validator.warnings[0]


def test_validate_private_dns_dns_support_disabled(
    ai_input: AppInterfaceInput,
    mock_aws_api: MagicMock,
) -> None:
    ai_input.data.private_dns_enabled = True
    mock_aws_api.return_value.check_endpoint_service_exists.return_value = True
    mock_aws_api.return_value.get_vpc_dns_attributes.return_value = (False, True)

    validator = VpcEndpointPreRunValidator(ai_input)

    assert not validator.validate()
    assert len(validator.errors) == 1
    assert "enableDnsSupport" in validator.errors[0]
    mock_aws_api.return_value.get_private_dns_verification_state.assert_not_called()


def test_validate_private_dns_dns_hostnames_disabled(
    ai_input: AppInterfaceInput,
    mock_aws_api: MagicMock,
) -> None:
    ai_input.data.private_dns_enabled = True
    mock_aws_api.return_value.check_endpoint_service_exists.return_value = True
    mock_aws_api.return_value.get_vpc_dns_attributes.return_value = (True, False)

    validator = VpcEndpointPreRunValidator(ai_input)

    assert not validator.validate()
    assert len(validator.errors) == 1
    assert "enableDnsHostnames" in validator.errors[0]
    mock_aws_api.return_value.get_private_dns_verification_state.assert_not_called()


def test_validator_uses_consumer_region_for_vpc_dns(
    ai_input: AppInterfaceInput,
    mock_aws_api: MagicMock,
) -> None:
    ai_input.data.private_dns_enabled = True
    ai_input.data.region = "eu-west-1"
    service_api = MagicMock()
    consumer_api = MagicMock()
    service_api.check_endpoint_service_exists.return_value = True
    service_api.get_private_dns_verification_state.return_value = "verified"
    consumer_api.get_vpc_dns_attributes.return_value = (True, True)
    mock_aws_api.side_effect = [service_api, consumer_api]

    validator = VpcEndpointPreRunValidator(ai_input)

    assert validator.validate()
    assert mock_aws_api.call_args_list == [
        call(config_options={"region_name": "us-east-1"}),
        call(config_options={"region_name": "eu-west-1"}),
    ]
    consumer_api.get_vpc_dns_attributes.assert_called_once_with("vpc-0123456789abcdef0")


def test_validate_private_dns_not_checked_when_service_missing(
    ai_input: AppInterfaceInput,
    mock_aws_api: MagicMock,
) -> None:
    ai_input.data.private_dns_enabled = True
    mock_aws_api.return_value.check_endpoint_service_exists.return_value = False
    validator = VpcEndpointPreRunValidator(ai_input)
    assert not validator.validate()
    assert not validator.warnings
    mock_aws_api.return_value.get_private_dns_verification_state.assert_not_called()
