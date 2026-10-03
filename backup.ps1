#
# Ensure defender is turned off (or at least the process (restic.exe or restic_0.18.1_windows_amd64.exe) is excepted and the backup folder is excepted)
#################################

$Source = "C:\Users\Senso"
$Repo = "E:\Backup\restic-backup-dell-xps-15-home-folder"
$ExcludePattern1 = "Large\Pictures\Pictures\new\**\*.arw"
$ExcludePattern2 = "Large\Pictures\Pictures\new-old\**\*.arw"
$ExcludePattern2_2= "Large\Pictures\Temp\**\*.arw"
$ExcludePattern3 = "AppData\**"
$ExcludePattern4 = "CrossDevice\**"
$ExcludePattern5 = '$Recycle.Bin\**'
$ExcludePattern6 = "**\.git\**"
$ExcludePattern7 = "Large\Pictures\**\*.acr"
$ExcludePattern8 = "OneDrive\**"
$ExcludePattern9 = "Large\Pictures\Temp\**"
$ExcludePattern10 = "Downloads\**"
# !!!! first ensure destination exists, so we catch when another ext drive is mapped to E:
# !!!! SDXC Music/Videos etc
# !!!! lr preview folder ausklammern, und aus backup entfernen

if (-not (Test-Path $Repo)) {
    Write-Host "Initializing new restic repository at $Repo"
    & restic init `
		--repo $Repo `
		--insecure-no-password `
		--compression off
}

Write-Host "Starting backup of $Source ..."
& restic backup "$Source" `
    --repo $Repo `
    --iexclude="$ExcludePattern1" `
	--iexclude="$ExcludePattern2" `
	--iexclude="$ExcludePattern2_2" `
	--iexclude="$ExcludePattern3" `
	--iexclude="$ExcludePattern4" `
	--iexclude="$ExcludePattern5" `
	--iexclude="$ExcludePattern6" `
	--iexclude="$ExcludePattern7" `
	--iexclude="$ExcludePattern8" `
	--iexclude="$ExcludePattern9" `
	--iexclude="$ExcludePattern10" `
	--insecure-no-password `
	--compression off `
	--verbose

# & restic forget --repo "E:\Backup\restic-backup-dell-xps-15-home-folder" --prune --keep-last 5 --keep-monthly 10 --verbose --insecure-no-password --dry-run

# & restic snapshots --insecure-no-password  --repo $Repo # Available snapshots

# rsync --dry-run -a --delete --link-dest="$LAST_SNAPSHOT" "$SRC" "$DEST_NEW_SNAPSHOT"

# after aborting a backup: restic prune --repo "E:\Backup\restic-backup-dell-xps-15-home-folder" --insecure-no-password

# restic -r "E:\Backup\restic-backup-dell-xps-15-home-folder" restore latest --target C:\restored --include "C:\Users\senso\Large\Pictures\Pictures\new\party\Baile Leon II 2026" --dry-run --insecure-no-password