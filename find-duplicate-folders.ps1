# Paths to the two directory trees
$TreeA = "C:\Users\senso\Large\Pictures\Pictures\GeneratedOrOriginalsUnsorted"
$TreeB = "C:\Users\senso\Large\Pictures\Originals"

# Get folder names (not full paths)
$FoldersA = Get-ChildItem -Path $TreeA -Directory -Recurse | Select-Object -ExpandProperty Name
$FoldersB = Get-ChildItem -Path $TreeB -Directory -Recurse | Select-Object -ExpandProperty Name

# Find duplicates
$Common = $FoldersA | Where-Object { $FoldersB -contains $_ } | Sort-Object -Unique

Write-Host "Common folder names:"
$Common
