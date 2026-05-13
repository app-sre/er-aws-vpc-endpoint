locals {
  # Service name format: com.amazonaws.vpce.<region>.<svc-id>
  service_region  = split(".", var.endpoint_service_name)[3]
  is_cross_region = local.service_region != var.region
  tags            = merge(var.tags, { Name = "vpce-${var.identifier}" })
}

# Only needed for same-region: look up supported AZs to filter subnets.
# Cross-region PrivateLink has no AZ alignment requirement.
data "aws_vpc_endpoint_service" "this" {
  count        = local.is_cross_region ? 0 : 1
  service_name = var.endpoint_service_name
}

data "aws_subnet" "all" {
  for_each = local.is_cross_region ? toset([]) : toset(var.subnet_ids)
  id       = each.value
}

locals {
  # For same-region, filter to subnets in AZs supported by the endpoint service.
  # For cross-region, all subnets are valid.
  supported_subnet_ids = local.is_cross_region ? var.subnet_ids : [
    for subnet_id, subnet in data.aws_subnet.all :
    subnet_id
    if contains(data.aws_vpc_endpoint_service.this[0].availability_zones, subnet.availability_zone)
  ]
}

resource "aws_security_group" "endpoint" {
  name        = "${var.identifier}-endpoint-sg"
  description = "Security group for VPC endpoint ${var.identifier}"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.tags
}

resource "aws_vpc_endpoint" "this" {
  vpc_id              = var.vpc_id
  service_name        = var.endpoint_service_name
  vpc_endpoint_type   = "Interface"
  subnet_ids          = local.supported_subnet_ids
  security_group_ids  = [aws_security_group.endpoint.id]
  private_dns_enabled = false
  ip_address_type     = "ipv4"
  service_region      = local.service_region
  tags                = local.tags
}
