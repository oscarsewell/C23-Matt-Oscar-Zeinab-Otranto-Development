#As the terraform_dynamodb file stands:

##Important notes for future

Important notes for deployment and use:
The different 'rows' will be subject-article dependant. I.E every article will have a separate input for each specified person/company 

The database will need the following keys:
- "subject_name" with value as a string specific to one individual contained in the article. Ensure proper capitalization, and no acronyms for companies.


- "published_at_article_url"with a value of a string containing the date and URL, in the format 'YYYY-MM-DDTHH:MM:SS_**URL**' this will act as the unique identifier and also allow automatic sorting based upon publish time.


##Further development:

- The ARN for the stream is aws_dynamodb_table.c23-smearbot-enriched-data-dynamodb-table.stream_arn

- lambda stream policy to refer access to stream:

resource "aws_iam_role_policy" "lambda_stream_policy" {
  name = "lambda-stream-policy"
  role = aws_iam_role.lambda_dynamodb_stream_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:GetRecords",
        "dynamodb:GetShardIterator",
        "dynamodb:DescribeStream",
        "dynamodb:ListStreams"
      ]
      Resource = "${aws_dynamodb_table.c23-smearbot-enriched-data-dynamodb-table.stream_arn}/*"
    }]
  })
}