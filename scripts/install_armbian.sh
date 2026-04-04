#!/bin/bash
set -e

echo "🚀 Installation de FlashNode-AI sur Armbian (Rock 5C)..."

# 1. Update and install dependencies
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip python3-venv python3-gpiod \
    libgpiod-dev libgpiod2 gpiod \
    openocd gdb-multiarch \
    libusb-1.0-0-dev cmake git build-essential pkg-config npm

# 2. Compile picotool
if ! command -v picotool &> /dev/null; then
    echo "📦 Compilation de picotool..."
    cd /tmp
    git clone https://github.com/raspberrypi/picotool.git
    cd picotool && mkdir build && cd build
    cmake .. && make -j$(nproc) && sudo make install
    cd ~
fi

# 3. Setup UDEV Rules
echo "🔧 Configuration des règles UDEV (ESP32 & RP2040)..."
sudo usermod -aG plugdev,dialout $USER

echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="2e8a", MODE="0666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/99-rp2040.rules
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="10c4", MODE="0666", GROUP="dialout"' | sudo tee /etc/udev/rules.d/99-esp32prog.rules

sudo udevadm control --reload-rules
sudo udevadm trigger

# 4. Setup Project Structure
PROJECT_DIR="/opt/flashnode"
echo "📁 Préparation de $PROJECT_DIR..."
sudo mkdir -p $PROJECT_DIR/vault $PROJECT_DIR/data $PROJECT_DIR/config
sudo chown -R $USER:$USER $PROJECT_DIR

# 5. Python Environment
echo "🐍 Initialisation de l'environnement Python..."
cd $(dirname "$0")/..
python3 -m venv $PROJECT_DIR/venv
source $PROJECT_DIR/venv/bin/activate
pip install -r backend/requirements.txt

# 6. Build Frontend
echo "🌐 Compilation du Frontend Vue.js..."
cd frontend
npm install
npm run build
cp -r dist/* $PROJECT_DIR/
cd ..

# 7. Install systemd service
echo "🏗️ Installation du service systemd..."
sudo cp scripts/flashnode.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable flashnode.service

echo "✅ Installation terminée ! Vous pouvez lancer le service avec : sudo systemctl start flashnode"
