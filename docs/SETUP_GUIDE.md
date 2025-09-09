# Complete VPS Setup Guide

This guide covers the complete production deployment of Universal MIRO Server on a VPS with SSL/HTTPS support.

## Prerequisites

- Ubuntu 20.04+ VPS (DigitalOcean, Linode, AWS EC2, etc.)
- Domain name or DuckDNS subdomain
- MIRO account with API access
- Root or sudo access to VPS

## Part 1: Initial VPS Setup

### Update System
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y python3-pip python3-venv git curl wget \
    build-essential nginx certbot python3-certbot-nginx

# Install uv (modern Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Part 2: Install Universal MIRO Server

### Create Directory Structure
```bash
# Create directory structure
mkdir -p ~/mcp-servers/miro_board-mcp
cd ~/mcp-servers/miro_board-mcp

# Clone repository (or copy files)
git clone https://github.com/alldevice/miro-board-mcp .
# OR manually copy your files here
```

### Setup Python Environment
```bash
# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install fastapi uvicorn httpx python-dotenv aiohttp pydantic
```

## Part 3: Environment Configuration

### Create Environment File
```bash
cd ~/mcp-servers/miro_board-mcp
cat > .env << EOF
# MIRO API Configuration (REQUIRED)
MIRO_ACCESS_TOKEN=your-miro-access-token-here

# Server Configuration
PORT=8001
LOG_LEVEL=INFO
EOF

# Secure the file
chmod 600 .env
```

### Get MIRO Access Token
1. Go to https://miro.com/app/settings/user-profile/apps
2. Create a new app or use existing
3. Copy the access token
4. Replace `your-miro-access-token-here` in `.env`

## Part 4: Quick Verification

```bash
cd ~/mcp-servers/miro_board-mcp
source .venv/bin/activate

# Test dependencies
python -c "import fastapi, uvicorn, httpx; print('✅ Dependencies OK')"

# Test configuration
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
if os.getenv('MIRO_ACCESS_TOKEN') == 'your-miro-access-token-here':
    print('⚠️ WARNING: Update MIRO_ACCESS_TOKEN in .env')
else:
    print('✅ MIRO_ACCESS_TOKEN configured')
"
```

## Part 5: DuckDNS Setup (Optional - Free Domain)

If you don't have a domain, use DuckDNS for free:

```bash
mkdir -p ~/duckdns
cd ~/duckdns

# Create update script
cat > duck.sh << 'EOF'
#!/bin/bash
TOKEN="your-duckdns-token-here"
DOMAIN="miromcp"
echo url="https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip=" | curl -k -o ~/duckdns/duck.log -K -
EOF

chmod 700 duck.sh
./duck.sh

# Add to crontab for auto-update
(crontab -l 2>/dev/null; echo "*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1") | crontab -
```

Replace `your-duckdns-token-here` with token from https://www.duckdns.org

## Part 6: Nginx Configuration

### Create Nginx Config
```bash
sudo tee /etc/nginx/conf.d/miro-mcp.conf << 'EOF'
server {
    listen 80;
    server_name miromcp.duckdns.org;  # Replace with your domain

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        
        # SSE specific settings
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_read_timeout 86400;
    }
}
EOF

# Test and reload Nginx
sudo nginx -t
sudo systemctl reload nginx
```

## Part 7: SSL Certificate Setup

```bash
# Get SSL certificate
sudo certbot --nginx -d miromcp.duckdns.org \
    --non-interactive \
    --agree-tos \
    --email your-email@example.com \
    --redirect

# Verify certificate
sudo certbot certificates

# Test auto-renewal
sudo certbot renew --dry-run
```

## Part 8: Systemd Service

### Create Service File
```bash
sudo tee /etc/systemd/system/miro-mcp.service << EOF
[Unit]
Description=Universal Miro Server (MCP + Filter)
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/mcp-servers/miro_board-mcp
Environment="PATH=/home/$USER/mcp-servers/miro_board-mcp/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/$USER/mcp-servers/miro_board-mcp/.venv/bin/python /home/$USER/mcp-servers/miro_board-mcp/miro_mcp_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable miro-mcp
sudo systemctl start miro-mcp

# Check status
sudo systemctl status miro-mcp
```

## Part 9: Firewall Configuration

```bash
# Allow necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable
```

## Part 10: Testing

### Test Local Server
```bash
curl http://localhost:8001/health
```

### Test HTTPS Endpoints
```bash
# Health check
curl https://miromcp.duckdns.org/health

# Service info
curl https://miromcp.duckdns.org/
```

### Test with Real MIRO Board
```bash
# Get your board ID from MIRO URL
curl https://miromcp.duckdns.org/api/miro/board/YOUR_BOARD_ID
```

## Part 11: Connect Services

### Claude.ai Setup
1. Go to Claude.ai web interface
2. Click integrations/connectors
3. Select "Custom Connector" or "MCP Server"
4. Enter: `https://miromcp.duckdns.org/sse`
5. Click "Connect"

### OpenWebUI Setup
1. Go to Settings → Filters
2. Add new filter with code from `miro_mcp_filter.py`
3. Set server URL to `https://miromcp.duckdns.org`
4. Enable for your model

## Monitoring & Maintenance

### View Logs
```bash
# Service logs
sudo journalctl -u miro-mcp -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Restart Services
```bash
sudo systemctl restart miro-mcp
sudo systemctl restart nginx
```

### Update Server
```bash
cd ~/mcp-servers/miro_board-mcp
git pull  # If using git
source .venv/bin/activate
uv pip install --upgrade -r requirements.txt
sudo systemctl restart miro-mcp
```

## Security Best Practices

1. **Secure .env file**: `chmod 600 .env`
2. **Regular updates**: `sudo apt update && sudo apt upgrade`
3. **Monitor logs**: Check for unusual activity
4. **Backup configuration**: Keep copies of working configs
5. **Rate limiting**: Consider adding nginx rate limiting
6. **Fail2ban**: Install for brute force protection

## Troubleshooting

See [Troubleshooting Guide](TROUBLESHOOTING.md) for common issues and solutions.