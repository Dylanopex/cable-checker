import rumps
import subprocess
import time
import threading

class CableCheckerApp(rumps.App):
    def __init__(self):
        super(CableCheckerApp, self).__init__("Cable Checker")
        self.menu = ["Sair"]
        self.icon = None # You can set a custom icon file path here
        self.title = "🔄"
        
        # IPs to check (Primary: Google, Fallback: Cloudflare)
        self.check_ips = ["8.8.8.8", "1.1.1.1"]
        
        # State
        self.current_state = "UNKNOWN"
        self.fail_count = 0
        self.success_count = 0
        
        # Configuration
        self.ethernet_service = "Ethernet" # Change this if your network service name is different
        self.wifi_service = "Wi-Fi"
        self.ethernet_interface = self.get_interface_for_service(self.ethernet_service)
        
        if not self.ethernet_interface:
            self.title = "⚠️"
            rumps.alert("Erro", f"Não foi possível encontrar a interface para o serviço '{self.ethernet_service}'. Verifique o nome nas Preferências de Sistema.")
        
        # Start background thread
        self.running = True
        self.thread = threading.Thread(target=self.monitor_loop)
        self.thread.daemon = True
        self.thread.start()

    def get_interface_for_service(self, service_name):
        try:
            # networksetup -listnetworkserviceorder
            result = subprocess.run(['networksetup', '-listnetworkserviceorder'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if service_name in line and "Hardware Port" in lines[i+1]:
                    # Example: (Hardware Port: Ethernet, Device: en0)
                    parts = lines[i+1].split("Device: ")
                    if len(parts) > 1:
                        return parts[1].replace(')', '').strip()
            return None
        except Exception as e:
            print(f"Error getting interface: {e}")
            return None

    def set_network_priority(self, primary_service, secondary_service):
        try:
            # Note: This command might require administrative privileges depending on system settings
            print(f"Setting priority: 1. {primary_service}, 2. {secondary_service}")
            # We must list all services in order, or at least the top ones. 
            # For simplicity, we put primary first, secondary second, and others will follow.
            # However, networksetup requires all services or it might disable others.
            # To be safe, we should get all current services and reorder them.
            
            result = subprocess.run(['networksetup', '-listallnetworkservices'], capture_output=True, text=True)
            all_services = [s.strip() for s in result.stdout.split('\n') if s.strip() and not s.startswith('*')]
            
            # Remove our two target services from the list
            if primary_service in all_services: all_services.remove(primary_service)
            if secondary_service in all_services: all_services.remove(secondary_service)
            
            # Create new order
            new_order = [primary_service, secondary_service] + all_services
            
            # Execute command
            cmd = ['networksetup', '-ordernetworkservices'] + new_order
            subprocess.run(cmd, capture_output=True)
        except Exception as e:
            print(f"Error setting priority: {e}")

    def ping_test(self):
        if not self.ethernet_interface:
            return False
            
        for ip in self.check_ips:
            try:
                # -c 1 (1 ping), -W 1000 (timeout 1s), -b interface (bind to interface)
                cmd = ['ping', '-c', '1', '-W', '1000', '-b', self.ethernet_interface, ip]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    return True # Success on this IP
            except Exception as e:
                print(f"Ping error: {e}")
        return False # Failed on all IPs

    def monitor_loop(self):
        while self.running:
            if not self.ethernet_interface:
                time.sleep(5)
                self.ethernet_interface = self.get_interface_for_service(self.ethernet_service)
                continue

            is_online = self.ping_test()
            
            if is_online:
                self.fail_count = 0
                self.success_count += 1
                
                if self.current_state != "ETHERNET" and self.success_count >= 2:
                    self.current_state = "ETHERNET"
                    self.title = "🟢 Cabo OK"
                    self.set_network_priority(self.ethernet_service, self.wifi_service)
            else:
                self.success_count = 0
                self.fail_count += 1
                
                if self.current_state != "WIFI" and self.fail_count >= 2:
                    self.current_state = "WIFI"
                    self.title = "🟡 Wi-Fi (Cabo Down)"
                    self.set_network_priority(self.wifi_service, self.ethernet_service)

            time.sleep(3)

    @rumps.clicked("Sair")
    def quit_app(self, _):
        self.running = False
        # Restore Ethernet priority on exit
        if self.current_state == "WIFI":
            self.set_network_priority(self.ethernet_service, self.wifi_service)
        rumps.quit_application()

if __name__ == "__main__":
    CableCheckerApp().run()
