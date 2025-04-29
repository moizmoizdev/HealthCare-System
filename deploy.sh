#!/bin/bash

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and pip
sudo apt-get install -y python3 python3-pip python3-venv

# Install MySQL
sudo apt-get install -y mysql-server

# Install Nginx
sudo apt-get install -y nginx

# Create project directory
sudo mkdir -p /var/www/healthcare
sudo chown $USER:$USER /var/www/healthcare

# Create virtual environment
cd /var/www/healthcare
python3 -m venv venv
source venv/bin/activate

# Install project dependencies
pip install -r requirements.txt

# Configure MySQL
sudo mysql -e "CREATE DATABASE IF NOT EXISTS healthnetstorage;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'zero'@'localhost' IDENTIFIED BY 'UW5KZgLBZmFrDGh';"
sudo mysql -e "GRANT ALL PRIVILEGES ON healthnetstorage.* TO 'zero'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# Configure Nginx
sudo tee /etc/nginx/sites-available/healthcare << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/healthcare /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Create systemd service
sudo tee /etc/systemd/system/healthcare.service << EOF
[Unit]
Description=Healthcare Management System
After=network.target

[Service]
User=$USER
WorkingDirectory=/var/www/healthcare
Environment="PATH=/var/www/healthcare/venv/bin"
ExecStart=/var/www/healthcare/venv/bin/python api/app.py

[Install]
WantedBy=multi-user.target
EOF

# Start the service
sudo systemctl daemon-reload
sudo systemctl start healthcare
sudo systemctl enable healthcare 