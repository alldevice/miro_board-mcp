#!/bin/bash
# Automated installation script for VPS

set -e

echo "🚀 Universal MIRO Server - Automated Installation"
echo "================================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root"
   exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt install -y python3-pip python3-venv git curl wget \
    build-essential nginx certbot python3-certbot-nginx

# Install uv
echo "📦 Installing uv package manager..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p ~/mcp-servers/miro_board-mcp
cd ~/mcp-servers/miro_board-mcp

# Clone repository
echo "📥 Cloning repository..."
git clone https://github.com/alldevice/miro-board-mcp .

# Setup Python environment
echo "🐍 Setting up Python environment..."
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Create .env file
echo "⚙️ Creating configuration..."
cp .env.example .env

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your MIRO_ACCESS_TOKEN"
echo "   nano .env"
echo ""
echo "2. Run the server:"
echo "   cd ~/mcp-servers/miro_board-mcp"
echo "   source .venv/bin/activate"
echo "   python miro_mcp_server.py"
echo ""
echo "For production deployment with SSL, see docs/SETUP_GUIDE.md"