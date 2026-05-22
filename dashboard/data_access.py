import boto3
import os


def get_dynamodb_table():
    table_name = os.getenv("DYNAMODB_TABLE")
    region = os.getenv("AWS_REGION", "eu-west-2")
    dynamodb = boto3.resource("dynamodb", region_name=region)

    return dynamodb.Table(table_name)


def get_all_articles():
    table = get_dynamodb_table()
    response = table.scan()

    return response.get("Items", [])
