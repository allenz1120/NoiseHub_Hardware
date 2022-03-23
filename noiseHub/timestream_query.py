import boto3

ACCESS_KEY='AKIATBZ4AXFK2AXA7QHV'
SECRET_KEY='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'
DATABASE_NAME='noisehub-timestream'
TABLE_NAME='noise_data'
REGION='us-east-2'

client = boto3.client(
    service_name='timestream-query',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name=REGION,
)

sql_query = 'SELECT * FROM "{DATABASE_NAME}"."{TABLE_NAME}" ORDER BY time DESC LIMIT 1'.format(DATABASE_NAME=DATABASE_NAME, TABLE_NAME=TABLE_NAME)

response = client.query(
    QueryString=sql_query,
    MaxRows=10
)

print(response)