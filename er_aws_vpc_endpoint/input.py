from __future__ import annotations

from typing import Any

from external_resources_io.input import AppInterfaceProvision
from pydantic import BaseModel, Field


class VpcEndpointData(BaseModel):
    """App-Interface input parameters for the VPC Endpoint module"""

    identifier: str
    region: str
    vpc_id: str
    subnet_ids: list[str] = Field(default_factory=list)
    endpoint_service_name: str
    private_dns_enabled: bool = False
    tags: dict[str, Any] = Field(default_factory=dict)
    output_resource_name: str | None = None


class AppInterfaceInput(BaseModel):
    """Validated app-interface input for the VPC Endpoint module."""

    data: VpcEndpointData
    provision: AppInterfaceProvision
