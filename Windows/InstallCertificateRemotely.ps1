# Populate array with items from D:\Servers.txt
$Servers = Get-Content ".\Servers.txt"

# BEFORE RUNNING, COPY AND PASTE THE $CertTumbprint VALUE INTO NOTEPAD++ AND CONVERT TO ANSI. MAKE SURE THERE ARE NO ODD CHARACTERS.
#$CertThumbprint = "fc760f7550714b22a9049a0873dbac29"
#$CertFileName = 'certificate.pfx'

$CertThumbprint = Read-Host -Prompt 'Enter the NEW Certificate Thumbprint'
$CertFileName = Read-Host -Prompt 'Enter the Certificate File Name (Must be located in D:\Install_Files\)'

# MODIFY THIS LINE TO REFLECT APPROPRIATE YEARS
$CertFriendlyName = '*.website.com 2022-2024'

# Certthumbprint can be auto-generated if the same certificate is installed on the host machine.
#$CertThumbprint = (Get-ChildItem -Path Cert:\LocalMachine\My | Where-Object {$_.Subject -match "dsicloud.com"}).Thumbprint;

# NOTE: Enter the location of the certificate file on the HOST machine. This will be copied to the same directory on the target server.
$CertFilePath = 'D:\Install_Files\' + $CertFileName
$UNCPath = $CertFilePath -replace ':','$'

# Prompt for certificate password
$CertPwd = Get-Credential -UserName 'Enter Certificate Password below' -Message 'Enter Certificate Password below'

# Loop through Servers array
ForEach ($Server in $Servers) {

    # Check to see if cretificte exists on remote machine. 
    if ( (Test-Path "\\$Server\$UNCPath") -ne $true ) {
        Write-Output "Copying Certificate to \\$Server\$UNCPath"
        Copy-Item -Path $CertFilePath -Destination \\$Server\$UNCPath
    } else {
        Write-Output "\\$Server\$UNCPath already exists. Skipping Copy."
    }

    # All commands below this point will execute remotely on each server in $Servers
    Invoke-Command -ComputerName $Server -Scriptblock {

        Import-PFXCertificate -CertStoreLocation Cert:\LocalMachine\My -FilePath $using:CertFilePath -Password $using:CertPwd.Password
        # Set the friendly name of the certificate
        (Get-ChildItem -Path Cert:\LocalMachine\My\$using:CertThumbprint).FriendlyName = $using:CertFriendlyName

    }

}

# Variable cleanup
Get-Variable CertPwd | Remove-Variable

