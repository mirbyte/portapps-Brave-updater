import os
import sys
import shutil
import requests
from datetime import datetime
import time
from bs4 import BeautifulSoup
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from pathlib import Path
import ctypes


# this is ass

# --- DPI Awareness ---
try:
    ctypes.windll.shcore.SetProcessDpiAwarenessContext(-2)
except (AttributeError, OSError):
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            # Fallback: no DPI awareness
            pass


class BraveUpdaterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("portapps.io Brave updater v1.2")
        
        # Better window sizing and scaling
        self.setup_window_scaling()
        
        self.colors = {
            'primary_blue': '#337ab7',
            'secondary_blue': '#2068a5', 
            'accent_orange': '#f27a38',
            'light_orange': '#ff8c4e',
            'background': '#f8fafc',
            'surface': '#ffffff',
            'text_dark': '#1e293b',
            'text_light': '#64748b',
            'success': '#059669',
            'error': '#dc2626'
        }
        
        self.root.configure(bg=self.colors['background'])
        self.setup_styles()
        self.create_widgets()
        self.setup_logging()
        
        # Threading control
        self.update_thread = None
        self.is_updating = False
        
        # Check if running from correct folder on startup
        self.validate_folder()
    
    def setup_window_scaling(self):
        """Proper window scaling and DPI handling"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate DPI scaling factor
        try:
            dpi = self.root.winfo_fpixels('1i')
            scale_factor = dpi / 150.0
        except:
            scale_factor = 1.0
        
        # Adjust base window size based on screen size and DPI - INCREASED HEIGHTS
        if screen_width >= 1920:  # Large screens
            base_width, base_height = 900, 950
        elif screen_width >= 1366:  # Medium screens
            base_width, base_height = 800, 850
        else:  # Small screens
            base_width, base_height = 700, 750
        
        # Apply scaling with better height accommodation
        window_width = int(base_width * min(scale_factor, 1.5))
        window_height = int(base_height * min(scale_factor, 1.5))
        
        # Ensure minimum height to accommodate all elements
        min_height = 800
        window_height = max(window_height, min_height)
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(650, 800)
        self.root.resizable(True, True)
        
        # Store scaling info for font adjustments
        self.scale_factor = scale_factor
        
    def get_scaled_font_size(self, base_size):
        """Calculate scaled font size based on DPI"""
        return max(8, int(base_size * min(self.scale_factor, 1.3)))
        
    def validate_folder(self):
        current_folder = os.path.basename(os.getcwd())
        if "brave" not in current_folder.lower():
            messagebox.showerror("Error", 
                               "This script must be run from a folder containing 'brave' in its name.\n"
                               "Please move this script to the correct location.")
            self.root.quit()
            return False
        return True
        
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Scaled font sizes
        title_font_size = self.get_scaled_font_size(16)
        subtitle_font_size = self.get_scaled_font_size(10)
        button_font_size = self.get_scaled_font_size(10)
        
        # Configure custom styles with proper scaling
        self.style.configure('Title.TLabel', 
                           font=('Segoe UI', title_font_size, 'bold'),
                           foreground=self.colors['primary_blue'],
                           background=self.colors['background'])
        
        self.style.configure('Subtitle.TLabel',
                           font=('Segoe UI', subtitle_font_size),
                           foreground=self.colors['text_light'],
                           background=self.colors['background'])
        
        self.style.configure('Primary.TButton',
                           font=('Segoe UI', button_font_size, 'bold'),
                           foreground='white',
                           padding=(10, 8))
        
        self.style.map('Primary.TButton',
                      background=[('active', self.colors['secondary_blue']),
                                ('!active', self.colors['primary_blue'])])
        
        self.style.configure('Orange.TButton',
                           font=('Segoe UI', button_font_size, 'bold'),
                           foreground='white',
                           padding=(10, 8))
        
        self.style.map('Orange.TButton',
                      background=[('active', self.colors['light_orange']),
                                ('!active', self.colors['accent_orange'])])
        
        # Improved progressbar configuration
        try:
            self.style.configure('Orange.Horizontal.TProgressbar',
                               background=self.colors['accent_orange'],
                               troughcolor=self.colors['background'],
                               borderwidth=1,
                               focuscolor='none',
                               lightcolor=self.colors['accent_orange'],
                               darkcolor=self.colors['accent_orange'])
            
            self.style.map('Orange.Horizontal.TProgressbar',
                          background=[('active', self.colors['light_orange'])])
            
            self.progressbar_style = 'Orange.Horizontal.TProgressbar'
        except:
            self.progressbar_style = 'TProgressbar'
    
    def create_widgets(self):
        # Better padding and scaling
        padding_x = max(15, int(20 * self.scale_factor))
        padding_y = max(15, int(20 * self.scale_factor))
        
        # Main container with scrollable frame
        self.main_canvas = tk.Canvas(self.root, bg=self.colors['background'], 
                                   highlightthickness=0)
        self.main_canvas.pack(fill='both', expand=True)
        
        # Scrollbar for the canvas
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", 
                                     command=self.main_canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Frame inside canvas
        self.main_frame = tk.Frame(self.main_canvas, bg=self.colors['background'])
        self.canvas_frame = self.main_canvas.create_window((0, 0), 
                                                         window=self.main_frame, 
                                                         anchor="nw")
        
        # Content frame with proper padding
        content_frame = tk.Frame(self.main_frame, bg=self.colors['background'])
        content_frame.pack(fill='both', expand=True, padx=padding_x, pady=padding_y)
        
        # Scaled font sizes for labels
        label_font_size = self.get_scaled_font_size(9)
        small_font_size = self.get_scaled_font_size(8)
        
        # Header
        header_frame = tk.Frame(content_frame, bg=self.colors['background'])
        header_frame.pack(fill='x', pady=(0, 15))
        
        title_label = ttk.Label(header_frame, text="🦁 portapps.io Brave Updater v1.2", 
                              style='Title.TLabel')
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame, text="github.com/mirbyte", 
                                 style='Subtitle.TLabel')
        subtitle_label.pack()
        
        # Version info frame
        self.version_frame = tk.LabelFrame(content_frame, text="Version Information", 
                                         bg=self.colors['surface'], fg=self.colors['text_dark'],
                                         font=('Segoe UI', label_font_size, 'bold'), 
                                         padx=12, pady=12)
        self.version_frame.pack(fill='x', pady=(0, 12))
        
        # Better text wrapping and spacing
        label_config = {
            'bg': self.colors['surface'], 
            'fg': self.colors['text_dark'],
            'font': ('Segoe UI', label_font_size),
            'wraplength': 600,
            'justify': 'left'
        }
        
        self.current_version_label = tk.Label(self.version_frame, 
                                            text="Current Brave Version: Checking...", 
                                            **label_config)
        self.current_version_label.pack(anchor='w', pady=2)
        
        self.latest_version_label = tk.Label(self.version_frame, 
                                           text="Latest Brave Version: Checking...", 
                                           **label_config)
        self.latest_version_label.pack(anchor='w', pady=2)
        
        self.launcher_version_label = tk.Label(self.version_frame, 
                                             text="Launcher Version: Checking...", 
                                             **label_config)
        self.launcher_version_label.pack(anchor='w', pady=2)
        
        self.portable_mode_label = tk.Label(self.version_frame, 
                                          text="Mode: Detecting...", 
                                          **label_config)
        self.portable_mode_label.pack(anchor='w', pady=2)
        
        # Progress frame
        progress_frame = tk.LabelFrame(content_frame, text="Update Progress", 
                                     bg=self.colors['surface'], fg=self.colors['text_dark'],
                                     font=('Segoe UI', label_font_size, 'bold'), 
                                     padx=12, pady=12)
        progress_frame.pack(fill='x', pady=(0, 12))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                          variable=self.progress_var,
                                          maximum=100, 
                                          style=self.progressbar_style,
                                          length=400)
        self.progress_bar.pack(fill='x', pady=(0, 8))
        
        self.progress_label = tk.Label(progress_frame, text="Ready to check for updates", 
                                     bg=self.colors['surface'], fg=self.colors['text_light'],
                                     font=('Segoe UI', label_font_size),
                                     wraplength=600)
        self.progress_label.pack(anchor='w')
        
        # Log area with better sizing
        log_frame = tk.LabelFrame(content_frame, text="Activity Log", 
                                bg=self.colors['surface'], fg=self.colors['text_dark'],
                                font=('Segoe UI', label_font_size, 'bold'), 
                                padx=12, pady=12)
        log_frame.pack(fill='both', expand=True, pady=(0, 12))
        
        # Responsive log area
        log_height = max(8, min(15, int(12 * self.scale_factor)))
        console_font_size = self.get_scaled_font_size(9)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                height=log_height, 
                                                bg='#fafafa', 
                                                fg=self.colors['text_dark'],
                                                font=('Consolas', console_font_size), 
                                                wrap=tk.WORD)
        self.log_text.pack(fill='both', expand=True)
        
        # Buttons frame with better spacing
        button_frame = tk.Frame(content_frame, bg=self.colors['background'])
        button_frame.pack(fill='x', pady=(10, 0))
        
        button_spacing = max(8, int(10 * self.scale_factor))
        
        self.check_button = ttk.Button(button_frame, text="🔍 Check for Updates", 
                                     command=self.check_updates, style='Primary.TButton')
        self.check_button.pack(side='left', padx=(0, button_spacing))
        
        self.update_button = ttk.Button(button_frame, text="⬇️ Update Now", 
                                      command=self.start_update, style='Orange.TButton', 
                                      state='disabled')
        self.update_button.pack(side='left', padx=(0, button_spacing))
        
        self.close_button = ttk.Button(button_frame, text="❌ Close", 
                                     command=self.root.quit)
        self.close_button.pack(side='right')
        
        # Configure canvas scrolling
        self.main_frame.bind('<Configure>', self.on_frame_configure)
        self.main_canvas.bind('<Configure>', self.on_canvas_configure)
        
        # Mouse wheel scrolling
        self.main_canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        
        # Auto-check on startup
        self.root.after(1000, self.check_updates)
    
    def on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        """Reset the canvas window to encompass inner frame when required"""
        canvas_width = event.width
        self.main_canvas.itemconfig(self.canvas_frame, width=canvas_width)
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def setup_logging(self):
        """Original logging setup"""
        os.makedirs("log", exist_ok=True)
        self.log_file = os.path.join("log", "brave_updater_log.txt")
        self.portable_log_file = os.path.join("log", "launcher_updater_log.txt")
    
    def log_message(self, message, level='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            'info': self.colors['text_dark'],
            'success': self.colors['success'],
            'error': self.colors['error'],
            'warning': self.colors['accent_orange']
        }
        
        formatted_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        
        # Color the last line
        start_line = self.log_text.index("end-2l")
        end_line = self.log_text.index("end-1l")
        self.log_text.tag_add(level, start_line, end_line)
        self.log_text.tag_config(level, foreground=colors.get(level, colors['info']))
        
        self.root.update_idletasks()
    
    def update_progress(self, value, text=""):
        self.progress_var.set(value)
        if text:
            self.progress_label.config(text=text)
        self.root.update_idletasks()
    
    # --- PRESERVED: All original functions ---
    
    def get_latest_launcher_version(self):
        url = "https://github.com/portapps/brave-portable/releases"
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            release_tag = soup.select_one("a.Link--primary[href*='/releases/tag/']")
            if not release_tag:
                release_tag = soup.find("a", href=lambda x: x and "/releases/tag/" in x)
            if release_tag:
                latest_version = release_tag.text.strip()
                return latest_version
        except requests.RequestException as e:
            self.log_message(f"Error fetching GitHub releases: {e}", 'error')
        return None

    def download_portable_launcher(self, version, output_path):
        url = f"https://github.com/portapps/brave-portable/releases/download/{version}/brave-portable-win64.exe"
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0
            start_time = time.time()
            try:
                with open(output_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 0:
                            download_speed = downloaded_size / (elapsed_time * 1024 * 1024)
                            percent_completed = (downloaded_size / total_size) * 100 if total_size > 0 else 0
                            
                            self.update_progress(percent_completed, 
                                f"Downloading launcher: {percent_completed:.1f}% | Speed: {download_speed:.2f} MB/s")
                return True
            except Exception as e:
                self.log_message(f"Error writing launcher file: {e}", 'error')
                return False
        except requests.RequestException as e:
            self.log_message(f"Error downloading launcher from GitHub: {e}", 'error')
            return False

    def get_last_installed_version(self):
        if not os.path.exists(self.log_file):
            return None
        try:
            with open(self.log_file, "r") as file:
                last_version = file.read().strip()
            return last_version if last_version else None
        except:
            return None

    def get_last_launcher_version(self):
        if not os.path.exists(self.portable_log_file):
            return None
        try:
            with open(self.portable_log_file, "r") as file:
                last_version = file.read().strip()
            return last_version if last_version else None
        except:
            return None

    def update_log(self, version, is_launcher=False):
        log = self.portable_log_file if is_launcher else self.log_file
        with open(log, "w") as file:
            file.write(version)

    def get_latest_brave_version(self):
        url = "https://brave.com/latest/"
        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            release_notes = soup.find("h3", id=lambda x: x and x.startswith("desktop-release-notes-"))
            if release_notes:
                # version parsing
                version = release_notes.text.split("Release Notes v")[1].split()[0]
                self.log_message(f"Latest Brave version: {version}")
                return version
            else:
                self.log_message("Error: Could not find the latest Brave version on the page.", 'error')
                return None
        except requests.RequestException as e:
            self.log_message(f"Error fetching Brave release notes: {e}", 'error')
            return None

    def is_file_locked(self, file_path):
        try:
            with open(file_path, 'a'):
                return False
        except IOError:
            return True

    def download_brave_installer(self, version, output_path):
        urls = [
            f"https://brave-browser-downloads.s3.brave.com/latest/brave_installer-x64.exe",
            f"https://brave-browser-downloads.s3.brave.com/latest/brave_installer-x64.exe"
            # multiple urls for future
        ]
        for i, url in enumerate(urls):
            try:
                self.log_message(f"Downloading Brave installer from source {i+1}...")
                response = requests.get(url, stream=True)
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))
                downloaded_size = 0
                start_time = time.time()
                try:
                    with open(output_path, "wb") as file:
                        for chunk in response.iter_content(chunk_size=8192):
                            file.write(chunk)
                            downloaded_size += len(chunk)
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 0:
                                download_speed = downloaded_size / (elapsed_time * 1024 * 1024)
                                percent_completed = (downloaded_size / total_size) * 100 if total_size > 0 else 0
                                
                                self.update_progress(percent_completed, 
                                    f"Downloading Brave: {percent_completed:.1f}% | Speed: {download_speed:.2f} MB/s")
                    return True
                except Exception as e:
                    self.log_message(f"Error writing Brave installer file: {e}", 'error')
                    return False
            except requests.RequestException as e:
                self.log_message("Trying alternate source...", 'warning')
                continue
        self.log_message("All download attempts failed.", 'error')
        return False

    def extract_archive(self, archive_path, output_dir):
        seven_zip_path = os.path.join(os.getcwd(), "7zip", "7z.exe")
        if not os.path.isfile(seven_zip_path):
            self.log_message(f"Error: 7-Zip not found at {seven_zip_path}. Please ensure the 7zip folder is present.", 'error')
            return False
            
        command = [seven_zip_path, "x", archive_path, f"-o{output_dir}", "-y"]
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError as e:
            self.log_message(f"Error extracting file: {e}", 'error')
            return False

    def check_updates(self):
        def check_thread():
            # Clear the log window before starting new check
            self.log_text.delete('1.0', tk.END)
            
            self.log_message("🔍 Checking for updates...")
            self.update_progress(10, "Fetching latest Brave version...")
            
            # Check Brave version
            latest_version = self.get_latest_brave_version()
            current_version = self.get_last_installed_version()
            
            self.update_progress(30, "Checking portable mode...")
            
            # Portable mode detection
            launcher_portable_exe = os.path.join(os.getcwd(), "brave-portable.exe")
            portable_mode = os.path.exists(launcher_portable_exe)
            
            self.update_progress(50, "Checking launcher version...")
            
            launcher_version = None
            current_launcher_version = None
            if portable_mode:
                launcher_version = self.get_latest_launcher_version()
                current_launcher_version = self.get_last_launcher_version()
            
            self.update_progress(100, "Version check complete!")
            
            # Update UI on main thread
            def update_ui():
                self.current_version_label.config(
                    text=f"Current Brave Version: {current_version or 'Not installed'}")
                self.latest_version_label.config(
                    text=f"Latest Brave Version: {latest_version or 'Unknown'}")
                
                if portable_mode:
                    self.launcher_version_label.config(
                        text=f"Launcher: {current_launcher_version or 'Unknown'} → {launcher_version or 'Unknown'}")
                    self.portable_mode_label.config(text="Mode: Portable (brave-portable.exe found)")
                else:
                    self.launcher_version_label.config(text="Launcher: Not applicable")
                    self.portable_mode_label.config(text="Mode: Standard installation")
                
                # Update logic
                self.standard_update_needed = current_version != latest_version
                self.launcher_update_needed = portable_mode and launcher_version and current_launcher_version != launcher_version
                
                if not self.standard_update_needed and not self.launcher_update_needed:
                    self.log_message("Both Brave and the launcher are already up to date.", 'success')
                    if portable_mode and launcher_version:
                        self.log_message(f"Brave version: {latest_version}")
                        self.log_message(f"Launcher version: {launcher_version}")
                    self.update_button.config(state='disabled')
                else:
                    update_message = "New version available:"
                    if self.standard_update_needed:
                        update_message += f"\n- Brave: {latest_version} (Installed: {current_version or 'None'})"
                    if self.launcher_update_needed:
                        update_message += f"\n- Launcher: {launcher_version} (Installed: {current_launcher_version or 'None'})"
                    self.log_message(update_message, 'warning')
                    self.update_button.config(state='normal')
                
                self.update_progress(0, "Ready")
                
                # Store versions for update process
                self.latest_version = latest_version
                self.launcher_version = launcher_version
                self.portable_mode = portable_mode
            
            self.root.after(0, update_ui)
        
        threading.Thread(target=check_thread, daemon=True).start()

    def start_update(self):
        if self.is_updating:
            return
        
        # Confirmation dialog
        if not messagebox.askyesno("Confirm Update", 
                                 "This will download and install the latest Brave browser updates.\n"
                                 "Make sure Brave is closed before proceeding. Continue?",
                                 icon='question'):
            return
        
        self.is_updating = True
        self.update_button.config(state='disabled')
        self.check_button.config(state='disabled')
        
        def update_thread():
            try:
                self.perform_complete_update()
            finally:
                def reset_ui():
                    self.is_updating = False
                    self.update_button.config(state='disabled')
                    self.check_button.config(state='normal')
                    self.update_progress(0, "Update process completed!")
                    # Auto-check again after update
                    self.root.after(2000, self.check_updates)
                
                self.root.after(0, reset_ui)
        
        threading.Thread(target=update_thread, daemon=True).start()

    def perform_complete_update(self):
        """Complete update process from original script"""
        self.log_message("🚀 Starting update process...", 'info')
        
        launcher_updated = False
        
        # Launcher update logic
        if self.portable_mode and self.launcher_update_needed:
            self.log_message("Updating portable launcher...", 'info')
            self.update_progress(10, "Updating launcher...")
            
            temp_launcher_portable_exe = os.path.join(os.getcwd(), "brave-portable-win64.exe")
            launcher_portable_exe = os.path.join(os.getcwd(), "brave-portable.exe")
            
            if os.path.exists(temp_launcher_portable_exe):
                self.log_message("Removing old temporary files...")
                os.remove(temp_launcher_portable_exe)
                
            if self.download_portable_launcher(self.launcher_version, temp_launcher_portable_exe):
                try:
                    # Check if the current launcher is locked
                    if self.is_file_locked(launcher_portable_exe):
                        self.log_message("Error: brave-portable.exe is currently in use. Please close the application and try again.", 'error')
                        return

                    backup_launcher = os.path.join(os.getcwd(), "brave-portable.exe.bak")
                    if os.path.exists(launcher_portable_exe):
                        shutil.copy2(launcher_portable_exe, backup_launcher)
                    if os.path.exists(launcher_portable_exe):
                        os.remove(launcher_portable_exe)
                    os.rename(temp_launcher_portable_exe, launcher_portable_exe)
                    self.log_message("brave-portable.exe updated successfully.", 'success')
                    launcher_updated = True
                    if launcher_updated:
                        self.update_log(self.launcher_version, is_launcher=True)
                        if not self.standard_update_needed:
                            self.log_message("Launcher update completed!", 'success')
                            return

                except Exception as e:
                    self.log_message(f"Error updating brave-portable.exe: {e}", 'error')
                    self.log_message("Attempting to restore from backup...")
                    if os.path.exists(backup_launcher):
                        try:
                            shutil.copy2(backup_launcher, launcher_portable_exe)
                            self.log_message("Restored from backup successfully.")
                        except Exception as restore_error:
                            self.log_message(f"Failed to restore from backup: {restore_error}", 'error')
                    self.log_message("brave-portable.exe update failed.", 'error')
            else:
                self.log_message("Failed to download the launcher.", 'error')

        # Brave update logic
        if hasattr(self, 'standard_update_needed') and self.standard_update_needed:
            self.log_message("Updating Brave browser files...", 'info')
            self.update_progress(30, "Downloading Brave installer...")
            
            installer_exe = os.path.join(os.getcwd(), "brave_setup.exe")
            if os.path.exists(installer_exe):
                os.remove(installer_exe)
                
            if not self.download_brave_installer(self.latest_version, installer_exe):
                self.log_message("Failed to download latest Brave. Exiting.", 'error')
                return
                
            self.update_progress(50, "Extracting installer...")
            
            exe_extract_folder = os.path.join(os.getcwd(), "portable-temp")
            if os.path.exists(exe_extract_folder):
                shutil.rmtree(exe_extract_folder)
            os.makedirs(exe_extract_folder, exist_ok=True)

            if not self.extract_archive(installer_exe, exe_extract_folder):
                self.log_message("Failed to extract installer. 7zip error?", 'error')
                return
                
            self.update_progress(60, "Finding chrome.7z...")
            
            # Look for chrome.7z in the extracted files
            chrome_7z_path = None
            for root, dirs, files in os.walk(exe_extract_folder):
                for file in files:
                    if file.lower() == "chrome.7z":
                        chrome_7z_path = os.path.join(root, file)
                        break
                if chrome_7z_path:
                    break
                    
            if not chrome_7z_path:
                self.log_message("Error: chrome.7z not found in extracted files! Problem with extraction process.", 'error')
                return
                
            self.update_progress(70, "Extracting chrome.7z...")
            
            chrome_extract_folder = os.path.join(os.getcwd(), "chrome-temp")
            if os.path.exists(chrome_extract_folder):
                shutil.rmtree(chrome_extract_folder)
            os.makedirs(chrome_extract_folder, exist_ok=True)
            
            if not self.extract_archive(chrome_7z_path, chrome_extract_folder):
                self.log_message("Failed to extract chrome.7z. 7zip error?", 'error')
                return
            
            self.update_progress(80, "Finding chrome-bin folder...")
            
            chrome_bin_path = None
            for root, dirs, files in os.walk(chrome_extract_folder):
                for dir in dirs:
                    if dir.lower() == "chrome-bin":
                        chrome_bin_path = os.path.join(root, dir)
                        break
                if chrome_bin_path:
                    break
                    
            if not chrome_bin_path:
                self.log_message("Error: Chrome-bin folder not found in extracted chrome.7z!", 'error')
                return

            # Check if brave.exe exists
            brave_found = False
            for root, dirs, files in os.walk(chrome_bin_path):
                for file in files:
                    if file.lower() == "brave.exe":
                        brave_found = True
                        break
                if brave_found:
                    break
            if not brave_found:
                self.log_message("Error: brave.exe not found in Chrome-bin folder! Problem with extraction process.", 'error')
                return

            self.update_progress(90, "Creating backup and copying files...")
            
            app_folder = os.path.join(os.getcwd(), "app")
            backup_folder = os.path.join(os.getcwd(), f"app-backup-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}")
            
            if os.path.exists(app_folder):
                shutil.copytree(app_folder, backup_folder)
            else:
                os.makedirs(app_folder, exist_ok=True)

            # Copy files
            if os.path.exists(app_folder):
                shutil.rmtree(app_folder)
            shutil.copytree(chrome_bin_path, app_folder)
            self.log_message("Files copied successfully.", 'success')
                        
            # Clean up temporary files
            self.update_progress(95, "Cleaning up temporary files...")
            temp_files = [exe_extract_folder, chrome_extract_folder, installer_exe]
            for temp in temp_files:
                if os.path.exists(temp):
                    if os.path.isdir(temp):
                        shutil.rmtree(temp)
                    else:
                        os.remove(temp)

            self.update_log(self.latest_version)
            self.log_message("Brave files updated.", 'success')

        # Cleanup backup files
        self.update_progress(98, "Cleaning up backup files...")
        backup_files = []
        launcher_backup = os.path.join(os.getcwd(), "brave-portable.exe.bak")
        if os.path.exists(launcher_backup):
            backup_files.append(launcher_backup)

        for item in os.listdir(os.getcwd()):
            if item.startswith("app-backup-") and os.path.isdir(os.path.join(os.getcwd(), item)):
                backup_files.append(os.path.join(os.getcwd(), item))

        for backup in backup_files:
            try:
                if os.path.isdir(backup):
                    shutil.rmtree(backup)
                else:
                    os.remove(backup)
            except Exception as e:
                self.log_message(f"Failed to delete {backup}: {e}", 'warning')

        self.update_progress(100, "Update completed!")
        self.log_message("✅ Update process completed successfully!", 'success')
        messagebox.showinfo("Update Complete", "Brave browser has been updated successfully!")

def main():
    root = tk.Tk()
    app = BraveUpdaterGUI(root)
    try:
        root.iconbitmap("brave.ico")
    except:
        pass
    
    root.mainloop()

if __name__ == "__main__":
    main()
