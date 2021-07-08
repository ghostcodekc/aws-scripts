import boto3, datetime, time, pprint, json, requests
pp = pprint.PrettyPrinter(indent=4)

################## CHANGE VALUES BELOW TO MATCH YOUR ENVIRONMENT ##################

webhook_url = ''
athenaQueryResultLocation = ''
cloudTrailLoggingBucket = ''
consoleSignInFalureAlarmName = ''
cloudTrailChangesAlarmName = ''
iamPolicyChangesAlarmName = ''
authorizationFailuresAlarmName = ''
ec2InstanceChangesAlarmName = ''
gatewayChangesAlarmName = ''
ec2LargeInstanceChangesAlarmName = ''
networkACLChangesAlarmName = ''
securityGroupChangesAlarmName = ''
vpcChangesAlarmName = ''

################## CHANGE VALUES ABOVE TO MATCH YOUR ENVIRONMENT ##################

time_now = time.time()
start_time = time_now - 900
start_time = datetime.datetime.fromtimestamp(start_time)
start_time_month = start_time.strftime("%m")
start_time_day = start_time.strftime("%d")
start_time_minute = start_time.strftime("%M")
start_time_hour = start_time.strftime("%H")
start_time_string = f"{start_time.year}-{start_time_month}-{start_time_day}T{start_time_hour}:{start_time_minute}:00Z"

def create_authorization_failures_query(time_now_string, table_name):
    query = f'''SELECT useridentity.arn as username, eventname, eventtime as date, errormessage FROM "default"."{table_name}" WHERE "eventname" LIKE 'UnauthorizedOperation' OR "errorcode" LIKE 'AccessDenied' AND "eventtime" BETWEEN '{start_time_string}' AND '{time_now_string}' '''
    return query

def create_console_sign_in_failure_query(time_now_string, table_name):
    query = f'''SELECT useridentity.arn as username, eventname, eventtime as date, errormessage FROM "default"."{table_name}" WHERE "eventname" LIKE 'ConsoleLogin' AND "errormessage" LIKE 'Failed authentication' AND "eventtime" between '{start_time_string}' and '{time_now_string}' '''
    return query

def create_iam_policy_changes_query(time_now_string, table_name):
    query = f'''SELECT useridentity.arn as username, eventname, eventtime as date, requestparameters FROM "default"."{table_name}" WHERE "eventname" LIKE 'DeleteGroupPolicy' OR "eventname" LIKE 'DeleteRolePolicy' OR "eventname" LIKE 'DeleteUserPolicy' OR "eventname" LIKE 'PutGroupPolicy' OR "eventname" LIKE 'PutRolePolicy' OR "eventname" LIKE 'PutUserPolicy' OR "eventname" LIKE 'CreatePolicy' OR "eventname" LIKE 'DeletePolicy' OR "eventname" LIKE 'CreatePolicyVersion' OR "eventname" LIKE 'DeletePolicyVersion' OR "eventname" LIKE 'AttachRolePolicy' OR "eventname" LIKE 'DetachRolePolicy' OR "eventname" LIKE 'AttachUserPolicy' OR "eventname" LIKE 'DetachUserPolicy' OR "eventname" LIKE 'AttachGroupPolicy' OR "eventname" LIKE 'DetachGroupPolicy' AND "eventtime" BETWEEN '{start_time_string}' AND '{time_now_string}' '''
    return query

def create_cloud_trail_changes_query(time_now_string, table_name):
    query = f'''SELECT useridentity.arn as username, eventname, eventtime as date, errormessage FROM "default"."{table_name}" WHERE "eventname" LIKE 'CreateTrail' OR "eventname" LIKE 'DeleteTrail' OR "eventname" LIKE 'StartLogging' OR "eventname" LIKE 'StopLogging' AND "eventtime" BETWEEN '{start_time_string}' AND '{time_now_string}' '''
    return query

def create_vpc_changes_query(time_now_string, table_name):
    query = f'''SELECT useridentity.arn as username, eventname, eventtime as date, requestparameters FROM "default"."{table_name}" WHERE "eventname" LIKE 'CreateVpc' OR "eventname" LIKE 'DeleteVpc' OR "eventname" LIKE 'ModifyVpcAttribute' OR "eventname" LIKE 'AcceptVpcPeeringConnection' OR "eventname" LIKE 'CreateVpcPeeringConnection' OR "eventname" LIKE 'DeleteVpcPeeringConnection' OR "eventname" LIKE 'RejectVpcPeeringConnection' OR "eventname" LIKE 'AttachClassicLinkVpc' OR "eventname" LIKE 'DetachClassicLinkVpc' OR "eventname" LIKE 'DisableVpcClassicLink' OR "eventname" LIKE 'EnableVpcClassicLink' AND "eventtime" BETWEEN '{start_time_string}' AND '{time_now_string}' '''
    return query

def getProperQuery(event, time_now_string, table_name):
    json_message = json.loads(event['Records'][0]['Sns']['Message'])
    alarmName = json_message['AlarmName']
    print(f'alarmname in getProperQuery = {alarmName}')
    if alarmName == consoleSignInFalureAlarmName:
        query = create_console_sign_in_failure_query(time_now_string, table_name)
        return query, alarmName
    if alarmName == cloudTrailChangesAlarmName:
        query = create_cloud_trail_changes_query(time_now_string, table_name)
        return query, alarmName
    if alarmName == iamPolicyChangesAlarmName:
        query = create_iam_policy_changes_query(time_now_string, table_name)
        return query, alarmName
    if alarmName == authorizationFailuresAlarmName:
        query = create_authorization_failures_query(time_now_string, table_name)
        return query, alarmName
    if alarmName == vpcChangesAlarmName:
        query = create_vpc_changes_query(time_now_string, table_name)
        return query, alarmName

def athenaParsing(event, table_name):
    print('Starting athenaParsing function...')
    dt = datetime.datetime.today()
    minute =  dt.strftime("%M")
    month = dt.strftime("%m")
    hour = dt.strftime("%H")
    year = dt.year
    day = dt.strftime("%d")
    time_now_string = f'{year}-{month}-{day}T{hour}:{minute}:59Z'
    m = str(minute)
    m = int(m[1:])
    if m <= 4:
        print(str(m) + ' is less than or equal to 5.')
        waittime = (6 - m) * 60
        print('wait time is ' + str(waittime) + ' seconds')
    elif m <= 9:
        print(str(m) + ' is less than or equal to 9.')
        waittime = (11 - m) * 60
        print('wait time is ' + str(waittime) + ' seconds')
    fetch_data = getProperQuery(event, time_now_string, table_name)
    alarmName = fetch_data[1]
    print(fetch_data)
    print(f'alarmName in athenaParsing function = {alarmName}')
    drop_table = f'DROP TABLE IF EXISTS {table_name}'
    load_table = f'''
        CREATE EXTERNAL TABLE {table_name}(
        eventVersion STRING,
        userIdentity STRUCT<
            type: STRING,
            principalId: STRING,
            arn: STRING,
            accountId: STRING,
            invokedBy: STRING,
            accessKeyId: STRING,
            userName: STRING,
            sessionContext: STRUCT<
                attributes: STRUCT<
                    mfaAuthenticated: STRING,
                    creationDate: STRING>,
                sessionIssuer: STRUCT<
                    type: STRING,
                    principalId: STRING,
                    arn: STRING,
                    accountId: STRING,
                    userName: STRING>>>,
        eventTime STRING,
        eventSource STRING,
        eventName STRING,
        awsRegion STRING,
        sourceIpAddress STRING,
        userAgent STRING,
        errorCode STRING,
        errorMessage STRING,
        requestParameters STRING,
        responseElements STRING,
        additionalEventData STRING,
        requestId STRING,
        eventId STRING,
        readOnly STRING,
        resources ARRAY<STRUCT<
            arn: STRING,
            accountId: STRING,
            type: STRING>>,
        eventType STRING,
        apiVersion STRING,
        recipientAccountId STRING,
        serviceEventDetails STRING,
        sharedEventID STRING,
        vpcEndpointId STRING
    )
    PARTITIONED BY (
    `timestamp` string)
    ROW FORMAT SERDE 'com.amazon.emr.hive.serde.CloudTrailSerde'
    STORED AS INPUTFORMAT 'com.amazon.emr.cloudtrail.CloudTrailInputFormat'
    OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
    LOCATION
    's3://{cloudTrailLoggingBucket}'
    TBLPROPERTIES (
    'projection.enabled'='true', 
    'projection.timestamp.format'='yyyy/MM/dd', 
    'projection.timestamp.interval'='1', 
    'projection.timestamp.interval.unit'='DAYS', 
    'projection.timestamp.range'='{year}/{month}/{day},NOW', 
    'projection.timestamp.type'='date', 
    'storage.location.template'='s3://{cloudTrailLoggingBucket}${{timestamp}}')
    '''
    pp.pprint(f'Sleeping for {waittime} seconds to ensure S3 CloudTrail logs are written...')
    time.sleep(waittime)
    time.sleep(60)
    drop_table = executeQuery(drop_table, executionType="drop_table")
    time.sleep(2)
    load_table = executeQuery(load_table, executionType="load_table")
    time.sleep(2)
    result_data = executeQuery(fetch_data[0], executionType="fetch_data")
    response = result_data[1]['Rows']
    # the del statement below removes the [0] index which is the "header" column name information in the Athena table.
    del response[0]
    return response, alarmName

def executeQuery(query, executionType):
    pp.pprint('Starting executeQuery function...')
    client = boto3.client('athena', region_name='us-east-1')
    response_query_execution_id = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': 'default'
        },
        ResultConfiguration={
            'OutputLocation': f's3://{athenaQueryResultLocation}'
        }
    )
    # This function takes query execution id as input and returns the details of the query executed
    response_get_query_details = client.get_query_execution(
        QueryExecutionId=response_query_execution_id['QueryExecutionId']
    )
    status = 'RUNNING'
    iterations = 15
    while (iterations > 0):
        iterations = iterations - 1
        response_get_query_details = client.get_query_execution(
            QueryExecutionId=response_query_execution_id['QueryExecutionId']
        )
        status = response_get_query_details['QueryExecution']['Status']['State']
        pp.pprint(executionType + ' ' + status)
        if (status == 'FAILED') or (status == 'CANCELLED'):
            return False, False

        elif status == 'SUCCEEDED':
            location = response_get_query_details['QueryExecution']['ResultConfiguration']['OutputLocation']

            # Function to get output results
            response_query_result = client.get_query_results(
                QueryExecutionId=response_query_execution_id['QueryExecutionId']
            )
            result_data = response_query_result['ResultSet']
            return location, result_data
        else:
            time.sleep(1)

    return False

def sendToSlack(data, alarmName):
    print(data)
    num_of_alarms = len(data)
    num_of_alarms -= 1
    print(num_of_alarms)
    for alarm in data:
        print(alarm['Data'])
        userName = alarm['Data'][0]['VarCharValue']
        print(f'userName Value: {userName}')
        userName = userName.replace('arn:aws:sts::', '')
        userName = userName.replace('arn:aws:iam::', '')
        userName = userName[13:]
        eventName = alarm['Data'][1]['VarCharValue']
        alarmTime = alarm['Data'][2]['VarCharValue']
        additionalDetails = alarm['Data'][3]['VarCharValue']
        message = f"####################################\nAlarm: {alarmName}\nBlame: {userName}\nTime: {alarmTime}\nEvent Name: {eventName}\nAdditional Information: {additionalDetails}\n####################################"
        print(message)
        slack_data = {'text': message}
        print(slack_data)
        response = requests.post(
            webhook_url, data = json.dumps(slack_data),
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code != 200:
            raise ValueError(
                'Request to slack returned an error %s, the response is:\n%s'
                % (response.status_code, response.text)
        )
        num_of_alarms -= 1
    return data

def lambda_handler(event, context):
    event_time = event['Records'][0]['Sns']['Timestamp']
    print(f'Event Time: {event_time}')
    print(event)
    requestid = context.aws_request_id
    requestid = requestid.replace('-', '')
    table_name = f'cloudtrail_logs_{requestid}'
    print(f'Athena Table Name: {table_name}')
    response = athenaParsing(event, table_name)
    print(f'Response Variable after athenaParsing function: {response}')
    results = sendToSlack(response[0], response[1])
    cleanupFunction(table_name)
    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }

def cleanupFunction(table_name):
    cleanup_table_query = f'DROP TABLE IF EXISTS {table_name}'
    cleanup_table = executeQuery(cleanup_table_query, executionType="drop_table")