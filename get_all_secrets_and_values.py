import boto3
import json
import pprint
pp = pprint.PrettyPrinter(indent=4)

def get_secrets():
    client = boto3.client('secretsmanager')
    response = client.list_secrets()
    results_for_call=100
    response = client.list_secrets(MaxResults=results_for_call)
    i=0
    secretList = []
    while True:
        i=i+1
        if 'NextToken' in response:
            response = client.list_secrets(MaxResults=results_for_call,NextToken=response['NextToken'])
        else:
            response = client.list_secrets(MaxResults=results_for_call)
        for secret in response['SecretList']:
            secretList.append(secret['Name'])
        if 'NextToken' not in response:
            break
    return secretList

def get_secret_values(secrets):
    data = {}
    data['Keys'] = {}
    for i in secrets:
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(
            SecretId=i
        )
        secretData = {i : response['SecretString'] }
        data['Keys'].update(secretData)
    return data

secretList = get_secrets()
Kingdom = get_secret_values(secretList)
with open('secrets.json', 'w') as outfile:
    json.dump(Kingdom, outfile)