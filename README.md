# Cable Checker 🟢🟡🔴

A macOS Menu Bar application that monitors real-time internet connectivity when connected to both **Ethernet (Cable)** and **Wi-Fi** simultaneously. It automatically manages macOS network service priority to ensure a seamless and instant failover if the Ethernet connection loses internet access, keeping the Wi-Fi connected at all times.

---

## 📖 Background

By default, macOS prioritizes the Ethernet connection. However, if the Ethernet interface loses its internet connection but remains physically connected to a router/switch, macOS does not automatically switch traffic over to Wi-Fi. 

**Cable Checker** solves this by:
1. Keeping both Wi-Fi and Ethernet active and connected at all times (preventing authentication delays).
2. Pinging public servers via the Ethernet interface every 3 seconds to check actual internet availability.
3. Dynamically reordering network services in macOS using `networksetup` when a connection loss is detected.
4. Restoring Ethernet priority as soon as the cable connection becomes stable again.

---

## 🛠️ Features

* **Sleek, Premium UI:** Programmatically draws an elegant, anti-aliased 7x7 dot (20% smaller than standard emoji dots) directly onto a custom `NSImage` to perfectly match the minimalist aesthetic of the native macOS menu bar.
* **Smart Localization:** Automatically detects the macOS system language on boot and translates the interface. Supports: **Portuguese, English, Spanish, French, and German** with an English fallback.
* **High Tolerance Failover:** Prevents unnecessary network switching due to minor network blips by requiring 2 consecutive failed ping tests (6 seconds) before switching to Wi-Fi, and 2 consecutive successful pings before switching back to Cable.
* **Dock-less & Background Execution:** Built as an agent (`LSUIElement = true`) so it runs exclusively in the menu bar without showing in the Dock.
* **Safe Exit:** Restores default Ethernet priority immediately when quitting the application.

---

## 📋 Requirements

* macOS 10.15+ (Big Sur, Monterey, Ventura, Sonoma, Sequoia)
* Python 3.9+
* `rumps` and `pyobjc` libraries

---

## 🚀 Installation & Build

### 1. Install Dependencies
Ensure you have the required Python packages installed:
```bash
pip3 install -r requirements.txt
```

### 2. Customizing Network Service Names
By default, the script looks for network services named `"Ethernet"` and `"Wi-Fi"`. If your macOS uses different names (e.g., `"USB 10/100/1000 LAN"`), open `cable_checker.py` and modify the configuration fields in `__init__`:
```python
self.ethernet_service = "Ethernet"  # Change to your Ethernet service name
self.wifi_service = "Wi-Fi"        # Change to your Wi-Fi service name
```

### 3. Compile Native macOS Application
To bypass Gatekeeper and `py2app` framework distribution errors on modern macOS, we compile the app using the native `osacompile` utility. This wraps the python script in a secure, signed AppleScript bundle:

```bash
# Compile
osacompile -o CableChecker.app -e 'do shell script "/usr/bin/python3 \"/Users/dylanmac/.cable_checker_app/cable_checker.py\""'

# Hide from Dock
/usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" CableChecker.app/Contents/Info.plist
```

---

## ⚙️ Administrative Privileges (Sudoers)

The `networksetup -ordernetworkservices` command used to dynamically prioritize interfaces usually requires administrative privileges. 

To prevent macOS from prompting you for your administrator password every time it switches networks, you can grant passwordless permission to `networksetup` for your user.

1. Open your terminal and run:
   ```bash
   sudo visudo
   ```
2. Add the following line at the very end of the file (replace `dylanmac` with your actual macOS username):
   ```text
   dylanmac ALL=(ALL) NOPASSWD: /usr/sbin/networksetup
   ```
3. Save and close. The app will now perform lightning-fast switches in the background silently.

---

## 🔄 Auto-Start on Boot

To run Cable Checker automatically when you start your Mac:
1. Open **System Settings** > **General** > **Login Items** (Itens de Início).
2. Click the `+` button.
3. Choose your compiled `CableChecker.app` from your Applications folder.

---

## 📄 License

This project is open-source and free to use. Designed with 💚 for macOS power users.
