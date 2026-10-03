$LocalFolder = "C:\photos\foo\bar"
$RemoteFolder = "/wp-content/uploads/foo/bar"

$FtpHost = "ftp.yourdomain.ch"
$FtpUser = "yourftpuser"
$FtpPass = "yourftppassword"

$SshHost = "yourdomain.ch"
$SshUser = "yoursshuser"

Add-Type -Path "C:\Tools\WinSCP\WinSCPnet.dll" # Path to WinSCP .NET assembly

# FTP sync (mirror local → server)
# -------------------------------
$sessionOptions = New-Object WinSCP.SessionOptions -Property @{
    Protocol = [WinSCP.Protocol]::Ftp
    HostName = $FtpHost
    UserName = $FtpUser
    Password = $FtpPass
    FtpSecure = [WinSCP.FtpSecure]::None
}

$session = New-Object WinSCP.Session
$session.Open($sessionOptions)

$syncResult = $session.SynchronizeDirectories(
    [WinSCP.SynchronizationMode]::Remote,
    $LocalFolder,
    $RemoteFolder,
    $False
)

if (!$syncResult.IsSuccess) {
    Write-Host "FTP sync FAILED."
    exit 1
}

$session.Dispose()

# Import new files
# -------------------------------
ssh $SshUser@$SshHost "wp media import '$RemoteFolder/*.jpg' --skip-copy"

# Update modified files
# -------------------------------
ssh $SshUser@$SshHost "wp media import '$RemoteFolder/*.jpg' --skip-copy --update"

# Delete remvoed files
# -------------------------------
$DeleteScript = @"
wp media list --fields=ID,file --format=csv | grep 'foo/bar' | while IFS=, read id file; do
  if [ ! -f "\$file" ]; then
    echo "Deleting missing file: \$id (\$file)"
    wp media delete \$id --force
  fi
done
"@

ssh $SshUser@$SshHost $DeleteScript

# Regenerate thumbnails
# -------------------------------
$RegenScript = @"
IDS=\$(wp media list --fields=ID,file --format=csv | grep 'foo/bar' | cut -d, -f1)
if [ ! -z "\$IDS" ]; then
  wp media regenerate \$IDS --yes
fi
"@

ssh $SshUser@$SshHost $RegenScript
