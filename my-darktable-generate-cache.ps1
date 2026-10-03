param(
    [Parameter(Mandatory=$true)]
    [int]$MinImgId,

    [Parameter(Mandatory=$true)]
    [int]$MaxImgId
)

# 8
$proc = Start-Process -FilePath "darktable-generate-cache" `
    -ArgumentList "--min-mip", "0",
                  "--max-mip", "8",
                  "--min-imgid", $MinImgId,
                  "--max-imgid", $MaxImgId `
    -WindowStyle Normal -PassThru

$proc.PriorityClass = 'High'
