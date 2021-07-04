import boto3, datetime, argparse, sys

def main(sendit, dryrun):
    AWSAccountId = boto3.client('sts').get_caller_identity().get('Account')
    t = datetime.datetime.utcnow()
    filename = f'Output/[{AWSAccountId}]-{t.strftime("%m")}-{t.strftime("%d")}-{t.year}-{t.strftime("%H%M%S")}UTC_gp2_conversion_information.txt'
    count = 0
    regions = ["us-east-1", "us-east-2", "us-west-1", "us-west-2"]

    # Create new blank gp2_volume_information.txt file.
    f = open(filename, "x")
    f.write(f'\n###########################################################\nVolumes Not Attached to any EC2 Instance.\nAccount: {AWSAccountId}\n###########################################################')

    for region in regions:
        # Initializing EC2 boto 3 client
        ec2_client = boto3.client('ec2', region_name=region)
        f.write(f'\n{region}:\n')
        # Retrieving all volumes that are currently gp2
        response = ec2_client.describe_volumes(Filters=[{'Name': 'volume-type', 'Values': ['gp2']}])

        # Iterating over each gp2 volume
        for volume in response['Volumes']:
            volumeInfo = ec2_client.describe_volumes(Filters=[{'Name': 'volume-id', 'Values': [volume['VolumeId']]}])
            for y in volumeInfo['Volumes']:
                try:
                    if len(y['Attachments']) < 1:
                        # Writing output to file.
                        f.write("\n" + str(volume['VolumeId']) + " has " + str(volume['Iops']) + " IOPS. Info (Not attached to any instance...)\n")
                    else:
                        for tag in y['Tags']: 
                            if tag['Key'] == 'Name':
                                # Writing output to file.
                                f.write("\n" + str(volume['VolumeId']) + " has " + str(volume['Iops']) + " IOPS. Info ("+ str(tag['Value']) + " ||| " + str(y['Attachments'][0]['InstanceId']) + ")\n")
                except KeyError as ke:
                    # Writing output to file.
                    f.write("\n" + str(volume['VolumeId']) + " has " + str(volume['Iops']) + " IOPS. Info ("+ str(y['Attachments'][0]['InstanceId']) + ")\n")

            
            if dryrun:
                # Modifying volume from gp2 to gp3.
                f.write(str(volume['VolumeId']) + " WOULD BE CONVERTED to GP3.. \n")
            if sendit:
                # Modifying volume from gp2 to gp3.
                ec2_client.modify_volume(VolumeId=volume['VolumeId'], VolumeType='gp3')
                # Writing information to file.
                f.write(str(volume['VolumeId']) + " converting to GP3.. \n")
            
            count += 1

        if dryrun:
            # Writing to file how many volumes were modified
            f.write("\n\n###########################################################\n"+ str(count) + " volumes would be modified.\n###########################################################")
        if sendit:
            f.write("\n\n###########################################################\n"+ str(count) + " volumes modified.\n###########################################################")
    
    # Closing file.
    f.close()



if __name__ == "__main__":
    dryrun = False
    sendit = False
    parser = argparse.ArgumentParser(description='Convert gp2 ebs volumes to gp3 ebs volumes.')
    parser.add_argument('-d', "--dryrun", dest='dryrun', action='store_true',
                        help='Dry run the script, not changing or modifying anything in AWS.')
    parser.add_argument('-s', "--sendit", dest='sendit', action='store_true',
                        help='Run the script, upgrading the gp2 volumes to gp3 in AWS. Full send.')

    args = parser.parse_args()
    if args.dryrun and args.sendit:
        print("Don\'t use both arguments.... ")
        sys.exit()
    elif not args.dryrun and not args.sendit:
        parser.print_help()
        sys.exit()
    elif args.dryrun and not args.sendit:
        dryrun = True
    elif args.sendit and not args.dryrun:
        val = input("Sending it! Are you sure? (y/n)")
        if val == "n":
            print("Good thing I had this check... Exiting...")
            sys.exit()
        if val != "y":
            print("You must enter 'y' or 'n'. Try again.")
            sys.exit()
        sendit = True
    main(sendit, dryrun)