#;=====================================================================
#; > Title:  Classic Load Balancer Lambda Firewall
#; > Author: Andrew Grube
#; > Date:   12 Nov, 2020
#; > Description: This lambda function will take the event from a 
#; CloudWatch SNS event and parse it to obtain the load balancer, 
#; region, and the AWS account id. The variables are then passed to
#; the getLoadBalancerInfo function to obtain the VPC ID and S3
#; logging bucket and add it to the return variable array. The
#; variables are then sent to the athenaParsing function which waits
#; until the logs are written to S3, and then runs the executeQuery
#; function to drop the table, create the table, and then query the
#; 'elb_logs' table. The athenaParsing will then remove the index 
#; which is the "header" column name information in the Athena table.
#; athenaParsing will then return the ip addresses in an array. 
#; Then the updateNACL function will run which is passed the ip address
#; array and updates the NACL of the load balancer to add the ip
#; addresses at 50 and will decrement by 1 for each ip.
#;=====================================================================

import boto3
import time
import datetime
import json


def parseEvent(event):
    print('\nEvent:')
    print(event)
    print('\n')
    snsobj = event['Records'][0]['Sns']['Message']
    x = snsobj.replace("/", "-")
    x = json.loads(x)
    loadBalancer = x['Trigger']['Dimensions'][0]['value']
    alarmArnDict = x['AlarmArn'].split(':')
    accountId = alarmArnDict[4]
    region = alarmArnDict[3]
    return {
        'loadBalancer': loadBalancer,
        'region': region,
        'accountId': accountId
    }


def getLoadBalancerInfo(vars):
    print('Starting getLoadBalancerInfo function...')
    region = vars['region']
    loadBalancer = vars['loadBalancer']
    elb = boto3.client('elb', region_name=region)
    lbAttributes = elb.describe_load_balancer_attributes(
        LoadBalancerName=loadBalancer)
    lb = elb.describe_load_balancers(LoadBalancerNames=[loadBalancer])
    vars['lbvpc'] = lb['LoadBalancerDescriptions'][0]['VPCId']
    vars['s3LoggingBucket'] = lbAttributes['LoadBalancerAttributes']['AccessLog']['S3BucketName']
    return vars


def executeQuery(query, region, accountId, executionType):
    print('Starting executeQuery function...')
    client = boto3.client('athena', region_name=region)
    response_query_execution_id = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': 'default'
        },
        ResultConfiguration={
            'OutputLocation': f's3://aws-athena-query-results-{accountId}-{region}/Unsaved/'
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
        print(executionType + ' ' + status)
        if (status == 'FAILED') or (status == 'CANCELLED'):
            return False, False

        elif status == 'SUCCEEDED':
            location = response_get_query_details['QueryExecution']['ResultConfiguration']['OutputLocation']

            # Function to get output results
            response_query_result = client.get_query_results(
                QueryExecutionId=response_query_execution_id['QueryExecutionId']
            )
            result_data = response_query_result['ResultSet']
            # print("location: ", location)
            # print("data: ", result_data)
            return location, result_data
        else:
            time.sleep(1)

    return False


def athenaParsing(vars):
    print('Starting athenaParsing function...')
    offendingIP = []
    dt = datetime.datetime.today()
    minute = dt.minute
    m = str(minute)
    if len(m) < 2:
        m = '0'+m
    m = int(m[1:])
    if m <= 4:
        print(str(m) + ' is less than or equal to 5.')
        waittime = (6 - m) * 60
        print('wait time is ' + str(waittime) + ' seconds')
    elif m <= 9:
        print(str(m) + ' is less than or equal to 9.')
        waittime = (11 - m) * 60
        print('wait time is ' + str(waittime) + ' seconds')
    region = vars['region']
    lbvpc = vars['lbvpc']
    accountId = vars['accountId']
    s3LoggingBucket = vars['s3LoggingBucket']
    loadBalancer = vars['loadBalancer']
    drop_table = 'DROP TABLE IF EXISTS elb_logs'
    load_table = f'''
    CREATE EXTERNAL TABLE IF NOT EXISTS elb_logs (
    timestamp string,
    elb_name string,
    request_ip string,
    request_port int,
    backend_ip string,
    backend_port int,
    request_processing_time double,
    backend_processing_time double,
    client_response_time double,
    elb_response_code string,
    backend_response_code string,
    received_bytes bigint,
    sent_bytes bigint,
    request_verb string,
    url string,
    protocol string,
    user_agent string,
    ssl_cipher string,
    ssl_protocol string
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.RegexSerDe'
    WITH SERDEPROPERTIES (
    'serialization.format' = '1',
    'input.regex' = '([^ ]*) ([^ ]*) ([^ ]*):([0-9]*) ([^ ]*)[:-]([0-9]*) ([-.0-9]*) ([-.0-9]*) ([-.0-9]*) (|[-0-9]*) (-|[-0-9]*) ([-0-9]*) ([-0-9]*) \\\"([^ ]*) ([^ ]*) (- |[^ ]*)\\\" (\"[^\"]*\") ([A-Z0-9-]+) ([A-Za-z0-9.-]*)$' )
    LOCATION 's3://{s3LoggingBucket}/AWSLogs/{accountId}/elasticloadbalancing/{region}/{dt.year}/{dt.month}/{dt.day}/';
    '''
    fetch_data = f'''
    SELECT
    count(request_ip) as request_count,
    request_ip,
    elb_name
    FROM "elb_logs"
    where elb_name = '{loadBalancer}'
    and backend_response_code like '40%'
    Group by request_ip,elb_name
    HAVING count(request_ip) > 30
    Order by 1 desc;
    '''
    print(
        f'Sleeping for {waittime} seconds to ensure S3 ELB logs are written...')
    time.sleep(waittime)
    result_data = executeQuery(
        drop_table, region, accountId, executionType="drop_table")
    result_data = executeQuery(
        load_table, region, accountId, executionType="load_table")
    result_data = executeQuery(
        fetch_data, region, accountId, executionType="fetch_data")
    response = result_data[1]['Rows']
    # the del statement below removes the [0] index which is the "header" column name information in the Athena table.
    del response[0]
    for row in response:
        ip = row['Data'][1]['VarCharValue']
        # print(f'\n{ip}\n')
        offendingIP.append(ip)
        # print(offendingIP)

    vars['offendingIP'] = offendingIP

    return vars


def updateNACL(vars):
    print('Starting updateNACL function...')
    region = vars['region']
    lbvpc = vars['lbvpc']
    offendingIP = vars['offendingIP']
    ruleNumber = 50
    numOffendingIPs = len(offendingIP)
    ec2 = boto3.resource('ec2', region_name=region)
    vpc = ec2.Vpc(lbvpc)
    network_acl_iterator = vpc.network_acls.all()
    print(offendingIP)
    for ip in offendingIP:
        print(f'\nIterating through loop for {ip}...\n')
        for x in network_acl_iterator:
            nacl = str(x)
            nacl = nacl.split('\'')
            nacl = nacl[1]
            network_acl = ec2.NetworkAcl(nacl)
            # print(network_acl)
            for acl in network_acl.entries:
                if acl['RuleNumber'] == ruleNumber:
                    print(f'Rule #{ruleNumber} exists in {nacl} removing..')
                    network_acl.delete_entry(
                        Egress=False,
                        RuleNumber=ruleNumber
                    )
            print('adding ' + str(ip) + ' to ' +
                  str(nacl) + ' as rule #' + str(ruleNumber))
            network_acl.create_entry(
                CidrBlock=f'{ip}/32',
                Egress=False,
                Protocol="-1",
                RuleAction='deny',
                RuleNumber=ruleNumber)
        ruleNumber -= 1
    return vars


def lambda_handler(event, context):
    results = parseEvent(event)
    print('Ended parseEvent function...\n')
    results = getLoadBalancerInfo(results)
    print('Ended getLoadBalancerInfo function...\n')
    results = athenaParsing(results)
    print('Ended athenaParsing function...\n')
    results = updateNACL(results)
    print('Ended updateNACL function...\n')

    return {
        'statusCode': 200,
        'body': json.dumps('Offending IP Addresses successfully blocked!')
    }
