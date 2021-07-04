$ErrorActionPreference = "Stop"

$StringGuid = '{'+[guid]::NewGuid().ToString()+'}'

# Populate array with items from D:\Servers.txt
$Servers = Get-Content ".\Servers.txt"

$oldCertHash = Read-Host -Prompt 'Input the OLD certificate Hash'
$newCertHash = Read-Host -Prompt 'Input the NEW certificate Hash'

ForEach ($server in $Servers) {

    Invoke-Command -ComputerName $server -ScriptBlock {

        # Verify certificates exist on each server before taking further action.
        If (!(Get-ChildItem -Path Cert:\LocalMachine\My\$using:oldCertHash | Select-Object -ExpandProperty Thumbprint)) {
            Write-Warning "OLD Cert does not exist on $using:server! Stopping script."
        }

        If (!(Get-ChildItem -Path Cert:\LocalMachine\My\$using:newCertHash | Select-Object -ExpandProperty Thumbprint)) {
            Write-Warning "NEW Cert does not exist on $using:server! Stopping script."
        }
    }
}

ForEach ($server in $Servers) {

    Invoke-Command -ComputerName $server -ScriptBlock {

        # Note: The output of the 'netsh' command is not a powershell object, rather a string. It must be manipulated and parsed into objects we can work with.
        $netshResult = (netsh http show sslcert).replace('IP:port','Port').replace('0.0.0.0:','') | select -Skip 4
        $result = @{}

        $netshObject = New-Object psobject -Property @{
            IPPort = $Null
            CertHash = $Null
        } 
        
        $netshResult = $netshResult | Select-String : 
        $i = 0
        
        While ($i -lt $netshResult.Length) {
            $line = $netshResult[$i]
            $line = $line -split(":")
            $line[0] = $line[0].trim()
            $line[1] = $line[1].trim()
            $result.$($line[0]) += "$($line[1])`n" 
            $i++
        }

        # Copy results to string within netshObject
        $netshObject.IPPort = $result.'Port'
        $netshObject.CertHash = $result.'Certificate Hash'

        # Copy netshObject into separate arrays
        $boundPorts = ($netshObject.IPPort).split("`n")
        $boundPorts = $boundPorts | ForEach-Object {"0.0.0.0:$_"}
        $hashes = ($netshObject.CertHash).split("`n")

		# Finally, loop through the list of port bindings and replace the old certificate with the new one 
        $j = 0
		
        ForEach ($port in $boundPorts) {

            if ($hashes[$j] -eq $using:oldCertHash) {
                netsh http delete sslcert ipport=$port
                netsh http add sslcert ipport=$port certhash=$using:newCertHash appid=$using:StringGuid
            }
            $j++
        }

    }

}
