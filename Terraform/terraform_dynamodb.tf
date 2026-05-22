resource "aws_dynamodb_table" "c23-smearbot-enriched-data-dynamodb-table" {
  name           = var.dynamodb_table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "subject_name"
  range_key      = "published_at_article_url"
  stream_enabled = true
  stream_view_type = "NEW_IMAGE"

  attribute {
    name = "subject_name"
    type = "S"
  }

  attribute {
    name = "published_at_article_url"
    type = "S"
  }

  tags = {
    Name        = var.dynamodb_table_name
  }
}