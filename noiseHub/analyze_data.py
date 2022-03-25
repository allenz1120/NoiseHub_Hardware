import boto3
import sys

sys.path.insert(1, '../certs')
import keys

DATABASE_NAME='noisehub-timestream'
# TABLE_NAME='noise_data'
REGION='us-east-2'

client = boto3.client(
    service_name='timestream-query',
    aws_access_key_id=keys.ACCESS_KEY,
    aws_secret_access_key=keys.SECRET_KEY,
    region_name=REGION,
)

door_sql_query = 'SELECT * FROM "{DATABASE_NAME}"."door_table" WHERE time > ago(24h) ORDER BY time'.format(DATABASE_NAME=DATABASE_NAME)
noise_sql_query = 'SELECT * FROM "{DATABASE_NAME}"."noise_data" WHERE time > ago(24h) ORDER BY time'.format(DATABASE_NAME=DATABASE_NAME)

# door_data = client.query(
#     QueryString=door_sql_query
#     # MaxRows=10
# )

noise_data = client.query(
    QueryString=noise_sql_query
    # MaxRows=10
)

# print(door_data)
# print('\n')
# print(noise_data)

# Noise data parsing
noise_data = noise_data['Rows']
for row in noise_data:
    # print(row['Data'])

    timestamp = row['Data'][2]['ScalarValue']
    noise_level = row['Data'][3]['ScalarValue']

    print(f'timestamp: {timestamp}')
    print(f'noise_level: {noise_level}')
