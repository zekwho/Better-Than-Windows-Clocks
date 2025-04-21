import tkinter as tk
import customtkinter as ctk
from datetime import datetime
import pytz, time, threading, json, os, uuid, winreg, sys, subprocess, pystray, ctypes
from PIL import Image, ImageTk
from pystray import MenuItem as item

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clock_config.json")

if hasattr(sys, '_MEIPASS'):
    try:
        from pathlib import Path
        documents_folder = str(Path.home() / "Documents")
        CONFIG_FILE = os.path.join(documents_folder, "BetterThanWindowsClocks", "clock_config.json")
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        print(f"Using config file: {CONFIG_FILE}")
    except Exception as e:
        print(f"Error setting config path: {e}")
        CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clock_config.json")
class TimeCard(tk.Toplevel):
    """Individual timezone card that displays the current time for a specific timezone"""
    def __init__(self, parent, timezone, card_id=None, position=None, size=None):
        super().__init__(parent)
        self.parent = parent
        self.timezone = timezone
        self.card_id = card_id or str(uuid.uuid4())  
        self.title(f"Clock: {timezone}")
        self.geometry("280x125")  
        self.attributes("-alpha", 0.85) 
        self.attributes("-topmost", False)  
        self.overrideredirect(True)  
        if position:
            self.geometry(position)
        if size:
            self.geometry(size)
        bg_color = "#2B2B2B"  
        self.configure(bg=bg_color)
        self.resizing = False
        self.resize_x = 0
        self.resize_y = 0
        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.end_drag)  
        self.bind("<Button-3>", self.show_context_menu)  
        self.create_widgets()
        self.update_display_time()
    def create_widgets(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#2D3035")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=0)  
        self.main_frame.grid_rowconfigure(1, weight=1)  
        self.name_label = ctk.CTkLabel(
            self.main_frame, 
            text=self.timezone,
            font=("Segoe UI", 16, "bold"),
            padx=0, pady=0,  
            text_color="#8E96A3" 
        )
        self.name_label.grid(row=0, column=0, sticky="ew", padx=0, pady=(12, 0))
        self.time_label = ctk.CTkLabel(
            self.main_frame, 
            text="--:--:--", 
            font=("Segoe UI", 40),  
            padx=0, pady=0,  
            text_color="#FFFFFF"  
        )
        self.time_label.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, 12))
        self.resize_frame = ctk.CTkFrame(self, width=12, height=12, corner_radius=2, fg_color="#555555")
        self.resize_frame.place(relx=1.0, rely=1.0, anchor="se", x=-4, y=-4)
        self.resize_frame.bind("<Button-1>", self.start_resize)
        self.resize_frame.bind("<B1-Motion>", self.on_resize)
        self.resize_frame.bind("<ButtonRelease-1>", self.end_resize)
    def start_drag(self, event):
        if event.widget != self.resize_frame:
            self.x = event.x
            self.y = event.y
    def on_drag(self, event):
        if not self.resizing and event.widget != self.resize_frame:
            x = self.winfo_pointerx() - self.x
            y = self.winfo_pointery() - self.y
            self.geometry(f"+{x}+{y}")
    def start_resize(self, event):
        self.resizing = True
        self.resize_x = event.x
        self.resize_y = event.y
    def on_resize(self, event):
        if self.resizing:
            new_width = max(200, self.winfo_width() + (event.x - self.resize_x))
            new_height = max(120, self.winfo_height() + (event.y - self.resize_y))
            self.geometry(f"{new_width}x{new_height}")
            self.resize_x = event.x
            self.resize_y = event.y
    def end_resize(self, event):
        self.resizing = False
        self.notify_position_change()
    def end_drag(self, event):
        if not self.resizing:
            self.snap_to_others()
            self.after(100, self.notify_position_change)
    def snap_to_others(self):
        other_cards = [card for cid, card in self.parent.cards.items() if cid != self.card_id]
        current_x = self.winfo_x()
        current_y = self.winfo_y()
        width = self.winfo_width()
        height = self.winfo_height()
        snap_distance = 20
        for other in other_cards:
            other_x = other.winfo_x()
            other_y = other.winfo_y()
            other_width = other.winfo_width()
            other_height = other.winfo_height()
            if abs((current_x + width/2) - (other_x + other_width/2)) < width/3:
                if abs((current_y + height) - other_y) < snap_distance:
                    center_x = other_x + (other_width - width)/2
                    self.geometry(f"+{int(center_x)}+{other_y - height}")
                    return
                if abs(current_y - (other_y + other_height)) < snap_distance:
                    center_x = other_x + (other_width - width)/2
                    self.geometry(f"+{int(center_x)}+{other_y + other_height}")
                    return
            if abs((current_y + height/2) - (other_y + other_height/2)) < height/3:
                if abs((current_x + width) - other_x) < snap_distance:
                    center_y = other_y + (other_height - height)/2
                    self.geometry(f"+{other_x - width}+{int(center_y)}")
                    return
                if abs(current_x - (other_x + other_width)) < snap_distance:
                    center_y = other_y + (other_height - height)/2
                    self.geometry(f"+{other_x + other_width}+{int(center_y)}")
                    return
    def notify_position_change(self):
        if hasattr(self.parent, "update_card_position"):
            geometry = self.geometry()
            self.parent.update_card_position(self.card_id, self.timezone, geometry)
    def update_display_time(self):
        """Update the time display based on the timezone"""
        time_str = self.get_time_for_timezone()
        self.time_label.configure(text=time_str)
    def get_time_for_timezone(self):
        try:
            if self.timezone == "Local":
                current_time = datetime.now()
            elif self.timezone == "UTC":
                current_time = datetime.now(pytz.UTC)
            else:
                tz = pytz.timezone(self.timezone)
                current_time = datetime.now(tz)
            if hasattr(self.parent, 'hour_format') and self.parent.hour_format.get() == "12h":
                return current_time.strftime("%I:%M:%S %p")  
            else:
                return current_time.strftime("%H:%M:%S") 
        except Exception as e:
            print(f"Error getting time for {self.timezone}: {e}")
            return "--:--:--"
    def show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Close Card", command=self.close_card)
        menu.add_command(label="Add New Timezone", command=self.parent.show_add_dialog)
        menu.post(event.x_root, event.y_root)
    def close_card(self):
        self.parent.remove_card(self.card_id)
        self.destroy()
class DesktopClocks(ctk.CTk):
    """Main application that manages all timezone cards"""
    def __init__(self):
        super().__init__()
        self.title("Better Than Windows Clocks")
        self.geometry("350x500")  
        self.attributes("-topmost", False) 
        self.minimized_to_tray = False
        self.cards = {}
        self.list_items = {}
        self.hour_format = tk.StringVar(value="24h")
        self.tray_icon = None
        self.tray_thread = None
        self.create_widgets()
        self.load_config()
        self.update_all_cards()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    def create_widgets(self):
        self.title_label = ctk.CTkLabel(
            self, 
            text="Better Than Windows Clocks", 
            font=("Segoe UI", 18, "bold")
        )
        self.title_label.pack(pady=20)
        self.format_frame = ctk.CTkFrame(self)
        self.format_frame.pack(fill=tk.X, padx=20, pady=5)
        self.format_label = ctk.CTkLabel(
            self.format_frame,
            text="Time Format:",
            font=("Segoe UI", 12)
        )
        self.format_label.pack(side=tk.LEFT, padx=10)
        self.format_24h = ctk.CTkRadioButton(
            self.format_frame,
            text="24-hour",
            variable=self.hour_format,
            value="24h",
            command=self.update_all_cards
        )
        self.format_24h.pack(side=tk.LEFT, padx=10)
        self.format_12h = ctk.CTkRadioButton(
            self.format_frame,
            text="12-hour",
            variable=self.hour_format,
            value="12h",
            command=self.update_all_cards
        )
        self.format_12h.pack(side=tk.LEFT, padx=10)
        self.timezone_frame = ctk.CTkFrame(self)
        self.timezone_frame.pack(fill=tk.X, padx=20, pady=10)
        self.available_timezones = [
            "Local",
            "UTC",
            "Europe/London",
            "Europe/Amsterdam", 
            "Asia/Manila",
            "Asia/Tokyo",
            "US/Pacific", 
            "US/Mountain", 
            "US/Central", 
            "US/Eastern",
            "Europe/Paris", 
            "Europe/Berlin", 
            "Europe/Moscow",
            "Asia/Singapore", 
            "Asia/Dubai", 
            "Australia/Sydney",
            "Pacific/Auckland"
        ]
        self.timezone_var = tk.StringVar()
        self.timezone_dropdown = ctk.CTkOptionMenu(
            self.timezone_frame, 
            values=self.available_timezones,
            variable=self.timezone_var
        )
        self.timezone_dropdown.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.add_button = ctk.CTkButton(
            self.timezone_frame, 
            text="Add", 
            command=self.add_timezone_card
        )
        self.add_button.pack(side=tk.RIGHT, padx=10)
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.list_label = ctk.CTkLabel(
            self.list_frame, 
            text="Active Timezone Cards:", 
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        )
        self.list_label.pack(fill=tk.X, padx=10, pady=10)
        self.card_list = ctk.CTkScrollableFrame(self.list_frame)
        self.card_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.pack(fill=tk.X, padx=20, pady=10)
        self.hide_all_button = ctk.CTkButton(
            self.bottom_frame, 
            text="Hide All Cards", 
            command=self.toggle_all_cards
        )
        self.hide_all_button.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)
        self.hide_manager_button = ctk.CTkButton(
            self.bottom_frame, 
            text="Minimize to Tray", 
            command=self.minimize_to_tray,
            width=120
        )
        self.hide_manager_button.pack(side=tk.RIGHT, padx=10, expand=True, fill=tk.X)
        self.startup_frame = ctk.CTkFrame(self)
        self.startup_frame.pack(fill=tk.X, padx=20, pady=10)
        self.startup_var = tk.BooleanVar(value=self.check_startup())
        self.startup_checkbox = ctk.CTkCheckBox(
            self.startup_frame,
            text="Launch on Windows startup",
            variable=self.startup_var,
            command=self.toggle_startup
        )
        self.startup_checkbox.pack(pady=5)
        self.cards_visible = True
    def check_startup(self):
        """Check if the application is configured to run at startup"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )
            winreg.QueryValueEx(key, "DesktopTimezoneClock")
            winreg.CloseKey(key)
            return True
        except:
            return False
    def toggle_startup(self):
        """Add or remove the application from Windows startup"""
        script_path = os.path.abspath(__file__)
        python_exe = sys.executable
        cmd = f'"{python_exe}" "{script_path}"'
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_WRITE
            )
            if self.startup_var.get():
                winreg.SetValueEx(key, "DesktopTimezoneClock", 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, "DesktopTimezoneClock")
                except:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Error setting startup: {e}")
    def minimize_to_tray(self):
        """Minimize the application to system tray"""
        self.minimized_to_tray = True
        self.withdraw()
        if not self.tray_icon:
            icon_path = self.get_icon_path()
            self.tray_icon = pystray.Icon(
                "BetterThanWindowsClocks", 
                self.load_icon(icon_path), 
                "Better Than Windows Clocks",
                menu=self.create_tray_menu()
            )
            self.tray_icon.on_click = self.on_tray_click
            self.tray_thread = threading.Thread(target=self.run_tray_icon, daemon=True)
            self.tray_thread.start()
    def get_icon_path(self):
        """Get the path to the icon file"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "BTWC.ico")
        if hasattr(sys, '_MEIPASS'):
            pyinstaller_path = os.path.join(sys._MEIPASS, "BTWC.ico")
            if os.path.exists(pyinstaller_path):
                icon_path = pyinstaller_path
        if not os.path.exists(icon_path):
            print(f"Icon not found at {icon_path}, creating a default icon")
            try:
                img = Image.new('RGBA', (64, 64), color=(0, 120, 212, 255))
                temp_dir = os.environ.get('TEMP', os.path.dirname(os.path.abspath(__file__)))
                icon_path = os.path.join(temp_dir, 'desktop_clock_icon.ico')
                img.save(icon_path, format='ICO')
            except Exception as e:
                print(f"Error creating fallback icon: {e}")
        return icon_path
    def load_icon(self, icon_path):
        """Load icon image for the tray"""
        try:
            if os.path.exists(icon_path):
                return Image.open(icon_path)
            else:
                return Image.new('RGBA', (64, 64), color=(0, 120, 212, 255))
        except Exception as e:
            print(f"Error loading icon: {e}")
            return Image.new('RGBA', (64, 64), color=(0, 120, 212, 255))
    def run_tray_icon(self):
        """Run the tray icon in a separate thread"""
        try:
            self.tray_icon.run()
        except Exception as e:
            print(f"Error running tray icon: {e}")
    def create_tray_menu(self):
        """Create the tray icon menu"""
        return pystray.Menu(
            item('Show', self.on_tray_show),
            item('Exit', self.on_tray_exit)
        )
    def on_tray_show(self):
        """Callback for Show menu item - must be thread-safe"""
        if hasattr(self, 'after_idle'):
            self.after_idle(self._restore_window)
    def on_tray_exit(self):
        """Callback for Exit menu item - must be thread-safe"""
        if hasattr(self, 'after_idle'):
            self.after_idle(self.on_closing)
    def on_tray_click(self, icon, button, modifiers):
        """Handle clicks on the tray icon"""
        if button == pystray.mouse.Button.left:
            if threading.current_thread() != threading.main_thread():
                self.after_idle(self._restore_window)
            else:
                self._restore_window()
    def restore_from_tray(self):
        """Restore the application from system tray"""
        if not self.minimized_to_tray:
            return
        self.minimized_to_tray = False
        self.after_idle(self._restore_window)
    def _restore_window(self):
        """Actually restore the window (must be called from main thread)"""
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
            try:
                hwnd = self.winfo_id()
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                SW_SHOW = 5
                ctypes.windll.user32.ShowWindow(hwnd, SW_SHOW)   
                ctypes.windll.user32.FlashWindow(hwnd, True)
            except Exception as e:
                print(f"Error using Windows API for foreground: {e}")
            self.attributes("-topmost", True)
            self.update()
            self.attributes("-topmost", False)
            if self.tray_icon:
                threading.Thread(target=self.stop_tray_icon, daemon=True).start()
        except Exception as e:
            print(f"Error restoring window: {e}")
    def stop_tray_icon(self):
        """Stop the tray icon gracefully"""
        try:
            if self.tray_icon:
                self.tray_icon.stop()
                self.tray_icon = None
        except Exception as e:
            print(f"Error stopping tray icon: {e}")
    def add_timezone_card(self, timezone=None, card_id=None, position=None, size=None):
        if timezone is None:
            timezone = self.timezone_var.get()
        if not timezone:
            return
        print(f"Adding card for {timezone} with ID {card_id}, position {position}, size {size}")
        new_card = TimeCard(self, timezone, card_id, position, size)
        card_id = new_card.card_id
        self.cards[card_id] = new_card
        self.add_to_card_list(card_id, timezone)
        self.save_config()
        print(f"Card added with ID {card_id}, geometry: {new_card.geometry()}")
        return card_id
    def add_to_card_list(self, card_id, timezone):
        list_item = ctk.CTkFrame(self.card_list)
        list_item.pack(fill=tk.X, pady=2)
        name_label = ctk.CTkLabel(list_item, text=timezone, width=120) 
        name_label.pack(side=tk.LEFT, padx=10)
        remove_button = ctk.CTkButton(
            list_item, 
            text="×", 
            width=30, 
            command=lambda cid=card_id: self.remove_card(cid)
        )
        remove_button.pack(side=tk.RIGHT, padx=10)
        self.list_items[card_id] = list_item
    def remove_card(self, card_id):
        if card_id in self.cards:
            print(f"Removing card {card_id} for {self.cards[card_id].timezone}")
            self.cards[card_id].destroy()
            del self.cards[card_id]
            if card_id in self.list_items:
                self.list_items[card_id].destroy()
                del self.list_items[card_id]
            self.save_config()
    def update_card_position(self, card_id, timezone, position):
        """Update the position in our data"""
        if card_id in self.cards:
            print(f"Updating card position for {timezone}: {position}")
            self.save_config()
    def toggle_all_cards(self):
        if self.cards_visible:
            for card_id, card in self.cards.items():
                card.withdraw()
            self.hide_all_button.configure(text="Show All Cards")
        else:
            for card_id, card in self.cards.items():
                card.deiconify()
            self.hide_all_button.configure(text="Hide All Cards")
        self.cards_visible = not self.cards_visible
    def show_add_dialog(self):
        self.deiconify()
        self.lift()
    def save_config(self):
        """Save the current timezone cards configuration to a JSON file"""
        config = {
            "hour_format": self.hour_format.get(),
            "cards": {}
        }
        for card_id, card in self.cards.items():
            config["cards"][card_id] = {
                "timezone": card.timezone,
                "geometry": card.geometry() 
            }
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Configuration saved to {CONFIG_FILE}")
            print(f"Saved {len(config['cards'])} cards with {config['hour_format']} format")
        except Exception as e:
            print(f"Error saving configuration: {e}")
    def load_config(self):
        """Load timezone cards configuration from JSON file if it exists"""
        print(f"Attempting to load configuration from {CONFIG_FILE}")
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                print(f"Configuration loaded successfully")
                if "hour_format" in config:
                    self.hour_format.set(config["hour_format"])
                    print(f"Loaded hour format: {config['hour_format']}")
                if "cards" in config and config["cards"]:
                    print(f"Found {len(config['cards'])} saved cards")
                    for card_id, card_info in config["cards"].items():
                        timezone = card_info.get("timezone")
                        geometry = card_info.get("geometry")
                        print(f"Creating card for {timezone} with geometry {geometry}")
                        position = None
                        size = None
                        if geometry:
                            if "x" in geometry and "+" in geometry:
                                size_part = geometry.split("+")[0]
                                position = "+" + "+".join(geometry.split("+")[1:])
                                size = size_part
                                print(f"Parsed geometry: size={size}, position={position}")           
                        if timezone:
                            try:
                                self.add_timezone_card(timezone, card_id, position, size)
                                print(f"Card added successfully for {timezone}")
                            except Exception as e:
                                print(f"Error adding card for {timezone}: {e}")
                    print("Ensuring all cards are visible")
                    for card_id, card in self.cards.items():
                        try:
                            card.deiconify()
                            card.update()
                            print(f"Card {card_id} for {card.timezone} shown at {card.geometry()}")
                        except Exception as e:
                            print(f"Error showing card {card_id}: {e}")
                else:
                    print("No saved cards found, adding default Local timezone")
                    self.add_timezone_card("Local")
            except Exception as e:
                print(f"Error loading configuration: {e}")
                self.add_timezone_card("Local")
        else:
            print(f"Configuration file not found at {CONFIG_FILE}, adding default timezone")
            self.add_timezone_card("Local")
    def on_closing(self):
        """Save configuration and quit the application"""
        print("Application closing, saving configuration...")
        self.save_config()
        print(f"Configuration saved to {CONFIG_FILE}")
        for card_id, card in list(self.cards.items()):
            try:
                card.destroy()
            except:
                pass
        self.cards.clear()
        if self.tray_icon:
            try:
                threading.Thread(target=self.stop_tray_icon, daemon=True).start()
            except:
                pass
        self.destroy() 
    def update_all_cards(self):
        """Centralized time update for all cards to ensure synchronization"""
        try:
            for card_id, card in self.cards.items():
                card.update_display_time()        
            self.after(1000, self.update_all_cards)
        except Exception as e:
            print(f"Error in centralized time update: {e}")
            self.after(5000, self.update_all_cards)
if __name__ == "__main__":
    app = DesktopClocks()
    app.mainloop() 
