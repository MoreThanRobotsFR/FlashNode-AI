# 🚀 FlashNode-AI — Station de Programmation & Débogage Universelle

> Station de programmation, de débogage et de test matériel de niveau industriel basée sur un **Radxa Rock 5C (16 Go / Armbian)**, pilotable par interface web avancée, par ordinateur distant, et par Intelligence Artificielle via le protocole **MCP (Model Context Protocol)**.

---

## 📋 Table des Matières

1. [Vue d'ensemble](#-vue-densemble)
2. [Fonctionnalités](#-fonctionnalités)
3. [Architecture Système](#-architecture-système)
4. [Matériel Requis](#-matériel-requis)
5. [Interfaces Matérielles Supportées](#-interfaces-matérielles-supportées)
6. [GPIO — Rock 5C / Armbian](#-gpio--rock-5c--armbian)
7. [Contrôle des Rails d'Alimentation & Boot Forcé](#-contrôle-des-rails-dalimentation--boot-forcé)
8. [Stack Logicielle](#-stack-logicielle)
9. [Interface Web — Détail des Panneaux](#-interface-web--détail-des-panneaux)
10. [API REST — Endpoints](#-api-rest--endpoints)
11. [WebSockets — Temps Réel](#-websockets--temps-réel)
12. [Pipelines Multi-Puces](#-pipelines-multi-puces)
13. [Firmware Vault](#-firmware-vault)
14. [Intégration IA — Serveur MCP](#-intégration-ia--serveur-mcp)
15. [Structure du Projet](#-structure-du-projet)
16. [Déploiement sur Armbian](#-déploiement-sur-armbian)
17. [Configuration Système](#-configuration-système)
18. [Roadmap](#-roadmap)

---

## 🎯 Vue d'ensemble

**FlashNode-AI** transforme un Radxa Rock 5C en une station de programmation centralisée et intelligente. Elle élimine toute intervention manuelle lors du développement ou de la production de cartes électroniques embarquant un ou plusieurs microcontrôleurs.

### Plateforme

| Paramètre | Valeur |
|-----------|--------|
| **SBC** | Radxa Rock 5C |
| **SoC** | Rockchip RK3588S2 (4× Cortex-A76 @ 2.4 GHz + 4× Cortex-A55) |
| **RAM** | 16 Go LPDDR4x |
| **OS** | Armbian (base Debian/Ubuntu, kernel 6.x) |
| **GPIO** | 40 broches (compatible Raspberry Pi form factor) |
| **GPIO Library** | `libgpiod` + `python3-gpiod` |

### Cas d'usage typiques

- **Développement** : Flasher une cible depuis son bureau, lire les logs en direct, itérer sans toucher à la carte.
- **Production** : Programmer en séquence toutes les puces d'un PCB via un pipeline défini, valider automatiquement le démarrage.
- **PCB Multi-puces** : Flasher un RP2040 (MCU principal) + ESP32 (coprocesseur WiFi/BLE) sur le même board en une seule opération.
- **Débogage IA** : Demander à un LLM de compiler, flasher, analyser les logs et proposer des corrections, sans intervention humaine.

---

## ✨ Fonctionnalités

### Programmation Multi-Cibles
- **RP2040** : via `picotool` (USB / BOOTSEL) **ou** `OpenOCD` (SWD / Debug Probe)
- **ESP32** : via `esptool.py` en connexion USB directe **ou** via ESP32 Programmer V2

### Contrôle Matériel Avancé (GPIO)
- **Mise en mode BOOT du RP2040** en un clic : impulsion BOOTSEL + RESET via GPIO
- **Mise en mode Download de l'ESP32** en un clic : GPIO0 forcé à la masse + pulse EN
- **Contrôle du rail 5V** (alimentation principale du PCB cible) via MOSFET/relais GPIO
- **Contrôle du rail 3.3V** (alimentation MCUs) via MOSFET/relais GPIO
- **Reset matériel** de chaque puce individuellement

### Interface Web Avancée (SPA)
- Live Device Tree temps réel (événements `udev` via WebSocket)
- **Boot Control Panel** : boutons dédiés BOOTSEL (RP2040) et Download Mode (ESP32)
- **Power Rail Dashboard** : contrôle visuel des rails 5V et 3.3V avec état en temps réel
- Pipeline Studio : éditeur visuel de séquences avec conditions de succès
- Firmware Vault : gestionnaire de binaires (MD5 / SHA256)
- Terminaux multiplexés **xterm.js** : vraies consoles ANSI multi-onglets
- Moniteurs séries multi-ports intégrés au navigateur
- Barre de progression de flashage en direct
- Historique horodaté de toutes les opérations (SQLite)
- Dashboard de statut système (CPU, RAM, température Rock 5C)

### Orchestration Multi-Puces (Pipelines)
- Séquences de flashage pour PCB RP2040 + ESP32 sur le même board
- Actions : flash, verify, erase, power_cycle, gpio_pulse, gpio_sequence, monitor_serial, delay
- Conditions de validation (attente chaîne UART, timeout, retry)
- Sauvegarde et réutilisation des pipelines au format JSON

### Pilotage Distant & IA
- Contrôle complet via API REST depuis n'importe quel ordinateur
- Serveur MCP natif pour pilotage par LLM (Claude, etc.)
- Documentation OpenAPI auto-générée (Swagger UI intégré sur `/docs`)

---

## 🏗️ Architecture Système

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         RÉSEAU LOCAL / INTERNET                          │
│                                                                          │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────────────────┐  │
│  │  Navigateur │   │  PC Distant  │   │   Agent IA (Claude / autre)  │  │
│  │    Web SPA  │   │  (API REST)  │   │   Client MCP                 │  │
│  └──────┬──────┘   └──────┬───────┘   └─────────────┬────────────────┘  │
│         │  HTTP/WS        │  HTTP REST               │  MCP Protocol     │
└─────────┼─────────────────┼──────────────────────────┼──────────────────┘
          ▼                 ▼                          ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      RADXA ROCK 5C — Armbian                             │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                        FastAPI Backend                             │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐   │  │
│  │  │   REST API   │  │  WebSocket   │  │     MCP Server         │   │  │
│  │  │  /api/v1/*   │  │  Manager     │  │  (Tools pour LLM)      │   │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────┬─────────────┘   │  │
│  │         └─────────────────┴──────────────────────┘                 │  │
│  │  ┌─────────────────────────────────────────────────────────────┐   │  │
│  │  │                   Couche Orchestration                      │   │  │
│  │  │  ┌──────────────┐  ┌────────────────┐  ┌─────────────────┐ │   │  │
│  │  │  │   Flasher    │  │  Pipeline      │  │  GPIO           │ │   │  │
│  │  │  │   Manager    │  │  Engine        │  │  Controller     │ │   │  │
│  │  │  │  (esptool /  │  │  (séquenceur   │  │  (libgpiod)     │ │   │  │
│  │  │  │  picotool /  │  │   multi-étapes)│  │  Rails + Boot   │ │   │  │
│  │  │  │  openocd)    │  └────────────────┘  └─────────────────┘ │   │  │
│  │  │  └──────────────┘                                           │   │  │
│  │  └─────────────────────────────────────────────────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌──────────────────────┐   ┌────────────────────────────────────────┐   │
│  │   USB subsystem      │   │   GPIO 40-pin (libgpiod)               │   │
│  │   /dev/ttyUSB*       │   │   Rail 5V · Rail 3.3V                  │   │
│  │   /dev/ttyACM*       │   │   BOOTSEL (RP2040) · BOOT (ESP32)      │   │
│  │   /dev/bus/usb       │   │   RESET RP2040 · EN ESP32              │   │
│  └──────────┬───────────┘   └──────────────────┬─────────────────────┘   │
└─────────────┼────────────────────────────────────┼────────────────────────┘
              │ USB                                │ GPIO → Circuits de commande
              ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PCB CIBLE                                        │
│                                                                          │
│  ┌─────────────────────────────┐   ┌─────────────────────────────────┐  │
│  │          RP2040             │   │             ESP32                │  │
│  │  (MCU Principal)            │   │  (Coprocesseur WiFi / BLE)      │  │
│  │                             │   │                                  │  │
│  │  SWDIO ←── Debug Probe      │   │  TX/RX ←── ESP-Prog V2          │  │
│  │  SWDCLK ←── Debug Probe     │   │  GPIO0 ←── GPIO Rock 5C         │  │
│  │  USB ←── USB direct         │   │  EN ←──── GPIO Rock 5C          │  │
│  │  BOOTSEL ←── GPIO Rock 5C   │   │  USB ←── USB direct             │  │
│  │  RUN/RESET ←── GPIO Rock 5C │   │                                  │  │
│  └─────────────────────────────┘   └─────────────────────────────────┘  │
│                                                                           │
│  VCC_5V ←── MOSFET (GPIO Rock 5C)    VCC_3V3 ←── MOSFET (GPIO Rock 5C) │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Matériel Requis

### Plateforme principale
| Composant | Détail |
|-----------|--------|
| **Radxa Rock 5C** | 16 Go RAM, RK3588S2 |
| **Alimentation** | USB-C 5V/4A minimum |
| **Stockage** | eMMC 32 Go **ou** microSD 32 Go A1/A2 |
| **Hub USB alimenté** | Obligatoire (4 ports min.) pour sondes + programmateurs simultanés |

### Programmateurs
| Programmateur | Cible | Interface |
|---------------|-------|-----------|
| **Raspberry Pi Debug Probe** | RP2040 | SWD (CMSIS-DAP) |
| **ESP32 Programmer V2** | ESP32 | UART + auto-reset (DTR/RTS) |

### Circuits de commande GPIO
| Composant | Qté | Rôle |
|-----------|-----|------|
| **MOSFET N-channel** (IRLZ44N ou BSS138) | 4× | Commutation rails 5V / 3.3V et signaux BOOT/RESET |
| **Résistance pull-up 10 kΩ** | 4× | Protection entrées MCU |
| **Résistance de gate 100 Ω** | 4× | Limitation courant GPIO Rock 5C |
| **Diode de roue libre 1N4007** | 2× | Protection si relais utilisé |

> ⚠️ **Tension logique** : Les GPIO du Rock 5C sont en **3.3V, max 3.63V**. Ne jamais connecter directement à du 5V. Utiliser un MOSFET ou buffer logique pour commander des charges 5V.

---

## 🔌 Interfaces Matérielles Supportées

### RP2040 — Deux modes

#### Mode A : `picotool` (USB natif / BOOTSEL)
- Connexion USB directe sur le RP2040
- Nécessite le mode BOOTSEL (apparaît comme `RPI-RP2` Mass Storage)
- Commande : `picotool load -x firmware.uf2`
- Détection : `lsusb | grep "2e8a:0003"`
- **FlashNode-AI peut forcer BOOTSEL automatiquement via GPIO** (voir section GPIO)

#### Mode B : `OpenOCD` (SWD / Raspberry Pi Debug Probe)
- Connexion SWD : 3 fils (SWDIO, SWDCLK, GND)
- Flash à chaud, débogage GDB possible
- Commande générée dynamiquement :
  ```bash
  openocd -f interface/cmsis-dap.cfg \
          -f target/rp2040.cfg \
          -c "adapter speed 5000" \
          -c "program firmware.elf verify reset exit"
  ```
- Arguments personnalisables (vitesse SWD, scripts `.cfg` custom)

### ESP32 — Deux modes

#### Mode A : USB Direct (CDC/JTAG natif)
- Compatible ESP32-S2, S3, C3 avec USB natif
- Port : `/dev/ttyACM*`
- Commande : `esptool.py --port /dev/ttyACMx --chip auto flash_id`

#### Mode B : ESP32 Programmer V2
- Pont USB-UART avec gestion automatique DTR/RTS
- Port : `/dev/ttyUSB*`
- Commande :
  ```bash
  esptool.py --port /dev/ttyUSB0 --chip esp32 \
             --baud 921600 --before default_reset \
             --after hard_reset write_flash \
             -z --flash_mode dio --flash_freq 40m --flash_size detect \
             0x1000 firmware.bin
  ```

---

## ⚡ GPIO — Rock 5C / Armbian

### Différences clés vs Raspberry Pi

| Aspect | Raspberry Pi 4 | Radxa Rock 5C |
|--------|---------------|---------------|
| **Librairie** | `RPi.GPIO` | `libgpiod` + `python3-gpiod` |
| **Numérotation** | BCM (ex: GPIO17) | Nom de puce (ex: `GPIO1_B3`) ou numéro calculé |
| **Accès Python** | `GPIO.output(17, HIGH)` | `chip.get_line(offset).set_value(1)` |
| **Outil CLI** | `gpio write` | `gpioset $(gpiofind GPIO1_B3)=1` |
| **Tension logique** | 3.3V | 3.3V (max 3.63V) |
| **Device nodes** | N/A | `/dev/gpiochip0` … `/dev/gpiochip4` |

### Calcul du numéro GPIO (RK3588S2)

```
GPIO_NUMBER = (bank × 32) + (group × 8) + pin
Groupes : A=0, B=1, C=2, D=3

Exemple : GPIO1_B3 = (1 × 32) + (1 × 8) + 3 = 43
Exemple : GPIO4_B3 = (4 × 32) + (1 × 8) + 3 = 139
```

### Pinout 40 broches Rock 5C (extrait)

```
    3.3V ─── 1  ●  ● 2  ─── 5.0V
GPIO1_D7(63) ─── 3  ●  ● 4  ─── 5.0V
GPIO1_D6(62) ─── 5  ●  ● 6  ─── GND
GPIO1_B3(43) ─── 7  ●  ● 8  ─── GPIO0_B5(13)
         GND ─── 9  ●  ● 10 ─── GPIO0_B6(14)
GPIO4_B3(139)─── 11 ●  ● 12 ─── GPIO4_A1(129)
GPIO4_B2(138)─── 13 ●  ● 14 ─── GND
GPIO4_B4(140)─── 15 ●  ● 16 ─── GPIO1_A5(37)
    3.3V ─── 17 ●  ● 18 ─── GPIO1_B0(40)
GPIO1_A1(33) ─── 19 ●  ● 20 ─── GND
GPIO1_A0(32) ─── 21 ●  ● 22 ─── GPIO1_B5(45)
GPIO1_A2(34) ─── 23 ●  ● 24 ─── GPIO1_A3(35)
         GND ─── 25 ●  ● 26 ─── GPIO1_A4(36)
GPIO0_C7(23) ─── 27 ●  ● 28 ─── GPIO0_D0(24)
GPIO1_B2(42) ─── 29 ●  ● 30 ─── GND
GPIO1_B1(41) ─── 31 ●  ● 32 ─── GPIO4_B0(136)
GPIO1_B4(44) ─── 33 ●  ● 34 ─── GND
GPIO4_A0(128)─── 35 ●  ● 36 ─── GPIO4_A2(130)
  SARADC_IN2 ─── 37 ●  ● 38 ─── GPIO4_A5(133)
         GND ─── 39 ●  ● 40 ─── GPIO4_B1(137)
```

---

## 🔋 Contrôle des Rails d'Alimentation & Boot Forcé

### Mapping GPIO recommandé pour FlashNode-AI

| Broche physique | GPIO RK3588 | N° | Fonction FlashNode-AI | Direction |
|-----------------|-------------|----|-----------------------|-----------|
| **Pin 7** | GPIO1_B3 | 43 | Rail 5V — ON/OFF | OUT |
| **Pin 11** | GPIO4_B3 | 139 | Rail 3.3V — ON/OFF | OUT |
| **Pin 13** | GPIO4_B2 | 138 | RESET RP2040 (RUN, actif bas) | OUT |
| **Pin 15** | GPIO4_B4 | 140 | BOOTSEL RP2040 (actif bas) | OUT |
| **Pin 16** | GPIO1_A5 | 37 | EN ESP32 (actif haut) | OUT |
| **Pin 18** | GPIO1_B0 | 40 | GPIO0 ESP32 (Download Mode, actif bas) | OUT |

### Schéma de commande MOSFET (GPIO 3.3V → charge 5V)

```
Rock 5C GPIO (3.3V)
        │
      [R_gate 100Ω]
        │
        ├──── Gate (MOSFET N-channel, ex: IRLZ44N)
        │
    [R_pulldown 10kΩ] ──── GND
              │
            Source ──── GND
            Drain ──── Charge (Rail 5V ou signal BOOT/RESET)
                                │
                          VCC_Externe (5V)
```

### Séquences de Boot Forcé

#### RP2040 — Forcer le mode BOOTSEL automatiquement

Le RP2040 entre en mode BOOTSEL si `BOOTSEL` est bas **au moment** du reset :

```
1. GPIO BOOTSEL  → LOW   (maintenir à GND)             ← Pin 15
2. GPIO RESET    → LOW   (pulse ~100 ms)               ← Pin 13
3. GPIO RESET    → HIGH  (relâcher)
4. Attendre 500 ms — RP2040 énumère en USB Mass Storage
5. Vérifier USB : "2e8a:0003" détecté
6. picotool load firmware.uf2
7. GPIO BOOTSEL  → HIGH  (relâcher après flash)
8. GPIO RESET    → LOW → HIGH  (reset final, démarrage firmware)
```

#### ESP32 — Forcer le mode Download

```
1. GPIO GPIO0   → LOW   (forcer GPIO0 à GND)           ← Pin 18
2. GPIO EN      → LOW   (pulse ~200 ms)                ← Pin 16
3. GPIO EN      → HIGH  (relâcher EN)
4. Attendre 300 ms — ESP32 entre en mode download
5. esptool.py write_flash ...
6. GPIO GPIO0   → HIGH  (relâcher GPIO0 après flash)
7. GPIO EN      → LOW → HIGH  (reset final)
```

> Ces séquences sont déclenchables en **un clic** depuis le Boot Control Panel de l'interface web, ou via `POST /api/v1/gpio/sequence/rp2040_bootsel` et `POST /api/v1/gpio/sequence/esp32_download`.

### Contrôle des Rails d'Alimentation

```python
# Exemple Python avec gpiod (Armbian / Rock 5C)
import gpiod

# Rail 5V — GPIO1_B3 = bank 1, offset 11 dans gpiochip1
chip1 = gpiod.Chip('/dev/gpiochip1')
rail_5v = chip1.get_line(11)
rail_5v.request(consumer="flashnode", type=gpiod.LINE_REQ_DIR_OUT)

rail_5v.set_value(1)  # Rail 5V ON
rail_5v.set_value(0)  # Rail 5V OFF

# Rail 3.3V — GPIO4_B3 = bank 4, offset 11 dans gpiochip4
chip4 = gpiod.Chip('/dev/gpiochip4')
rail_3v3 = chip4.get_line(11)
rail_3v3.request(consumer="flashnode", type=gpiod.LINE_REQ_DIR_OUT)
```

> ⚠️ Lors d'un power cycle : couper **3.3V avant 5V**, rallumer **5V avant 3.3V**.

---

## 💻 Stack Logicielle

### Backend
| Composant | Technologie | Rôle |
|-----------|-------------|------|
| **Runtime** | Python 3.11+ | Langage principal |
| **API Framework** | FastAPI | REST + Swagger UI auto |
| **ASGI Server** | Uvicorn | Serveur async (ARM64) |
| **WebSockets** | FastAPI WebSocket | Streaming temps réel |
| **Tâches async** | `asyncio` + `asyncio.subprocess` | CLI non-bloquants |
| **GPIO** | `python3-gpiod` (libgpiod) | Contrôle GPIO RK3588S2 |
| **USB events** | `pyudev` | Plug/unplug USB temps réel |
| **Intégrité** | `hashlib` | MD5 / SHA256 |
| **Historique** | `sqlite3` | Journal des opérations |
| **Serveur MCP** | SDK Python `mcp` officiel | Outils pour LLM |

### Outils CLI (ARM64 / Armbian)
| Outil | Cible | Installation |
|-------|-------|-------------|
| `esptool.py` | ESP32 | `pip install esptool` |
| `picotool` | RP2040 | Compilation depuis source (aarch64) |
| `openocd` | RP2040 SWD | `apt install openocd` |
| `gdb-multiarch` | RP2040 debug | `apt install gdb-multiarch` |

### Frontend (SPA)
| Composant | Technologie |
|-----------|-------------|
| **Framework** | Vue.js 3 (Composition API) ou React 18 |
| **État global** | Pinia / Zustand |
| **Terminal** | xterm.js + addon-fit + addon-web-links |
| **Panneaux** | `vue-split-panes` / `react-resizable-panels` |
| **Charts** | Chart.js |
| **Build** | Vite 5 |
| **API** | Axios + WebSocket natif |

---

## 🖥️ Interface Web — Détail des Panneaux

SPA organisée en panneaux redimensionnables, servie par le Rock 5C sur le port 8000.

---

### Panneau 1 — Live Device Tree (colonne gauche)

```
📡 FlashNode-AI  [●ONLINE]  Rock 5C 16Go  |  CPU 12%  |  45°C
──────────────────────────────────────────────────────────────
🔌 Sondes de Débogage
  └── ✅ RPi Debug Probe   [/dev/ttyACM0]  SWD Ready   [CONFIG]

📟 Ports Série
  ├── ✅ ESP32 Prog V2     [/dev/ttyUSB0]  115200 baud  [OPEN]
  ├── ✅ RP2040 CDC        [/dev/ttyACM1]              [OPEN]
  └── ⚪ /dev/ttyUSB1      [Non assigné]               [ASSIGN]

⚡ GPIO & Alimentation
  ├── 🟢 Rail 5V           [ON]   GPIO1_B3(43)   [OFF]
  ├── 🟢 Rail 3.3V         [ON]   GPIO4_B3(139)  [OFF]
  ├── ⚫ RESET RP2040      [HIGH] GPIO4_B2(138)  [PULSE]
  ├── ⚫ BOOTSEL RP2040    [HIGH] GPIO4_B4(140)  [HOLD]
  ├── 🟢 EN ESP32          [HIGH] GPIO1_A5(37)   [PULSE]
  └── ⚫ GPIO0 ESP32       [HIGH] GPIO1_B0(40)   [HOLD]

📦 Firmware Vault  [4 fichiers]
  ├── RP2040/  main_logic_v1.2.elf  ✅
  └── ESP32/   wifi_modem_v2.0.bin  ✅
```

---

### Panneau 2 — Boot Control Panel (barre haute, toujours visible)

```
╔══════════════════════════════════════════════════════════════════╗
║  ⚡ QUICK ACTIONS                                                 ║
║                                                                   ║
║  RP2040 :  [▶ BOOTSEL MODE]  [↺ RESET]  [🔍 DETECT USB]          ║
║  ESP32  :  [▶ DOWNLOAD MODE] [↺ RESET EN] [🔍 DETECT PORT]       ║
║                                                                   ║
║  Rails  :  [5V  ██████ ON ▼]  [3.3V ██████ ON ▼]  [⚠ POWER CYCLE]║
╚══════════════════════════════════════════════════════════════════╝
```

Chaque bouton déclenche la séquence GPIO correspondante et affiche le résultat en notification flottante (détection USB, statut port série).

---

### Panneau 3 — Pipeline Studio (centre)

```
╔══════════════════════════════════════════════════════════════════╗
║  📋 Pipeline : [Prod_Board_V1 ▼]  [+ Nouveau]  [💾 Sauvegarder]  ║
╠══════════════════════════════════════════════════════════════════╣
║  ┌────────────────────────────────────────────────────────┐     ║
║  │ [1] Flash RP2040                          [▼] [×] [⋮] │     ║
║  │  Outil      [OpenOCD ▼]                               │     ║
║  │  Interface  [RPi Debug Probe ▼]                       │     ║
║  │  Firmware   [main_logic_v1.2.elf ▼]    ✅ MD5 OK      │     ║
║  │  ▶ Avancé : SWD [5000 kHz] | Config [cmsis-dap.cfg]  │     ║
║  └────────────────────────────────────────────────────────┘     ║
║  ┌────────────────────────────────────────────────────────┐     ║
║  │ [2] Flash ESP32                           [▼] [×] [⋮] │     ║
║  │  Outil      [esptool ▼]                               │     ║
║  │  Interface  [ESP Programmer V2 ▼]                     │     ║
║  │  Port       [/dev/ttyUSB0 ▼]  Baud [921600 ▼]        │     ║
║  │  Firmware   [wifi_modem_v2.0.bin ▼]    ✅ MD5 OK      │     ║
║  └────────────────────────────────────────────────────────┘     ║
║  ┌────────────────────────────────────────────────────────┐     ║
║  │ [3] Power Cycle — MAIN_VCC (500 ms)       [▼] [×] [⋮] │     ║
║  └────────────────────────────────────────────────────────┘     ║
║  ┌────────────────────────────────────────────────────────┐     ║
║  │ [4] Validate — "SYSTEM_READY" (10 s)      [▼] [×] [⋮] │     ║
║  └────────────────────────────────────────────────────────┘     ║
║  [+ Ajouter étape]                                               ║
║                                                                   ║
║  ████████████████████░░░░░░░░░  60%  Étape 2/4 en cours...       ║
║                     [▶ LANCER]   [⏹ ARRÊTER]                     ║
╚══════════════════════════════════════════════════════════════════╝
```

---

### Panneau 4 — Terminaux Multiplexés xterm.js (droite haute)

| Onglet | Contenu | Fonctionnalités |
|--------|---------|-----------------|
| **📤 Flash Output** | stdout/stderr de l'outil en cours | Barre de progression, couleurs ANSI |
| **📡 Serial RP2040** | UART RP2040 live | Baudrate configurable, envoi de commandes |
| **📡 Serial ESP32** | UART ESP32 live | Filtre par mot-clé, horodatage |
| **🔬 GDB Console** | Sortie GDB/OpenOCD | Commandes GDB interactives |
| **🖥️ System** | Logs FastAPI + MCP | Niveau de log configurable |

Fonctionnalités communes : copier/coller, recherche (Ctrl+F), export `.txt`, auto-scroll, filtre regex.

---

### Panneau 5 — Firmware Vault (droite basse)

```
📦 Firmware Vault
──────────────────────────────────────────────────────────────
  [+ Upload]  [🔍 Vérifier tout]  [🗑 Nettoyer anciens]

  📁 RP2040/
  ├── main_logic_v1.2.elf  128 KB  MD5:a3f4...  ✅  [Flash] [✕]
  └── main_logic_v1.1.elf  127 KB  MD5:b7c1...  ✅  [Flash] [✕]

  📁 ESP32/
  ├── wifi_modem_v2.0.bin  512 KB  MD5:d4e9...  ✅  [Flash] [✕]
  └── wifi_modem_v1.8.bin  510 KB  MD5:f9a2...  ✅  [Flash] [✕]
```

---

### Panneau 6 — Historique des Opérations

```
Historique (SQLite)
──────────────────────────────────────────────────────────────
2026-03-29 14:32:11  ✅  Flash RP2040 OpenOCD    main_logic_v1.2.elf  12.3s
2026-03-29 14:32:28  ✅  Flash ESP32 ESP-Prog V2  wifi_modem_v2.0.bin   8.7s
2026-03-29 14:32:36  ✅  Power Cycle MAIN_VCC     —                     0.5s
2026-03-29 14:32:47  ✅  Validation UART          SYSTEM_READY          3.2s
2026-03-29 14:25:03  ❌  Flash ESP32              wifi_modem_v1.9.bin   Timeout
```

---

### Barre de statut système Rock 5C (bas de page)

```
🖥 Rock 5C  |  CPU ████░░░░ 42%  |  RAM 2.1/16 Go  |  45°C
            |  Uptime 3j 14h     |  IP 192.168.1.42
            |  Dernière op : Flash ESP32 ✅ OK — il y a 4 min
```

---

## 🌐 API REST — Endpoints

**Base URL** : `http://<rock5c-ip>:8000/api/v1`
**Swagger UI** : `http://<rock5c-ip>:8000/docs`

### Firmwares
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/firmware/upload` | Upload .bin / .uf2 / .elf |
| `GET` | `/firmware/list` | Liste tous les firmwares |
| `GET` | `/firmware/{name}/checksum` | MD5 + SHA256 |
| `DELETE` | `/firmware/{name}` | Suppression |
| `POST` | `/firmware/fetch-url` | Téléchargement depuis URL |

### Périphériques
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/devices/scan` | Scan complet USB + GPIO |
| `GET` | `/devices/serial` | Liste `/dev/tty*` |
| `GET` | `/devices/probes` | Sondes CMSIS-DAP |
| `GET` | `/devices/usb-tree` | Arbre USB complet |

### Actions Flash
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/action/flash` | Flash selon config active |
| `POST` | `/action/erase` | Effacement |
| `POST` | `/action/verify` | Vérification sans reflash |
| `POST` | `/action/reset` | Reset logiciel |
| `GET` | `/action/status` | Statut action en cours |

### Pipelines
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/pipeline/create` | Crée/sauvegarde un pipeline |
| `GET` | `/pipeline/list` | Liste les pipelines |
| `GET` | `/pipeline/{name}` | Définition JSON |
| `POST` | `/pipeline/{name}/start` | Lance le pipeline |
| `POST` | `/pipeline/stop` | Arrête le pipeline |
| `GET` | `/pipeline/status` | Avancement détaillé |
| `DELETE` | `/pipeline/{name}` | Suppression |

### GPIO & Alimentation
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/gpio/rail/5v/on` | Activer rail 5V |
| `POST` | `/gpio/rail/5v/off` | Couper rail 5V |
| `POST` | `/gpio/rail/3v3/on` | Activer rail 3.3V |
| `POST` | `/gpio/rail/3v3/off` | Couper rail 3.3V |
| `POST` | `/gpio/sequence/rp2040_bootsel` | Séquence BOOTSEL auto |
| `POST` | `/gpio/sequence/esp32_download` | Séquence Download Mode auto |
| `POST` | `/gpio/sequence/power_cycle` | Cycle complet OFF/ON |
| `POST` | `/gpio/pin/{gpio_num}/set` | Contrôle direct d'une broche |
| `POST` | `/gpio/pin/{gpio_num}/pulse` | Impulsion (durée configurable) |
| `GET` | `/gpio/status` | État de tous les GPIOs |

### Débogage GDB
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/debug/start` | Démarre OpenOCD + GDB server |
| `POST` | `/debug/stop` | Arrête la session |
| `GET` | `/debug/status` | Statut session |

### Historique & Système
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/history` | Journal des opérations (paginé) |
| `GET` | `/system/status` | CPU, RAM, temp, uptime Rock 5C |
| `GET` | `/system/version` | Version FlashNode-AI |

---

## 📡 WebSockets — Temps Réel

**Base URL** : `ws://<rock5c-ip>:8000/ws`

| Endpoint | Description | Format JSON |
|----------|-------------|-------------|
| `WS /ws/flash/progress` | Progression flashage (0–100%) | `{"progress":42,"step":"Writing sector 3/8"}` |
| `WS /ws/flash/output` | Stdout complet de l'outil | `{"type":"stdout","data":"...","ts":"..."}` |
| `WS /ws/serial/{port}` | UART live | `{"data":"SYSTEM_READY\r\n","ts":"..."}` |
| `WS /ws/devices` | Événements udev plug/unplug | `{"event":"add","device":"/dev/ttyUSB0"}` |
| `WS /ws/gpio` | Changements d'état GPIO | `{"pin":"GPIO1_B3","value":1,"label":"Rail 5V"}` |
| `WS /ws/pipeline/status` | Avancement pipeline | `{"step":2,"total":4,"status":"running"}` |
| `WS /ws/system` | Métriques Rock 5C | `{"cpu":42,"ram_mb":2100,"temp_c":45}` |
| `WS /ws/system/logs` | Logs backend FastAPI | `{"level":"INFO","msg":"...","ts":"..."}` |

---

## 🔄 Pipelines Multi-Puces

### Schéma JSON Complet

```json
{
  "pipeline_name": "Prod_Board_V1_Full_Deploy",
  "description": "Flash complet RP2040 + ESP32 avec validation démarrage",
  "version": "1.0",
  "on_error": "stop",
  "steps": [
    {
      "step": 1,
      "description": "Mise sous tension du PCB",
      "action": "gpio_set",
      "pin": "GPIO1_B3",
      "value": 1,
      "label": "Rail 5V ON"
    },
    {
      "step": 2,
      "description": "Attente stabilisation alimentation",
      "action": "delay",
      "duration_ms": 500
    },
    {
      "step": 3,
      "description": "Forcer RP2040 en mode BOOTSEL via GPIO",
      "action": "gpio_sequence",
      "sequence": "rp2040_bootsel"
    },
    {
      "step": 4,
      "description": "Flash RP2040 via picotool",
      "target": "RP2040",
      "tool": "picotool",
      "firmware": "main_logic_v1.2.uf2",
      "action": "flash",
      "retry": 2
    },
    {
      "step": 5,
      "description": "Forcer ESP32 en mode Download via GPIO",
      "action": "gpio_sequence",
      "sequence": "esp32_download"
    },
    {
      "step": 6,
      "description": "Flash ESP32 via Programmer V2",
      "target": "ESP32",
      "tool": "esptool",
      "interface": "esp_prog_v2",
      "port": "/dev/ttyUSB0",
      "chip": "esp32",
      "baudrate": 921600,
      "firmware": "wifi_modem_v2.0.bin",
      "flash_address": "0x1000",
      "action": "flash",
      "retry": 2
    },
    {
      "step": 7,
      "description": "Power Cycle complet",
      "action": "gpio_sequence",
      "sequence": "power_cycle",
      "off_duration_ms": 1000
    },
    {
      "step": 8,
      "description": "Validation démarrage système",
      "action": "monitor_serial",
      "port": "/dev/ttyUSB0",
      "expected_output": "[SYSTEM_READY] Network Init OK",
      "timeout_ms": 10000,
      "on_timeout": "fail"
    }
  ]
}
```

### Actions Disponibles

| `action` | Paramètres clés | Description |
|----------|----------------|-------------|
| `flash` | `tool`, `firmware`, `interface` | Flashage |
| `flash_and_verify` | idem | Flash + vérification mémoire |
| `erase` | `target`, `port` | Effacement complet |
| `reset` | `target` | Reset logiciel |
| `gpio_set` | `pin`, `value` | Set direct d'une broche |
| `gpio_pulse` | `pin`, `duration_ms` | Impulsion |
| `gpio_sequence` | `sequence` | Séquence prédéfinie (BOOTSEL / Download / PowerCycle) |
| `monitor_serial` | `port`, `expected_output`, `timeout_ms` | Attente message UART |
| `delay` | `duration_ms` | Pause |
| `verify_checksum` | `firmware` | Vérif MD5 en flash |

---

## 📦 Firmware Vault

```
/opt/flashnode/vault/
├── RP2040/
│   ├── main_logic_v1.2.elf
│   ├── main_logic_v1.2.elf.md5
│   └── main_logic_v1.2.elf.sha256
└── ESP32/
    ├── wifi_modem_v2.0.bin
    └── wifi_modem_v2.0.bin.md5
```

Règles : checksum auto à l'upload, vérification avant chaque flash, rétention configurable (N versions max).

---

## 🧠 Intégration IA — Serveur MCP

Serveur **Model Context Protocol** sur le Rock 5C (port 8001).

### Outils MCP exposés

| Tool MCP | Description |
|----------|-------------|
| `get_connected_hardware()` | Liste périphériques USB + état GPIO |
| `list_firmwares()` | Contenu du Vault |
| `upload_firmware(path, target)` | Upload dans le Vault |
| `flash_rp2040(firmware, tool, interface)` | Flash RP2040 |
| `flash_esp32(firmware, interface, port, baud)` | Flash ESP32 |
| `run_pipeline(name)` | Lance un pipeline |
| `set_bootsel_mode_rp2040()` | Séquence GPIO BOOTSEL |
| `set_download_mode_esp32()` | Séquence GPIO Download Mode |
| `set_power_rail(rail, state)` | Contrôle rail 5V / 3.3V |
| `power_cycle(off_ms)` | Cycle d'alimentation |
| `stream_serial_logs(port, duration_s)` | Lecture UART N secondes |
| `get_flash_status()` | Statut flashage en cours |
| `get_pipeline_status()` | Statut pipeline |
| `get_system_status()` | CPU, RAM, temp Rock 5C |
| `verify_firmware_integrity(firmware)` | MD5/SHA256 |

### Configuration Claude Desktop

```json
{
  "mcpServers": {
    "flashnode-ai": {
      "command": "python3",
      "args": ["/opt/flashnode/mcp_server.py"],
      "env": {
        "FLASHNODE_API": "http://192.168.1.42:8000",
        "FLASHNODE_MCP_PORT": "8001"
      }
    }
  }
}
```

### Scénario complet piloté par IA

```
User : "Nouveau board branché. Flash les deux puces et dis-moi 
        si le système démarre correctement."

Claude :
  1. get_connected_hardware()
     → RP2040 détecté (sans firmware), ESP32 via ESP-Prog V2

  2. set_bootsel_mode_rp2040()
     → Séquence GPIO exécutée, RP2040 en BOOTSEL (2e8a:0003 détecté)

  3. flash_rp2040("main_logic_v1.3.elf", "picotool", "usb")
     → Flash OK, verified

  4. set_download_mode_esp32()
  5. flash_esp32("wifi_modem_v2.1.bin", "esp_prog_v2", "/dev/ttyUSB0", 921600)
     → Flash OK

  6. power_cycle(1000)
  7. stream_serial_logs("/dev/ttyUSB1", 15)
     → "[SYSTEM_READY] Network Init OK\n[WIFI] AP connected\n[BLE] Advertising..."

  Réponse : "Flash des deux puces réussi. Logs de démarrage : 
             système opérationnel, WiFi connecté, BLE actif. 
             Aucune erreur détectée."
```

---

## 📁 Structure du Projet

```
flashnode-ai/
├── backend/
│   ├── main.py
│   ├── api/v1/
│   │   ├── firmware.py
│   │   ├── devices.py
│   │   ├── actions.py
│   │   ├── pipeline.py
│   │   ├── gpio.py
│   │   ├── debug.py
│   │   └── system.py
│   ├── ws/
│   │   ├── flash_ws.py
│   │   ├── serial_ws.py
│   │   ├── devices_ws.py
│   │   ├── gpio_ws.py
│   │   └── system_ws.py
│   ├── core/
│   │   ├── flasher/
│   │   │   ├── esptool_runner.py
│   │   │   ├── openocd_runner.py
│   │   │   └── picotool_runner.py
│   │   ├── gpio/
│   │   │   ├── controller.py        # libgpiod wrapper
│   │   │   ├── sequences.py         # BOOTSEL / Download / PowerCycle
│   │   │   └── power_rails.py       # Rails 5V / 3.3V
│   │   ├── pipeline_engine.py
│   │   ├── device_scanner.py
│   │   ├── vault_manager.py
│   │   └── history_db.py            # SQLite
│   └── mcp_server.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LiveDeviceTree.vue
│   │   │   ├── BootControlPanel.vue
│   │   │   ├── PowerRailControl.vue
│   │   │   ├── PipelineStudio.vue
│   │   │   ├── TerminalPanel.vue
│   │   │   ├── FirmwareVault.vue
│   │   │   ├── OperationHistory.vue
│   │   │   └── SystemDashboard.vue
│   │   └── stores/
│   │       ├── devices.js
│   │       ├── gpio.js
│   │       ├── pipeline.js
│   │       └── firmware.js
│   └── vite.config.js
├── config/
│   ├── gpio_mapping.json
│   ├── gpio_sequences.json
│   └── openocd/rp2040_custom.cfg
├── vault/
├── pipelines/
├── data/
│   └── history.db
├── docker/
│   ├── Dockerfile.aarch64
│   └── docker-compose.yml
├── scripts/
│   ├── install_armbian.sh
│   └── flashnode.service
├── requirements.txt
└── README.md
```

---

## 🚀 Déploiement sur Armbian

### Méthode 1 — Docker (Recommandée)

```bash
git clone https://github.com/your-org/flashnode-ai.git
cd flashnode-ai
cp .env.example .env && nano .env
docker-compose up -d
```

**docker-compose.yml (extrait)**
```yaml
version: '3.8'
services:
  flashnode-ai:
    build:
      context: ./docker
      dockerfile: Dockerfile.aarch64
    privileged: true
    network_mode: host
    volumes:
      - /dev/bus/usb:/dev/bus/usb
      - /dev/gpiochip0:/dev/gpiochip0
      - /dev/gpiochip1:/dev/gpiochip1
      - /dev/gpiochip2:/dev/gpiochip2
      - /dev/gpiochip3:/dev/gpiochip3
      - /dev/gpiochip4:/dev/gpiochip4
      - /run/udev:/run/udev:ro
      - ./vault:/opt/flashnode/vault
      - ./pipelines:/opt/flashnode/pipelines
      - ./data:/opt/flashnode/data
    restart: unless-stopped
```

### Méthode 2 — Installation directe Armbian

```bash
# Dépendances système
sudo apt update && sudo apt install -y \
    python3 python3-pip python3-venv python3-gpiod \
    libgpiod-dev libgpiod2 gpiod \
    openocd gdb-multiarch \
    libusb-1.0-0-dev cmake git

# Compiler picotool (aarch64)
git clone https://github.com/raspberrypi/picotool.git
cd picotool && mkdir build && cd build
cmake .. && make -j$(nproc) && sudo make install && cd ../..

# esptool
pip3 install esptool --break-system-packages

# Permissions
sudo usermod -aG plugdev,dialout $USER
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="2e8a", MODE="0666", GROUP="plugdev"' | \
    sudo tee /etc/udev/rules.d/99-rp2040.rules
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="10c4", MODE="0666", GROUP="dialout"' | \
    sudo tee /etc/udev/rules.d/99-esp32prog.rules
sudo udevadm control --reload-rules && sudo udevadm trigger

# Application
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
npm install --prefix frontend && npm run build --prefix frontend

# Service systemd
sudo cp scripts/flashnode.service /etc/systemd/system/
sudo systemctl enable --now flashnode.service
```

---

## ⚙️ Configuration Système

### Variables d'Environnement (`.env`)

```env
# Réseau
FLASHNODE_HOST=0.0.0.0
FLASHNODE_PORT=8000

# Stockage
VAULT_PATH=/opt/flashnode/vault
PIPELINES_PATH=/opt/flashnode/pipelines
HISTORY_DB=/opt/flashnode/data/history.db

# GPIO Rock 5C (numéros absolus RK3588S2)
GPIO_RAIL_5V=43           # Pin 7  — GPIO1_B3
GPIO_RAIL_3V3=139         # Pin 11 — GPIO4_B3
GPIO_RESET_RP2040=138     # Pin 13 — GPIO4_B2 (actif bas)
GPIO_BOOTSEL_RP2040=140   # Pin 15 — GPIO4_B4 (actif bas)
GPIO_EN_ESP32=37          # Pin 16 — GPIO1_A5
GPIO_GPIO0_ESP32=40       # Pin 18 — GPIO1_B0 (actif bas)

# Timings Boot (ms)
BOOTSEL_HOLD_MS=100
BOOTSEL_DETECT_WAIT_MS=500
ESP32_DOWNLOAD_RESET_MS=200
ESP32_DOWNLOAD_WAIT_MS=300

# MCP
MCP_ENABLED=true
MCP_PORT=8001

# Sécurité
SECRET_KEY=changez_cette_cle_en_production
API_KEY_ENABLED=false
```

### Configuration GPIO (`config/gpio_mapping.json`)

```json
{
  "platform": "radxa-rock5c",
  "gpio_chip_map": {
    "GPIO0": "/dev/gpiochip0",
    "GPIO1": "/dev/gpiochip1",
    "GPIO4": "/dev/gpiochip4"
  },
  "pins": [
    { "id": "RAIL_5V",        "gpio_name": "GPIO1_B3", "gpio_num": 43,  "chip": "/dev/gpiochip1", "offset": 11, "active": "high", "label": "Rail 5V"       },
    { "id": "RAIL_3V3",       "gpio_name": "GPIO4_B3", "gpio_num": 139, "chip": "/dev/gpiochip4", "offset": 11, "active": "high", "label": "Rail 3.3V"      },
    { "id": "RP2040_RESET",   "gpio_name": "GPIO4_B2", "gpio_num": 138, "chip": "/dev/gpiochip4", "offset": 10, "active": "low",  "label": "RESET RP2040"   },
    { "id": "RP2040_BOOTSEL", "gpio_name": "GPIO4_B4", "gpio_num": 140, "chip": "/dev/gpiochip4", "offset": 12, "active": "low",  "label": "BOOTSEL RP2040" },
    { "id": "ESP32_EN",       "gpio_name": "GPIO1_A5", "gpio_num": 37,  "chip": "/dev/gpiochip1", "offset": 5,  "active": "high", "label": "EN ESP32"       },
    { "id": "ESP32_GPIO0",    "gpio_name": "GPIO1_B0", "gpio_num": 40,  "chip": "/dev/gpiochip1", "offset": 8,  "active": "low",  "label": "GPIO0 ESP32"    }
  ]
}
```

### Séquences Boot (`config/gpio_sequences.json`)

```json
{
  "rp2040_bootsel": {
    "description": "Force RP2040 en mode BOOTSEL via GPIO",
    "steps": [
      { "pin": "RP2040_BOOTSEL", "value": 0, "delay_after_ms": 10  },
      { "pin": "RP2040_RESET",   "value": 0, "delay_after_ms": 100 },
      { "pin": "RP2040_RESET",   "value": 1, "delay_after_ms": 500 },
      { "action": "wait_usb", "vid": "2e8a", "pid": "0003", "timeout_ms": 3000 }
    ],
    "restore_after_flash": [
      { "pin": "RP2040_BOOTSEL", "value": 1, "delay_after_ms": 50 },
      { "pin": "RP2040_RESET",   "value": 0, "delay_after_ms": 100 },
      { "pin": "RP2040_RESET",   "value": 1, "delay_after_ms": 0  }
    ]
  },
  "esp32_download": {
    "description": "Force ESP32 en mode Download via GPIO0 + EN",
    "steps": [
      { "pin": "ESP32_GPIO0", "value": 0, "delay_after_ms": 50  },
      { "pin": "ESP32_EN",    "value": 0, "delay_after_ms": 200 },
      { "pin": "ESP32_EN",    "value": 1, "delay_after_ms": 300 }
    ],
    "restore_after_flash": [
      { "pin": "ESP32_GPIO0", "value": 1, "delay_after_ms": 50  },
      { "pin": "ESP32_EN",    "value": 0, "delay_after_ms": 200 },
      { "pin": "ESP32_EN",    "value": 1, "delay_after_ms": 0   }
    ]
  },
  "power_cycle": {
    "description": "Cycle complet OFF/ON des deux rails",
    "steps": [
      { "pin": "RAIL_3V3", "value": 0, "delay_after_ms": 100 },
      { "pin": "RAIL_5V",  "value": 0, "delay_after_ms": 500 },
      { "pin": "RAIL_5V",  "value": 1, "delay_after_ms": 100 },
      { "pin": "RAIL_3V3", "value": 1, "delay_after_ms": 0   }
    ]
  }
}
```

---

## 🗺️ Roadmap

### v1.0 — Fondations
- [x] Architecture FastAPI + WebSockets (aarch64 / Armbian)
- [x] Flashage ESP32 (USB direct + ESP-Prog V2)
- [x] Flashage RP2040 (picotool + OpenOCD)
- [x] Contrôle GPIO libgpiod (Rock 5C RK3588S2)
- [x] Rails 5V + 3.3V
- [x] Séquences BOOTSEL RP2040 + Download ESP32
- [x] API REST complète + Swagger UI
- [x] Serveur MCP initial

### v1.1 — Interface & Production
- [ ] SPA complète (7 panneaux)
- [ ] Boot Control Panel (boutons one-click)
- [ ] Power Rail Dashboard
- [ ] Pipelines multi-puces JSON
- [ ] Firmware Vault avec checksums
- [ ] Terminaux xterm.js multiplexés
- [ ] Historique SQLite

### v1.2 — Expérience
- [ ] Éditeur visuel pipeline drag-and-drop
- [ ] Live Device Tree udev temps réel
- [ ] Notifications (webhook, email)
- [ ] Thème sombre / clair
- [ ] Pull firmware depuis URL/Git tag (CI/CD)

### v2.0 — Avancé
- [ ] Débogage GDB interactif dans le navigateur
- [ ] Support cluster multi-Rock 5C
- [ ] Rapport de test automatique (PDF)
- [ ] Support JTAG ESP32 natif
- [ ] Interface mobile optimisée

---

## 📝 Notes Techniques Armbian / Rock 5C

- Vérifier les `gpiochip` disponibles avec `gpiodetect` après installation.
- L'offset dans le `gpiochip` peut différer du numéro GPIO absolu — toujours vérifier avec `gpioinfo /dev/gpiochipX`.
- Le RK3588S2 est la variante du RK3588 du Rock 5C (sans PCIe x4 externe).
- OpenOCD pour CMSIS-DAP sur ARM64 peut nécessiter une recompilation depuis source pour le Raspberry Pi Debug Probe.
- Sur Armbian, le kernel 6.x expose généralement les banks GPIO via `/dev/gpiochip0` à `/dev/gpiochip4`.

---

## 📄 Licence

MIT — Voir `LICENSE` pour les détails.

---

*FlashNode-AI — Propulsé par Radxa Rock 5C + Armbian. Conçu pour les makers, ingénieurs hardware et développeurs embarqués exigeants.*
