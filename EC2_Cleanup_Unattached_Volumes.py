import boto3, datetime, argparse, sys, time

def main(dryrun, sendit):
    print(f'dryrun: {dryrun} | sendit: {sendit}')
    AWSAccountId = boto3.client('sts').get_caller_identity().get('Account')
    t = datetime.datetime.utcnow()
    filename = f'Output/[{AWSAccountId}]-{t.strftime("%m")}-{t.strftime("%d")}-{t.year}-{t.strftime("%H%M%S")}UTC_unattached_volume_information.txt'
    volumes_to_snapshot = list()
    count = 0
    storageUnusedGB = 0
    regions = ["us-east-1", "us-east-2", "us-west-1", "us-west-2"]
    # Create new blank "unattached_volume_information.txt file.
    f = open(filename, "x")
    f.write(f'\n###########################################################\nVolumes Not Attached to any EC2 Instance.\nAccount: {AWSAccountId}\n###########################################################')

    for region in regions:
        f.write(f'\n{region}:\n')
        # Initializing EC2 boto 3 client
        ec2_client = boto3.client('ec2', region_name=region)

        # Retrieving all volumes that are currently unattached from an EC2 instance.
        response = ec2_client.describe_volumes()
        # Iterating through EBS volumes
        for volume in response['Volumes']:
            # Looking for any volume where there are 0 attachments.
            if len(volume['Attachments']) < 1:
                f.write(f"{volume['VolumeId']} is not attached to any EC2 instance.\n")
                storageUnusedGB += volume['Size']
                if sendit == True:
                    take_snapshot(volume['VolumeId'], ec2_client, f)
                    delete_volume(volume['VolumeId'], ec2_client, f)
                count += 1
        # Making output file look more legible.
        f.write("\n\n")
    
    # Calculating wasted cost per month
    lostmoney = storageUnusedGB * 0.10
    # Ending output file.
    f.write(f'\n\n###########################################################\n{count} volumes unattached.\n${lostmoney} per month lost.\n###########################################################')
    
    # Closing file.
    f.close()

def take_snapshot(vid, ec2_client, f):
    try:
        f.write(f"Taking snapshot for volume: {vid}")
        snapshot = ec2_client.create_snapshot(
            Description=f'Automated Snapshot of unattached volume for AWS Cleanup',
            VolumeId=vid
            )  
        print(snapshot['SnapshotId'])         
    except Exception as e:
        f.write(f"snapshot for volumeid: {vid} failed\n")
    waiter = ec2_client.get_waiter('snapshot_completed')
    waiter.wait(
       SnapshotIds=[snapshot['SnapshotId']],
       WaiterConfig={'Delay' : 5, 'MaxAttempts' : 1440}    
       )

def delete_volume(vid, ec2_client, f):
    deleteVolume = ec2_client.delete_volume(
    VolumeId=vid
    )
    f.write(f'Deleted volume: {vid}\n')

if __name__ == "__main__":
    dryrun = False
    sendit = False
    parser = argparse.ArgumentParser(description='Iterate through regions to find unattached volumes.')
    parser.add_argument('-d', "--dryrun", dest='dryrun', action='store_true',
                        help='Dry run the script, finding unattached ebs volumes in AWS. No changes made.')
    parser.add_argument('-s', "--sendit", dest='sendit', action='store_true',
                        help='Run the script, taking snapshot of unattached ebs volumes. Full send.')
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
    main(dryrun, sendit)
