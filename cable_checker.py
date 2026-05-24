import rumps
import subprocess
import time
import threading
from Foundation import NSUserDefaults
from AppKit import NSImage, NSColor, NSBezierPath, NSSize

# Localized strings map for different macOS system languages
TRANSLATIONS = {
    'pt': {
        'cable': 'Cabo',
        'wifi': 'Wifi',
        'offline': 'Offline',
        'error': 'Erro',
        'error_desc': "Não foi possível encontrar a interface para o serviço '{}'.",
        'quit': 'Sair'
    },
    'es': {
        'cable': 'Cable',
        'wifi': 'Wifi',
        'offline': 'Offline',
        'error': 'Error',
        'error_desc': "No se pudo encontrar la interfaz para '{}'.",
        'quit': 'Salir'
    },
    'fr': {
        'cable': 'Câble',
        'wifi': 'Wifi',
        'offline': 'Hors ligne',
        'error': 'Erreur',
        'error_desc': "Impossible de trouver l'interface pour '{}'.",
        'quit': 'Quitter'
    },
    'de': {
        'cable': 'Kabel',
        'wifi': 'WLAN',
        'offline': 'Offline',
        'error': 'Fehler',
        'error_desc': "Schnittstelle für '{}' konnte nicht gefunden werden.",
        'quit': 'Beenden'
    },
    'en': {
        'cable': 'Cable',
        'wifi': 'Wifi',
        'offline': 'Offline',
        'error': 'Error',
        'error_desc': "Could not find interface for '{}'.",
        'quit': 'Quit'
    }
}

class CableCheckerApp(rumps.App):
    def __init__(self):
        # Disable the default quit button to add our custom localized "Sair" / "Quit" item
        super(CableCheckerApp, self).__init__("Cable Checker", quit_button=None)
        
        # Load system translations
        self.lang = self.get_system_language()
        self.t = TRANSLATIONS.get(self.lang, TRANSLATIONS['en'])
        
        # Create and add localized Quit Menu Item
        quit_item = rumps.MenuItem(self.t['quit'], callback=self.quit_app)
        self.menu.add(quit_item)
        
        self.title = " ..."
        
        # IPs to check (Primary: Google, Fallback: Cloudflare)
        self.check_ips = ["8.8.8.8", "1.1.1.1"]
        
        # State
        self.current_state = "UNKNOWN"
        self.fail_count = 0
        self.success_count = 0
        
        # Configuration
        self.ethernet_service = "Ethernet"
        self.wifi_service = "Wi-Fi"
        self.ethernet_interface = self.get_interface_for_service(self.ethernet_service)
        
        if not self.ethernet_interface:
            self.title = " ⚠️"
            rumps.alert(self.t['error'], self.t['error_desc'].format(self.ethernet_service))
        
        # Start background thread
        self.running = True
        self.thread = threading.Thread(target=self.monitor_loop)
        self.thread.daemon = True
        self.thread.start()

    def get_system_language(self):
        try:
            langs = NSUserDefaults.standardUserDefaults().objectForKey_("AppleLanguages")
            if langs and len(langs) > 0:
                return langs[0].split('-')[0].lower()
        except Exception:
            pass
        return 'en'

    def create_circle_image(self, color_name):
        # 14x14 canvas (20% smaller visual footprint compared to raw emojis)
        size = NSSize(14, 14)
        image = NSImage.alloc().initWithSize_(size)
        image.lockFocus()
        try:
            if color_name == "green":
                # High-fidelity vibrant green (matching macOS style)
                color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.18, 0.80, 0.44, 1.0)
            elif color_name == "yellow":
                # Elegant warning yellow
                color = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.75, 0.02, 1.0)
            elif color_name == "red":
                # Premium error red
                color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.92, 0.26, 0.21, 1.0)
            else:
                # Neutral loading gray
                color = NSColor.lightGrayColor()
                
            color.set()
            
            # Draw a sleek 7x7 circle (exactly 20% smaller than average 9-10px emoji dots)
            # Centered: (14 - 7) / 2 = 3.5
            rect = ((3.5, 3.5), (7, 7))
            path = NSBezierPath.bezierPathWithOvalInRect_(rect)
            path.fill()
        finally:
            image.unlockFocus()
        return image

    def update_status(self, state, text):
        self.title = text
        if hasattr(self, '_nsapp') and hasattr(self._nsapp, 'nsstatusitem'):
            image = self.create_circle_image(state)
            self._nsapp.nsstatusitem.setImage_(image)

    def get_interface_for_service(self, service_name):
        try:
            result = subprocess.run(['networksetup', '-listnetworkserviceorder'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if service_name in line and "Hardware Port" in lines[i+1]:
                    parts = lines[i+1].split("Device: ")
                    if len(parts) > 1:
                        return parts[1].replace(')', '').strip()
            return None
        except Exception:
            return None

    def set_network_priority(self, primary_service, secondary_service):
        try:
            result = subprocess.run(['networksetup', '-listallnetworkservices'], capture_output=True, text=True)
            all_services = [s.strip() for s in result.stdout.split('\n') if s.strip() and not s.startswith('*')]
            
            if primary_service in all_services: all_services.remove(primary_service)
            if secondary_service in all_services: all_services.remove(secondary_service)
            
            new_order = [primary_service, secondary_service] + all_services
            cmd = ['networksetup', '-ordernetworkservices'] + new_order
            subprocess.run(cmd, capture_output=True)
        except Exception:
            pass

    def ping_test(self, interface=None):
        for ip in self.check_ips:
            try:
                cmd = ['ping', '-c', '1', '-W', '1000']
                if interface:
                    cmd.extend(['-b', interface])
                cmd.append(ip)
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    return True 
            except Exception:
                pass
        return False

    def monitor_loop(self):
        while self.running:
            if not self.ethernet_interface:
                time.sleep(5)
                self.ethernet_interface = self.get_interface_for_service(self.ethernet_service)
                continue

            # Set initial loading status before ping completes
            if self.current_state == "UNKNOWN":
                self.update_status("gray", " ...")

            # Check if Ethernet has internet
            ethernet_online = self.ping_test(interface=self.ethernet_interface)
            
            if ethernet_online:
                self.fail_count = 0
                self.success_count += 1
                
                if self.current_state != "ETHERNET" and self.success_count >= 2:
                    self.current_state = "ETHERNET"
                    self.update_status("green", f" {self.t['cable']}")
                    self.set_network_priority(self.ethernet_service, self.wifi_service)
                elif self.current_state == "ETHERNET":
                    self.update_status("green", f" {self.t['cable']}")
            else:
                self.success_count = 0
                self.fail_count += 1
                
                if self.current_state != "WIFI" and self.fail_count >= 2:
                    self.current_state = "WIFI"
                    self.set_network_priority(self.wifi_service, self.ethernet_service)
                
                # If we are using WIFI, verify if system actually has internet
                if self.current_state == "WIFI":
                    system_online = self.ping_test() # Uses default route
                    if system_online:
                        self.update_status("yellow", f" {self.t['wifi']}")
                    else:
                        self.update_status("red", f" {self.t['offline']}")

            time.sleep(3)

    def quit_app(self, _):
        self.running = False
        if self.current_state == "WIFI":
            self.set_network_priority(self.ethernet_service, self.wifi_service)
        rumps.quit_application()

if __name__ == "__main__":
    CableCheckerApp().run()
