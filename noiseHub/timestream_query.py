import boto3
import sys

sys.path.insert(1, '/home/pi/NoiseHub_Hardware/certs')
import keys

DATABASE_NAME='noisehub-timestream'
TABLE_NAME='noise_data'
REGION='us-east-2'

client = boto3.client(
    service_name='timestream-query',
    aws_access_key_id=keys.ACCESS_KEY,
    aws_secret_access_key=keys.SECRET_KEY,
    region_name=REGION,
)

sql_query = 'SELECT * FROM "{DATABASE_NAME}"."{TABLE_NAME}" ORDER BY time DESC LIMIT 1'.format(DATABASE_NAME=DATABASE_NAME, TABLE_NAME=TABLE_NAME)

response = client.query(
    QueryString=sql_query,
    MaxRows=10
)

print(response)