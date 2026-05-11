param(
    [string]$HostName = "vulnshop.local",
    [string]$IpAddress = "127.0.0.1"
)

New-Item -ItemType Directory -Force -Path "certs" | Out-Null

openssl req -x509 -nodes -days 30 -newkey rsa:2048 `
    -keyout certs/privkey.pem `
    -out certs/fullchain.pem `
    -subj "/CN=$HostName" `
    -addext "subjectAltName=DNS:$HostName,IP:$IpAddress"

Write-Host "Created certs/fullchain.pem and certs/privkey.pem for $HostName / $IpAddress"
