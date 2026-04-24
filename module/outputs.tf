output "endpoint_id" {
  description = "The ID of the VPC Endpoint"
  value       = aws_vpc_endpoint.this.id
}

output "endpoint_dns_name" {
  description = "The primary DNS name for the VPC Endpoint"
  value       = aws_vpc_endpoint.this.dns_entry[0].dns_name
}

