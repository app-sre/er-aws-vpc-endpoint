"""Entry point for generating Terraform configuration files."""

from __future__ import annotations

from external_resources_io.input import parse_model, read_input_from_file
from external_resources_io.terraform import create_backend_tf_file, create_tf_vars_json

from er_aws_vpc_endpoint.input import AppInterfaceInput


def get_ai_input() -> AppInterfaceInput:
    """Parse and return the AppInterfaceInput from the input file."""
    return parse_model(AppInterfaceInput, read_input_from_file())


def main() -> None:
    """Generate Terraform backend and variables files from app-interface input."""
    ai_input = get_ai_input()
    create_backend_tf_file(ai_input.provision)
    create_tf_vars_json(ai_input.data)


if __name__ == "__main__":
    main()
