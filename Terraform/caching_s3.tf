resource "aws_s3_bucket" "c23-smearbot-caching-bucket" {
  bucket = var.s3_name
}