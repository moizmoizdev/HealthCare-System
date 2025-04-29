# Get droplet IP
$droplet = doctl compute droplet list --format "ID,Name,PublicIPv4" | Select-String "healthcare-app"
$ip = ($droplet -split '\s+')[2]

# Create SSH key if not exists
if (-not (Test-Path ~/.ssh/id_rsa)) {
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N '""'
}

# Copy SSH key to droplet
$sshKey = Get-Content ~/.ssh/id_rsa.pub
doctl compute ssh-key create healthcare-key --public-key $sshKey

# Copy project files to droplet
scp -r ./* root@$ip:/var/www/healthcare/

# Execute deployment script on droplet
ssh root@$ip "bash /var/www/healthcare/deploy.sh" 