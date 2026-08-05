variable "endpoint_service_name" {
  type = string
}

variable "identifier" {
  type = string
}

variable "output_resource_name" {
  type    = string
  default = null
}

variable "region" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "tags" {
  type = map(any)
}

variable "private_dns_enabled" {
  type    = bool
  default = false
}

variable "vpc_id" {
  type = string
}
