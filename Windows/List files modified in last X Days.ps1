# <FILE LOCATION> must be changed.
# Adjust the numeric value within the .AddDays function. Must be a negative value.

Get-ChildItem "<FILE LOCATION>\*.txt" -File -Recurse | Where{$_.LastWriteTime -gt (Get-Date).AddDays(-1)}