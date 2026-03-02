terraform {
  required_version = ">= 1.6.0"

  # Remote state on Terraform Cloud (free) — keeps state between CI/CD runs
  # without needing AWS S3. Every runner reads/writes the same state file.
  cloud {
    organization = "ssnc-veerathorn"  # replace with your Terraform Cloud org name
    workspaces {
      name = "ssnc-hello-world"
    }
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
