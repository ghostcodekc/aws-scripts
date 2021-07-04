$Region = Read-Host -Prompt 'Input AWS region where the database resides (eg. us-east-1, us-west-2)'
$dbInstance = Read-Host -Prompt 'Input database instance identifier'
$LogDay = Read-Host -Prompt 'Input date you would like to retrieve logs from in this format yyyy-MM-dd (ex. 2020-05-01 for May 01, 2020)'
$slowquerypath = New-Item -ItemType Directory -Force -Path $env:USERPROFILE\Desktop\RDSLogs\$Region\$dbInstance\mysql-slowquery\$LogDay
$generallogpath = New-Item -ItemType Directory -Force -Path $env:USERPROFILE\Desktop\RDSLogs\$Region\$dbInstance\mysql-general\$LogDay

For ($i=23; $i -gt 0; $i--) {
    if ($i -ge 10) {
        Write-Host "Downloading log file: slowquery/mysql-slowquery.log.$LogDay.$i"
        aws rds download-db-log-file-portion --db-instance-identifier $dbInstance --log-file-name "slowquery/mysql-slowquery.log.$LogDay.$i" --output text > $slowquerypath\mysql-slowquery.log.$LogDay.$i --region $Region
        Write-Host "Downloading log file: slowquery/mysql-general.log.$LogDay.$i"
        aws rds download-db-log-file-portion --db-instance-identifier $dbInstance --log-file-name "general/mysql-general.log.$LogDay.$i" --output text > $generallogpath\mysql-general.log.$LogDay.$i --region $Region
    }
    elseif ($i -lt 10) {
        Write-Host "Downloading log file: slowquery/mysql-slowquery.log.$LogDay.0$i"
        aws rds download-db-log-file-portion --db-instance-identifier $dbInstance --log-file-name "slowquery/mysql-slowquery.log.$LogDay.0$i" --output text > $slowquerypath\mysql-slowquery.log.$LogDay.0$i --region $Region
        Write-Host "Downloading log file: slowquery/mysql-general.log.$LogDay.0$i"
        aws rds download-db-log-file-portion --db-instance-identifier $dbInstance --log-file-name "general/mysql-general.log.$LogDay.0$i" --output text > $generallogpath\mysql-general.log.$LogDay.0$i --region $Region
    }
    else { 
        Write-Host "Downloading log file: mysql-slowquery.log"
        aws rds download-db-log-file-portion --db-instance-identifier $dbInstance --log-file-name "slowquery/mysql-slowquery.log" --output text > $slowquerypath\slowquery.log --region $Region
        Write-Host "Downloading log file: mysql-general.log"
        aws rds download-db-log-file-portion --db-instance-identifier $dbInstance --log-file-name "general/mysql-general.log" --output text > $generallogpath\slowquery.log --region $Region
    }

}


Write-Host "Operation Complete. Please go to the following directory to view the log files: $env:USERPROFILE\Desktop\RDSLogs"