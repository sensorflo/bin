# Set your folders
$folderA = "C:\Users\senso\Large\Pictures\Pictures\new\party\Baile Leon II 2026"   # contains .xmp files
$folderB = "E:\Pictures-already-on-backup-disc\Baile Leon II 2026"   # contains .arw files

# Get basenames of all .xmp files in folder A
$xmpNames = Get-ChildItem -Path $folderA -Filter *.xmp |
    Select-Object -ExpandProperty BaseName

# Copy matching .arw files from folder B into folder A
foreach ($name in $xmpNames) {
    $source = Join-Path $folderB "$name.arw"
    if (Test-Path $source) {
        Copy-Item $source -Destination $folderA
    }
}