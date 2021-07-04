## Grab Instance ID Tags that contain the string "Current"

`` aws ec2 describe-instances --region us-east-1 --query 'Reservations[].Instances[].Tags[?Key==`Name`].Value[]' --filter Name=tag:Name,Values=*Current* --output text ``

## Grab instance ID tag by IP

`` aws ec2 describe-instances --query 'Reservations[].Instances[].Tags[?Key==`Name`].Value[]' --filter "Name=network-interface.addresses.association.public-ip,Values=34.194.57.136" --region us-east-1 --output text ``

## Grab PRIVATE IP Address by instance ID tag

`aws ec2 describe-instances --region us-east-1 --instance-id 'i-0e8e8a4dcc5ac2911' --query 'Reservations[].Instances[].PrivateIpAddress' --output text`

#### Convert to Windows Host Name in PowerShell.

May be unnessecary, using -ComputerName in PS scripts will still resolve by IP, and depending on network configuration, may actually perform better.

> \[System.Net.Dns\]::GetHostbyAddress(\$AWS_PRIVATE_IP_ADDRESS).HostName

## Create table of all instances in a region

`aws ec2 describe-instances --region ap-southeast-2 --query "Reservations[*].Instances[*].{name: Tags[?Key=='Name'] | [0].Value, IP: PublicIpAddress, ID: InstanceId}" --filter "Name=tag:Name,Values=MEP*" --output table`

## Pull Instance Name based on public IP. Assign to Variable

`` aws ec2 describe-instances --query 'Reservations[].Instances[].Tags[?Key==`Name`].Value[]' --filter "Name=network-interface.addresses.association.public-ip,Values=54.85.171.144" --region us-east-1 --output text ``

## Get Attached ELBs by Instance Id

`` aws elb describe-load-balancers --output text --query 'LoadBalancerDescriptions[?Instances[?InstanceId==`i-0c59e7e32c051d479`]].[LoadBalancerName]' ``

## Get Attached Instance Ids by ELB Name

`aws elb describe-load-balancers --load-balancer-name MEP90-PRD --query "LoadBalancerDescriptions[*].Instances[*].[InstanceId]" --output table`

## Get Availability Zones by ELB Name

`aws elb describe-load-balancers --load-balancer-name MEP90-PRD --query "LoadBalancerDescriptions[*].[AvailabilityZones]" --output table`
