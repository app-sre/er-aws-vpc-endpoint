# External Resources VPC Endpoint Module

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

External Resources module to provision and manage AWS VPC Endpoints (AWS PrivateLink — consumer side) with app-interface.

Creates an interface VPC Endpoint connecting to a VPC Endpoint Service provisioned by the [`er-aws-vpc-endpoint-service`](https://github.com/app-sre/er-aws-vpc-endpoint-service) module. Handles subnet selection and AZ alignment automatically.

## Resources Managed

| Resource | Terraform Type | Notes |
|---|---|---|
| Security Group | `aws_security_group` | Allows all traffic; the endpoint service's allowed principals are the access boundary. |
| VPC Endpoint | `aws_vpc_endpoint` | Interface endpoint connecting to the VPC Endpoint Service. |

## Design Decisions

- **One endpoint per module invocation** — matches the ERv2 pattern of one resource per invocation.
- **Only works with VPCES-created services** — designed for services provisioned by `er-aws-vpc-endpoint-service`, not AWS-managed endpoint services.
- **Private subnets auto-selected** — subnets tagged `privacy: private` in the VPC reference are used automatically.
- **AZ alignment handled automatically** — for same-region, subnets are filtered to those in AZs supported by the endpoint service. For cross-region, all subnets are used (no AZ restriction applies).
- **`private_dns_enabled` defaults to `false`** — opt-in. Requires the endpoint service to have a verified private DNS name (see [`er-aws-vpc-endpoint-service`](https://github.com/app-sre/er-aws-vpc-endpoint-service)). If unset, consumers use the `endpoint_dns_name` from the output secret.
- **Security group allows all traffic** — the endpoint service's allowed principals list is the access control boundary.
- **Pre-run hook fails the run** if the endpoint service is not found or not accessible from this account.

## Tech stack

* Terraform
* AWS provider
* Python 3.12
* Pydantic

## Development

Prepare your local development environment:

```bash
make dev
```

See the `Makefile` for more details.

### Update Terraform providers

To update the Terraform providers used in this project, bump the version in [versions.tf](/terraform/versions.tf) and update the Terraform lockfile via:

```bash
make providers-lock
```

### Development workflow

1. Make changes to the code.
1. Build the image with `make build`.
1. Run the image manually with a proper input file and credentials. See the [Debugging](#debugging) section below.
1. Please don't forget to remove (`-e ACTION=Destroy`) any development AWS resources you create, as they will incur costs.

## Debugging

To debug and run the module locally, run the following commands:

```bash
# Get the input file from app-interface
$ qontract-cli --config=<CONFIG_TOML> external-resources --provisioner <AWS_ACCOUNT_NAME> --provider vpc-endpoint --identifier <IDENTIFIER> get-input > tmp/input.json

# Get the AWS credentials
$ qontract-cli --config=<CONFIG_TOML> external-resources --provisioner <AWS_ACCOUNT_NAME> --provider vpc-endpoint --identifier <IDENTIFIER> get-credentials > tmp/credentials

# Run the module
$ podman run --rm -it \
    --mount type=bind,source=$PWD/tmp/input.json,target=/inputs/input.json \
    --mount type=bind,source=$PWD/tmp/credentials,target=/credentials \
    --mount type=bind,source=$PWD/tmp/work,target=/work \
    -e DRY_RUN=True \
    -e ACTION=Apply \
    quay.io/redhat-services-prod/app-sre-tenant/er-aws-vpc-endpoint-main/er-aws-vpc-endpoint-main:latest
```

## Known Limitations

- **VPCES-only** — this module only connects to services created by `er-aws-vpc-endpoint-service`. AWS-managed services (e.g., `com.amazonaws.us-east-1.s3`) are not supported.
- **Private DNS is opt-in** — `private_dns_enabled` defaults to `false`. Enabling it before the endpoint service's private DNS name is verified does not fail `terraform apply`, but DNS resolution will not work until AWS completes verification.
- **AZ alignment (same-region)** — the endpoint can only be placed in subnets whose AZ is supported by the endpoint service. If the provider's NLB does not cover the consumer's AZs, no subnets will be selected and Terraform will error. Resolve by verifying AZ ID overlap or asking the provider to extend the NLB to additional AZs.
- **Physical AZ mapping** — AZ names (e.g., `us-east-1a`) map to different physical datacenters across AWS accounts in certain legacy regions. Use AZ IDs (e.g., `use1-az1`) to verify alignment: `aws ec2 describe-availability-zones --query 'AvailabilityZones[].{Name:ZoneName,Id:ZoneId}'`.
