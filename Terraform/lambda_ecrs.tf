# ECR Repository for RSS Extraction Lambda
resource "aws_ecr_repository" "rss_extraction" {
  name                 = var.rss_extraction_repo_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ECR Lifecycle Policy for RSS Extraction Lambda
resource "aws_ecr_lifecycle_policy" "rss_extraction_policy" {
  repository = aws_ecr_repository.rss_extraction.name
    policy     = jsonencode({
        rules = [
            {
                rulePriority = 1,
                description = "Keep only the 5 most recent images",
                selection = {
                    tagStatus = "any",
                    countType = "imageCountMoreThan",
                    countNumber = 5
                }
                action = {
                    type = "expire"
                }
            }
        ]
    })
}

# ECR Repository for Article Scraping Lambda
resource "aws_ecr_repository" "article_scraping" {
  name                 = var.article_scraping_repo_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ECR Lifecycle Policy for Article Scraping Lambda
resource "aws_ecr_lifecycle_policy" "article_scraping_policy" {
  repository = aws_ecr_repository.article_scraping.name
    policy     = jsonencode({
        rules = [
            {
                rulePriority = 1,
                description = "Keep only the 5 most recent images",
                selection = {
                    tagStatus = "any",
                    countType = "imageCountMoreThan",
                    countNumber = 5
                }
                action = {
                    type = "expire"
                }
            }
        ]
    })
}


# ECR Repository for Data Enrichment Lambda
resource "aws_ecr_repository" "data_enrichment" {
  name                 = var.data_enrichment_repo_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ECR Lifecycle Policy for Data Enrichment Lambda
resource "aws_ecr_lifecycle_policy" "data_enrichment_policy" {
  repository = aws_ecr_repository.data_enrichment.name
    policy     = jsonencode({
        rules = [
            {
                rulePriority = 1,
                description = "Keep only the 5 most recent images",
                selection = {
                    tagStatus = "any",
                    countType = "imageCountMoreThan",
                    countNumber = 5
                }
                action = {
                    type = "expire"
                }
            }
        ]
    })
}