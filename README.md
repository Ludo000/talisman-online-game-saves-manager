# Talisman Online Saves Manager 🎮

<img width="730" height="557" alt="image" src="https://github.com/user-attachments/assets/fd02ab36-1290-483a-a6b0-54bc8dba533b" />

An automated, lightweight, multi-language (English & French) save game backup utility for **Talisman: Digital Classic Edition**. 

This application safely monitors your live gameplay session, prevents unintended game state losses, and lets you manage an unlimited number of distinct, custom-named local save slots. Compatible with **Windows** and **Linux (Steam/Proton)**.

---

## ⚖️ Disclosure & Disclaimer

**Talisman Save Manager is an unofficial, community-made utility.** * This project is **not affiliated with, authorized, maintained, sponsored, or endorsed** by Nomad Games, Games Workshop, or any of their affiliates or partners. 
* "Talisman", "Talisman: Digital Edition", logos, and all associated game assets are registered trademarks of their respective owners.
* Use this tool at your own risk. The developer is not responsible for any data loss, save file corruption, or game bans resulting from the use of this software. Always ensure your active game client is fully closed before restoring backups.

---

## ✨ Features

* **Multiplatform Auto-Detection:** Automatically discovers your Steam library directory structures and active game profile save directories on both Windows and Linux (including native and Flatpak Steam setups).
* **Live Game Monitoring:** Polling diagnostics dynamically warn you if Talisman is active to prevent file corruption.
* **On-the-Fly Translation Selector:** Switch between English (Default) and French layout modes instantaneously with no app restart required.
* **Persistent Local Memory:** App preferences and save target path adjustments are kept safe inside a standalone config file stored right next to your application launcher.
* **Streamlined Backups:** Save, load, rename, or permanently erase individual save slots directly inside a clean graphical interface.

---

## 📂 Default Game Save Locations

The program automatically checks these locations first, but you can manually re-assign the paths via the UI's `✏️ Modify` tool:

* **Windows:** `%APPDATA%\Nomad Games\Talisman\saved_game\`
* **Linux (Standard Steam):** `~/.steam/steam/steamapps/compatdata/247000/pfx/drive_c/users/steamuser/AppData/Roaming/Nomad Games/Talisman/saved_game/`
* **Linux (Flatpak Steam):** `~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/compatdata/247000/pfx/drive_c/users/steamuser/AppData/Roaming/Nomad Games/Talisman/saved_game/`

---

## 🚀 Getting Started

### Prerequisites

To run or build the app from source code, ensure you have **Python 3.x** and the default graphic system toolkit variables installed on your operating system:

```bash
# Ubuntu / Debian / Mint Linux
sudo apt install python3-tk

# Fedora / RHEL
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
