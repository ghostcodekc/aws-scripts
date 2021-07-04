# Recursively loop through a folder structure and check for duplicate files by comparing hash values.
# Duplicate file locations and names are printed to the console.

# Source: https://stackoverflow.com/questions/27066989/how-to-use-powershell-to-list-duplicate-files-in-a-folder-structure-that-exist-i
# Example 
    # $h=@{};$s=@{};gci 'C:\Files' -R -file -Filt *.ps1|%{if($h.ContainsKey($_.Name)){$s[$_.Name]=1}else{$h[$_.Name]=@()}$h[$_.Name]+=$_.FullName};$s.Keys|%{if ($h[$_]-like 'C:\Files\*'){$h[$_]}}

$h=@{};$s=@{};gci '<ROOT FOLDER>' -R -file -Filt *.<FILE TYPE>|%{if($h.ContainsKey($_.Name)){$s[$_.Name]=1}else{$h[$_.Name]=@()}$h[$_.Name]+=$_.FullName};$s.Keys|%{if ($h[$_]-like '<ROOT FOLDER>\*'){$h[$_]}}
