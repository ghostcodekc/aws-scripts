from __future__ import print_function
import json
import boto3

print('Loading function')

# open connection to ec2
ec2 = boto3.client('ec2')

#Set Regions Variable and get all regions
regions = ec2.describe_regions().get('Regions',[] )
all_regions = [region['RegionName'] for region in regions]


for region_name in all_regions:
      print('Instances in EC2 Region {0}:'.format(region_name))
      ec2 = boto3.resource('ec2', region_name=region_name)

      #Get ALL instances to make reference to
      allinstances = ec2.instances.all()

      # Grab a list of all instnaces that have a "region" tag.
      taggedInstances = ec2.instances.filter(
          Filters=[
              {'Name': 'tag:Region', 'Values': ['**']}
          ]
      )
      #Set regionTag to KeyValue Pair Region : $CurrentRegion
      regionTag = [{
          "Key" : "Region", 
          "Value" : region_name
      }]

      # make a list of filtered instances IDs `[i.id for i in instances]`
      # Filter from all instances the instance that are not in the filtered list
      instances_to_tag = [to_tag for to_tag in allinstances if to_tag.id not in [i.id for i in taggedInstances]]
      for instance in instances_to_tag:
          for tag in instance.tags:  # Get the name of the instance
              if tag['Key'] == 'Name':
                  taggedInstanceName = tag['Value']
          print('Instance to tag: {2} || {0} in {1}'.format(taggedInstanceName, region_name, instance.id))
          print('Modifying tags on {0}'.format(instance.id))
          instance.create_tags(Tags=regionTag)
        #   ec2.create_tags(
        #     Resources = [instance["InstanceId"]],
        #     Tags= regionTag
        #    )