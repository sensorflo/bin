$xRoot = "C:\Users\senso\Large\Pictures\Pictures\GeneratedOrOriginalsUnsorted"
$yRoot = "C:\Users\senso\Large\Pictures\Originals"

# Collect filename stems from Y into a hash set
$stemsInY = @{}
Get-ChildItem -Path $yRoot -Recurse -File | ForEach-Object {
    $stemsInY[$_.BaseName] = $true
}

# Walk X and output relative paths for files whose stem also occurs in Y
Get-ChildItem -Path $xRoot -Recurse -File | ForEach-Object {
    if ($stemsInY.ContainsKey($_.BaseName)) {
        $relativePath = $_.FullName.Substring($xRoot.Length).TrimStart('\','/')
        Write-Output $relativePath
    }
}