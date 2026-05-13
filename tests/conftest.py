import pytest
from external_resources_io.input import parse_model

from er_aws_vpc_endpoint.input import AppInterfaceInput


@pytest.fixture
def base_input() -> dict:
    return {
        "data": {
            "identifier": "myservice-endpoint",
            "region": "us-east-1",
            "vpc_id": "vpc-0123456789abcdef0",
            "subnet_ids": ["subnet-aaaa", "subnet-bbbb"],
            "endpoint_service_name": "com.amazonaws.vpce.us-east-1.vpce-svc-0123456789abcdef0",
            "tags": {
                "managed_by_integration": "external_resources",
                "cluster": "appsret02ue1",
                "namespace": "myservice-stage",
                "environment": "production",
                "app": "myservice",
            },
        },
        "provision": {
            "provision_provider": "aws",
            "provisioner": "appsret02ue1",
            "provider": "vpc-endpoint",
            "identifier": "myservice-endpoint",
            "target_cluster": "appsret02ue1",
            "target_namespace": "myservice-stage",
            "target_secret_name": "myservice-endpoint",
            "module_provision_data": {
                "tf_state_bucket": "external-resources-terraform-state-dev",
                "tf_state_region": "us-east-1",
                "tf_state_dynamodb_table": "external-resources-terraform-lock",
                "tf_state_key": "aws/appsret02ue1/vpc-endpoint/myservice-endpoint/terraform.tfstate",
            },
        },
    }


@pytest.fixture
def ai_input(base_input: dict) -> AppInterfaceInput:
    return parse_model(AppInterfaceInput, base_input)
