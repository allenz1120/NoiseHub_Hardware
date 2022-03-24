import boto3
import sys

sys.path.insert(1, '/home/pi/NoiseHub_Hardware/certs')
import keys

keys.ACCESS_KEY='AKIATBZ4AXFK2GH4DGRF'
keys.SECRET_KEY='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'
DATABASE_NAME='noisehub-timestream'
TABLE_NAME='noise_data'
REGION='us-east-2'

client = boto3.client(
    service_name='timestream-query',
    aws_access_key_id=keys.ACCESS_KEY,
    aws_secret_access_key=keys.SECRET_KEY,
    region_name=REGION,
)

door_sql_query = 'SELECT * FROM "{DATABASE_NAME}"."door_table" WHERE time > ago(24h) ORDER BY time'.format(DATABASE_NAME=DATABASE_NAME)
noise_sql_query = 'SELECT * FROM "{DATABASE_NAME}"."noise_data" WHERE time > ago(24h) ORDER BY time'.format(DATABASE_NAME=DATABASE_NAME)

door_data = client.query(
    QueryString=door_sql_query
    # MaxRows=10
)

noise_data = client.query(
    QueryString=noise_sql_query
    # MaxRows=10
)

print(door_data)
print('\n')
print(noise_data)
