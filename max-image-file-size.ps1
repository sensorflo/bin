$maxWidth  = 3840
$maxHeight = 2160

Get-ChildItem . -Filter *.jpg | ForEach-Object {
    $file = $_.FullName
    $temp = "$file.tmp.jpg"

    # Step 1 — Resize if larger than 4K resolution
    magick "$file" -resize "${maxWidth}x${maxHeight}>" "$temp"
    Move-Item -Force "$temp" "$file"

    # Step 2 — Iteratively compress until ≤3MB
    $quality = 95
    while ((Get-Item $file).Length -gt 3MB -and $quality -gt 10) {
        magick "$file" -quality $quality "$temp"
        Move-Item -Force "$temp" "$file"
        $quality -= 5
    }

    Write-Host "Processed $file -> final quality $quality"
}