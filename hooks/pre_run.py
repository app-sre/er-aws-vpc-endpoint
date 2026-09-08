#!/usr/bin/env python3
from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from external_resources_io.exit_status import EXIT_ERROR, EXIT_OK
from external_resources_io.input import parse_model, read_input_from_file
from external_resources_io.log import setup_logging

from er_aws_vpc_endpoint.input import AppInterfaceInput
from hooks_lib.aws_api import AWSApi

if TYPE_CHECKING:
    from mypy_boto3_ec2.literals import DnsNameStateType

logger = logging.getLogger(__name__)

VERIFIED_STATE: DnsNameStateType = "verified"


def service_region(service_name: str) -> str:
    """Extract the AWS region from a VPC endpoint service name.

    Format: com.amazonaws.vpce.<region>.<svc-id>
    """
    return service_name.split(".")[3]


class VpcEndpointPreRunValidator:
    """Validate that the referenced VPC Endpoint Service exists before running Terraform."""

    def __init__(self, app_interface_input: AppInterfaceInput) -> None:
        self.input = app_interface_input
        service_name = self.input.data.endpoint_service_name
        # Check in the service's own region, not the consumer's region,
        # to correctly handle cross-region PrivateLink scenarios.
        region = service_region(service_name)
        self.aws_api = AWSApi(config_options={"region_name": region})
        self.vpc_aws_api = self.aws_api
        if self.input.data.region != region:
            self.vpc_aws_api = AWSApi(
                config_options={"region_name": self.input.data.region}
            )
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate(self) -> bool:
        """Check if the endpoint service is accessible; return True if no errors."""
        service_name = self.input.data.endpoint_service_name
        if not self.aws_api.check_endpoint_service_exists(service_name):
            self.errors.append(
                f"VPC Endpoint Service '{service_name}' not found or not accessible. "
                "Either the service name is incorrect, or this account's ARN has not "
                "been added to the service's allowed principals."
            )
        elif self.input.data.private_dns_enabled:
            self._validate_vpc_dns_attributes()
            if not self.errors:
                state = self.aws_api.get_private_dns_verification_state(service_name)
                if state != VERIFIED_STATE:
                    self.warnings.append(
                        f"private_dns_enabled is set but the endpoint service's private "
                        f"DNS name verification state is '{state}', not "
                        f"'{VERIFIED_STATE}'. "
                        "DNS resolution will not work until AWS completes verification."
                    )
        return not self.errors

    def _validate_vpc_dns_attributes(self) -> None:
        """Require VPC DNS attributes when Private DNS is enabled."""
        vpc_id = self.input.data.vpc_id
        dns_support, dns_hostnames = self.vpc_aws_api.get_vpc_dns_attributes(vpc_id)
        if not dns_support:
            self.errors.append(
                f"Consumer VPC '{vpc_id}' must have enableDnsSupport enabled "
                "when private_dns_enabled is true."
            )
        if not dns_hostnames:
            self.errors.append(
                f"Consumer VPC '{vpc_id}' must have enableDnsHostnames enabled "
                "when private_dns_enabled is true."
            )


if __name__ == "__main__":
    setup_logging()
    app_interface_input = parse_model(AppInterfaceInput, read_input_from_file())
    validator = VpcEndpointPreRunValidator(app_interface_input)
    if not validator.validate():
        logger.error(validator.errors)
        sys.exit(EXIT_ERROR)
    for warning in validator.warnings:
        logger.warning(warning)
    logger.info("Pre-run validation passed")
    sys.exit(EXIT_OK)
