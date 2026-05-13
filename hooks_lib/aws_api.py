from __future__ import annotations

from typing import TYPE_CHECKING, Any

from boto3 import Session
from botocore.config import Config
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from mypy_boto3_ec2 import EC2Client


class AWSApi:
    """AWS API client for VPC Endpoint operations"""

    def __init__(self, config_options: Mapping[str, Any]) -> None:
        self.session = Session()
        self.config = Config(**config_options)

    @property
    def ec2_client(self) -> EC2Client:
        """Return an EC2 client for the configured region."""
        return self.session.client("ec2", config=self.config)

    def check_endpoint_service_exists(self, service_name: str) -> bool:
        """Return True if the given VPC endpoint service name exists and is visible."""
        try:
            response = self.ec2_client.describe_vpc_endpoint_services(
                ServiceNames=[service_name]
            )
            return bool(response.get("ServiceDetails", []))
        except ClientError as e:
            if e.response["Error"]["Code"] in {"InvalidServiceName", "InvalidFilter"}:
                return False
            raise
