from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from hooks_lib.aws_api import AWSApi


@pytest.fixture
def mock_botocore_config(mocker: MagicMock) -> MagicMock:
    return mocker.patch("hooks_lib.aws_api.Config")


@pytest.fixture
def mock_session(mocker: MagicMock) -> MagicMock:
    return mocker.patch("hooks_lib.aws_api.Session")


def test_aws_api_init(mock_session: MagicMock, mock_botocore_config: MagicMock) -> None:
    config_options = {"region_name": "us-east-1"}
    api = AWSApi(config_options=config_options)
    mock_session.assert_called_once_with()
    assert api.session == mock_session.return_value
    mock_botocore_config.assert_called_once_with(**config_options)
    assert api.config == mock_botocore_config.return_value


@pytest.fixture
def aws_api(
    mock_session: MagicMock,
    mocker: MagicMock,
) -> tuple[AWSApi, MagicMock]:
    mocker.patch("hooks_lib.aws_api.Config")
    api = AWSApi(config_options={})
    return api, mock_session.return_value


def test_aws_api_ec2_client(aws_api: tuple[AWSApi, MagicMock]) -> None:
    api, mock_session = aws_api
    client = api.ec2_client
    mock_session.client.assert_called_once_with("ec2", config=api.config)
    assert client == mock_session.client.return_value


@pytest.fixture
def aws_api_with_mock_client(
    aws_api: tuple[AWSApi, MagicMock],
) -> tuple[AWSApi, MagicMock]:
    api, mock_session = aws_api
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client
    return api, mock_client


def test_check_endpoint_service_exists_found(
    aws_api_with_mock_client: tuple[AWSApi, MagicMock],
) -> None:
    api, mock_client = aws_api_with_mock_client
    mock_client.describe_vpc_endpoint_services.return_value = {
        "ServiceDetails": [
            {"ServiceName": "com.amazonaws.vpce.us-east-1.vpce-svc-0123"}
        ]
    }
    result = api.check_endpoint_service_exists(
        "com.amazonaws.vpce.us-east-1.vpce-svc-0123"
    )
    assert result is True
    mock_client.describe_vpc_endpoint_services.assert_called_once_with(
        ServiceNames=["com.amazonaws.vpce.us-east-1.vpce-svc-0123"]
    )


def test_check_endpoint_service_exists_empty(
    aws_api_with_mock_client: tuple[AWSApi, MagicMock],
) -> None:
    api, mock_client = aws_api_with_mock_client
    mock_client.describe_vpc_endpoint_services.return_value = {"ServiceDetails": []}
    result = api.check_endpoint_service_exists(
        "com.amazonaws.vpce.us-east-1.vpce-svc-0123"
    )
    assert result is False


def test_check_endpoint_service_exists_invalid_service_name(
    aws_api_with_mock_client: tuple[AWSApi, MagicMock],
) -> None:
    api, mock_client = aws_api_with_mock_client
    mock_client.describe_vpc_endpoint_services.side_effect = ClientError(
        {"Error": {"Code": "InvalidServiceName", "Message": "Not found"}},
        "DescribeVpcEndpointServices",
    )
    result = api.check_endpoint_service_exists(
        "com.amazonaws.vpce.us-east-1.vpce-svc-bad"
    )
    assert result is False


def test_check_endpoint_service_exists_other_error_propagates(
    aws_api_with_mock_client: tuple[AWSApi, MagicMock],
) -> None:
    api, mock_client = aws_api_with_mock_client
    mock_client.describe_vpc_endpoint_services.side_effect = ClientError(
        {"Error": {"Code": "UnauthorizedOperation", "Message": "Access denied"}},
        "DescribeVpcEndpointServices",
    )
    with pytest.raises(ClientError):
        api.check_endpoint_service_exists("com.amazonaws.vpce.us-east-1.vpce-svc-0123")
