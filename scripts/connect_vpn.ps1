# Enhanced VPN connection script
param(
    [string]$VPNName = "MyVPN",
    [int]$MaxRetries = 3,
    [int]$RetryDelay = 5
)

function Test-VPNConnection {
    param([string]$Name)
    $vpn = Get-VpnConnection -Name $Name -ErrorAction SilentlyContinue
    return ($vpn -and $vpn.ConnectionStatus -eq "Connected")
}

# Check if already connected
if (Test-VPNConnection -Name $VPNName) {
    Write-Host "VPN '$VPNName' is already connected"
    exit 0
}

# Attempt connection with retries
for ($i = 1; $i -le $MaxRetries; $i++) {
    Write-Host "Attempting VPN connection (attempt $i/$MaxRetries)..."
    
    try {
        rasdial $VPNName
        
        Start-Sleep -Seconds 3
        
        if (Test-VPNConnection -Name $VPNName) {
            Write-Host "VPN connected successfully"
            exit 0
        }
    }
    catch {
        Write-Host "Connection attempt failed: $_"
    }
    
    if ($i -lt $MaxRetries) {
        Write-Host "Retrying in $RetryDelay seconds..."
        Start-Sleep -Seconds $RetryDelay
    }
}

Write-Error "Failed to connect to VPN after $MaxRetries attempts"
exit 1
