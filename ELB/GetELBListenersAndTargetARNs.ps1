$LoadBalArn = Read-Host -Prompt "Input the Load Balancer ARN"

$ListenerArns = aws elbv2 describe-target-groups --load-balancer-arn $LoadBalArn --query "TargetGroups[].TargetGroupArn" --output json | ConvertFrom-Json

#Get Listener Arns
ForEach ($listener in $ListenerArns) {

    Write-Output "Listener: $listener"

    #Get Registered Target ARNs
    $TargetArns = aws elbv2 describe-target-health --target-group-arn $listener --query 'TargetHealthDescriptions[*].Target.Id' --output json | ConvertFrom-Json
   
    ForEach ($targetArn in $TargetArns) {
        
        #Write Targets
        Write-Output "Target Arn: $targetArn"
    }
}