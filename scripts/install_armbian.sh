#!/bin/bash
# ============================================================
# FlashNode-AI — Installation script for Armbian Debian 13 (Trixie)
# Target: Radxa Rock 5C (RK3588S2)
# ============================================================
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[1;32m'
CYAN='\033[1;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${CYAN}[FlashNode]${NC} $1"; }
ok()   { echo -e "${GREEN}[  ✅  ]${NC} $1"; }
warn() { echo -e "${YELLOW}[  ⚠️  ]${NC} $1"; }

PROJECT_DIR="/opt/flashnode"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ============================================================
# 1. System dependencies (Debian 13 Trixie / Armbian)
# ============================================================
log "📦 Installation des dépendances système..."
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip python3-venv python3-gpiod \
    libgpiod-dev libgpiod2 gpiod \
    openocd gdb-multiarch \
    libusb-1.0-0-dev cmake git build-essential pkg-config \
    ca-certificates curl

# ============================================================
# 2. Node.js 20 LTS via NodeSource (Debian Trixie apt npm is too old)
# ============================================================
if ! command -v node &> /dev/null || [[ $(node -v | cut -d'.' -f1 | tr -d 'v') -lt 20 ]]; then
    log "📦 Installation de Node.js 20 via NodeSource..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi
ok "Node.js $(node -v)"

# ============================================================
# 3. esptool (ESP32 flashing tool)
# ============================================================
if ! command -v esptool.py &> /dev/null; then
    log "📦 Installation de esptool..."
    pip3 install --break-system-packages esptool
fi
ok "esptool installé"

# ============================================================
# 4. picotool (RP2040 flashing tool — requires Pico SDK)
# ============================================================
if ! command -v picotool &> /dev/null; then
    log "📦 Compilation de picotool..."
    cd /tmp
    git clone --depth 1 https://github.com/raspberrypi/pico-sdk.git
    git clone --depth 1 https://github.com/raspberrypi/picotool.git
    cd picotool && mkdir -p build && cd build
    cmake .. -DPICO_SDK_PATH=/tmp/pico-sdk
    make -j$(nproc)
    sudo make install
    cd / && rm -rf /tmp/picotool /tmp/pico-sdk
fi
ok "picotool installé: $(picotool version 2>/dev/null || echo 'OK')"

# ============================================================
# 5. UDEV rules (RP2040 + ESP32 USB permissions)
# ============================================================
log "🔧 Configuration des règles UDEV..."
sudo usermod -aG plugdev,dialout,gpio "$USER" 2>/dev/null || true

# RP2040 (Raspberry Pi)
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="2e8a", MODE="0666", GROUP="plugdev"' \
    | sudo tee /etc/udev/rules.d/99-rp2040.rules > /dev/null

# ESP32 (Silicon Labs CP210x / Espressif)
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="10c4", MODE="0666", GROUP="dialout"
SUBSYSTEM=="usb", ATTR{idVendor}=="303a", MODE="0666", GROUP="dialout"' \
    | sudo tee /etc/udev/rules.d/99-esp32.rules > /dev/null

# Raspberry Pi Debug Probe (CMSIS-DAP)
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="2e8a", ATTR{idProduct}=="000c", MODE="0666", GROUP="plugdev"' \
    | sudo tee /etc/udev/rules.d/99-debugprobe.rules > /dev/null

sudo udevadm control --reload-rules
sudo udevadm trigger
ok "Règles UDEV configurées"

# ============================================================
# 6. Project structure
# ============================================================
log "📁 Préparation de $PROJECT_DIR..."
sudo mkdir -p "$PROJECT_DIR"/{vault,data,config,backend}
sudo chown -R "$USER:$USER" "$PROJECT_DIR"

# ============================================================
# 7. Python virtual environment + backend
# ============================================================
log "🐍 Configuration de l'environnement Python..."
python3 -m venv "$PROJECT_DIR/venv"
source "$PROJECT_DIR/venv/bin/activate"

pip install --upgrade pip
pip install -r "$REPO_DIR/backend/requirements.txt"
pip install aiofiles  # Required for FastAPI StaticFiles

# Copy backend source
cp -r "$REPO_DIR/backend/"* "$PROJECT_DIR/backend/"

# Copy config
cp -r "$REPO_DIR/config/"* "$PROJECT_DIR/config/"

ok "Backend installé dans $PROJECT_DIR"

# ============================================================
# 8. Build & deploy Frontend
# ============================================================
log "🌐 Compilation du Frontend Vue.js..."
cd "$REPO_DIR/frontend"
npm install
npm run build

# Copy built frontend to project dir where FastAPI will serve it
cp -r dist "$PROJECT_DIR/frontend_dist"
ok "Frontend compilé et déployé"

# ============================================================
# 9. Create .env from example if not present
# ============================================================
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cp "$REPO_DIR/.env.example" "$PROJECT_DIR/.env"
    # Set production defaults
    sed -i 's/GPIO_BACKEND=mock/GPIO_BACKEND=libgpiod/' "$PROJECT_DIR/.env"
    log "📝 .env créé depuis .env.example (GPIO_BACKEND=libgpiod)"
fi

# ============================================================
# 10. Install systemd service
# ============================================================
log "🏗️ Installation du service systemd..."
sudo cp "$REPO_DIR/scripts/flashnode.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable flashnode.service
ok "Service systemd installé et activé"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ FlashNode-AI installé avec succès !${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Démarrer :  ${BOLD}sudo systemctl start flashnode${NC}"
echo -e "  Status :    ${BOLD}sudo systemctl status flashnode${NC}"
echo -e "  Logs :      ${BOLD}journalctl -u flashnode -f${NC}"
echo -e "  Dashboard : ${BOLD}http://$(hostname -I | awk '{print $1}'):8000${NC}"
echo ""
warn "Redémarrez votre session pour que les groupes (plugdev, dialout, gpio) prennent effet."
