output "repository_url" {
  description = "ECR repository URL for docker push/pull"
  value       = aws_ecr_repository.main.repository_url
}

output "repository_name" {
  description = "ECR repository name"
  value       = aws_ecr_repository.main.name
}
