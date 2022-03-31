from xmlrpc.client import DateTime
import boto3
import sys
from datetime import datetime
import json

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

# Queries data from last 24h
door_sql_query = 'SELECT * FROM "{DATABASE_NAME}"."door_table" WHERE time > ago(24h) ORDER BY time'.format(DATABASE_NAME=DATABASE_NAME)
noise_sql_query = 'SELECT * FROM "{DATABASE_NAME}"."noise_data" WHERE time > ago(24h) ORDER BY time'.format(DATABASE_NAME=DATABASE_NAME)

# # Queries all data (Not just last 24h)
# door_sql_query = 'SELECT * FROM "{DATABASE_NAME}"."door_table" ORDER BY time'.format(DATABASE_NAME=DATABASE_NAME)
# noise_sql_query = 'SELECT * FROM "{DATABASE_NAME}"."noise_data" ORDER BY time'.format(DATABASE_NAME=DATABASE_NAME)

door_data = client.query(
    QueryString=door_sql_query
    # MaxRows=10
)

noise_data = client.query(
    QueryString=noise_sql_query
    # MaxRows=10
)

time_placeholder = datetime.now()

# Global dictionary for populating DynamoDB
dynamo_data = {
    'noise_timestamp': [],
    'noise_data': [],

    'max_loud_timestamp': '',
    'max_loud_value': 0,
    'max_quiet_timestamp': '',
    'max_quiet_value': 0,

    'head_timestamp': [],
    'head_data': [],

    'max_head_timestamp': '',
    'max_head_value': 0,
    'min_head_timestamp': '',
    'min_head_value': 0,

    'temp_timestamp': [],
    'temp_data': [],

    'max_temp_timestamp': '',
    'max_temp_value': 0,
    'min_temp_timestamp': '',
    'min_temp_value': 0
}

# print(door_data)
# print('\n')
# print(noise_data)

# Noise data parsing
noise_data = noise_data['Rows']

curr_loud_duration = 0
curr_loud_timestamp = time_placeholder
max_loud_duration = 0
max_loud_time = time_placeholder

curr_quiet_duration = 0
curr_quiet_timestamp = time_placeholder
max_quiet_duration = 0
max_quiet_time = time_placeholder

for row in noise_data:
    timestamp = row['Data'][2]['ScalarValue'][:-3]

    # Convert timestamp string to DateTime object
    datetime_object = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')

    # Append timestamp to global dictionary
    dynamo_data['noise_timestamp'].append(str(datetime_object))
    
    # Isolate the noise level of the data
    noise_level = row['Data'][0]['ScalarValue']

    # Append noise level to global dictionary
    dynamo_data['noise_data'].append(int(noise_level))

    # If the noise level is loud and previous reading was not loud, increment loud duration and save the current timestamp
    if noise_level == '2' and curr_loud_duration == 0:
        curr_loud_duration += 1
        curr_loud_timestamp = datetime_object
    # If the noise level is loud and the previous reading was loud, increment loud duration
    elif noise_level == '2':
        curr_loud_duration += 1
    # If the noise level is not loud
    else:
        # Check if the max loud duration is lower than the current loud duration. If so, update the max values
        if (max_loud_duration < curr_loud_duration):
            max_loud_duration = curr_loud_duration
            max_loud_time = curr_loud_timestamp
        # Reset the loud duration to 0 so it flags a low/medium noise level
        curr_loud_duration = 0

    # If the noise level is quiet and previous reading was not quiet, increment quiet duration and save the current timestamp
    if noise_level == '0' and curr_quiet_duration == 0:
        curr_quiet_duration += 1
        curr_quiet_timestamp = datetime_object
    # If the noise level is quiet and the previous reading was quiet, increment quiet duration
    elif noise_level == '0':
        curr_quiet_duration += 1
    # If the noise level is not quiet
    else:
        # Check if the max quiet duration is lower than the current quiet duration. If so, update the max values
        if (max_quiet_duration < curr_quiet_duration):
            max_quiet_duration = curr_quiet_duration
            max_quiet_time = curr_quiet_timestamp
        # Reset the quiet duration to 0 so it flags a medium/loud noise level
        curr_quiet_duration = 0

    # print(f'timestamp: {timestamp}')
    # print(f'noise_level: {noise_level}')

    # print(f'max_loud_duration: {max_loud_duration}')
    # print(f'max_loud_time: {max_loud_time}')

    # print(f'max_quiet_duration: {max_quiet_duration}')
    # print(f'max_quiet_time: {max_quiet_time}')

# Append max and min variables to global dictionary
dynamo_data['max_loud_timestamp'] = str(max_loud_time)
dynamo_data['max_loud_value'] = max_loud_duration
dynamo_data['max_quiet_timestamp'] = str(max_quiet_time)
dynamo_data['max_quiet_value'] = max_quiet_duration

# print(dynamo_data)


# Door data parsing
door_data = door_data['Rows']

max_heads = 0
max_heads_time = time_placeholder

min_heads = 100
min_heads_time = time_placeholder

max_temp = 0.0
max_temp_time = time_placeholder

min_temp = 100.0
min_temp_time = time_placeholder

for row in door_data:
    # print(row['Data'])

    timestamp = row['Data'][3]['ScalarValue'][:-3]

    # Convert timestamp string to DateTime object
    datetime_object = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
    
    # Append timestamp to global dictionary
    dynamo_data['head_timestamp'].append(str(datetime_object))
    dynamo_data['temp_timestamp'].append(str(datetime_object))
    
    temp = row['Data'][1]['ScalarValue']
    temp = round(float(temp) * 1.8 + 32, 2)

    # Append temp(erature) to global dictionary
    dynamo_data['temp_data'].append(str(temp))

    heads = int(row['Data'][0]['ScalarValue'])
    
    # Append headcount to global dictionary
    dynamo_data['head_data'].append(heads)
    
    if(temp > max_temp):
        max_temp = temp
        max_temp_time = datetime_object
    elif (temp < min_temp):
        min_temp = temp
        min_temp_time = datetime_object
        
    if(heads > max_heads):
        max_heads = heads
        max_heads_time = datetime_object
    elif(heads < min_heads):
        min_heads = heads
        min_heads_time = datetime_object

    # print(f'timestamp: {timestamp}')
    # print(f'temp: {temp}')
    # print(f'heads: {heads}')

# Append max and min variables to global dictionary
dynamo_data['max_head_timestamp'] = str(max_heads_time)
dynamo_data['max_head_value'] = max_heads
dynamo_data['min_head_timestamp'] = str(min_heads_time)
dynamo_data['min_head_value'] = min_heads

dynamo_data['max_temp_timestamp'] = str(max_temp_time)
dynamo_data['max_temp_value'] = str(max_temp)
dynamo_data['min_temp_timestamp'] = str(min_temp_time)
dynamo_data['min_temp_value'] = str(min_temp)

# print(dynamo_data)

DYNAMO_ACCESS_KEY=keys.DYNAMO_ACCESS_KEY
DYNAMO_SECRET_KEY=keys.DYNAMO_SECRET_KEY
TABLE_NAME='spaceTable'
UUID="113"

dynamodb = boto3.resource(
    service_name='dynamodb', 
    region_name='us-east-2',
    aws_access_key_id=DYNAMO_ACCESS_KEY,
    aws_secret_access_key=DYNAMO_SECRET_KEY,
)   

table = dynamodb.Table(TABLE_NAME)

data = json.dumps(dynamo_data)

response = table.update_item(
    Key={
        'uuid': '113',
    },
    UpdateExpression="set graphData=:g",
    ExpressionAttributeValues={
        ':g': data,
    },
    ReturnValues="UPDATED_NEW"
)
print(response)
