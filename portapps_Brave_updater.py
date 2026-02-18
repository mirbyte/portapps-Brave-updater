import os
import sys
import shutil
import requests
from datetime import datetime
import time
from bs4 import BeautifulSoup
import subprocess

os.system('title portapps.io Brave updater v1.2 (mirbyte)')
print("github/mirbyte")
print("")
print("")

# --- Constants ---
TIMEOUT_PAGE = 10
TIMEOUT_DOWNLOAD = (10, 60)

# --- Logging setup ---
os.makedirs("log", exist_ok=True)
log_file = os.path.join("log", "brave_updater_log.txt")
portable_log_file = os.path.join("log", "launcher_updater_log.txt")
event_log_file = os.path.join("log", "updater_events.log")

with open(event_log_file, "w") as f:
    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] INFO: Updater started\n")

def log(level, msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {level}: {msg}"
    if level == "ERROR":
        print(line)
    with open(event_log_file, "a") as f:
        f.write(line + "\n")

# --- Version log helpers ---
def get_last_installed_version():
    if not os.path.exists(log_file):
        return None
    with open(log_file, "r") as file:
        last_version = file.read().strip()
    return last_version if last_version else None

def get_last_launcher_version():
    if not os.path.exists(portable_log_file):
        return None
    with open(portable_log_file, "r") as file:
        last_version = file.read().strip()
    return last_version if last_version else None

def update_log(version, is_launcher=False):
    target = portable_log_file if is_launcher else log_file
    with open(target, "w") as file:
        file.write(version)

# --- Version fetchers ---
def get_latest_launcher_version():
    url = "https://github.com/portapps/brave-portable/releases"
    try:
        response = requests.get(url, timeout=TIMEOUT_PAGE)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        release_tag = soup.select_one("a.Link--primary[href*='/releases/tag/']")
        if not release_tag:
            release_tag = soup.find("a", href=lambda x: x and "/releases/tag/" in x)
        if release_tag:
            return release_tag.text.strip()
        log("ERROR", "Could not find launcher version tag on GitHub releases page")
        return None
    except requests.RequestException as e:
        log("ERROR", f"Error fetching GitHub releases: {e}")
        return None

def get_latest_brave_version():
    url = "https://brave.com/latest/"
    try:
        response = requests.get(url, timeout=TIMEOUT_PAGE)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        release_notes = soup.find("h3", id=lambda x: x and x.startswith("desktop-release-notes-"))
        if release_notes:
            try:
                version = release_notes.text.split("Release Notes v")[1].split()[0]
                print(f"Latest Brave version on website: {version}")
                print("")
                log("INFO", f"Latest Brave version: {version}")
                return version
            except (IndexError, AttributeError) as e:
                log("ERROR", f"Failed to parse Brave version from page text: {e}")
                return None
        log("ERROR", "Could not find the latest Brave version on the page")
        return None
    except requests.RequestException as e:
        log("ERROR", f"Error fetching Brave release notes: {e}")
        return None

# --- Downloaders ---
def download_portable_launcher(version, output_path):
    url = f"https://github.com/portapps/brave-portable/releases/download/{version}/brave-portable-win64.exe"
    try:
        response = requests.get(url, stream=True, timeout=TIMEOUT_DOWNLOAD)
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
                    download_speed = downloaded_size / (elapsed_time * 1024 * 1024)
                    percent_completed = (downloaded_size / total_size) * 100
                    print(f"Downloaded: {percent_completed:.2f}% | Speed: {download_speed:.2f} MB/s", end="\r")
            return True
        except Exception as e:
            log("ERROR", f"Error writing launcher file: {e}")
            return False
    except requests.RequestException as e:
        log("ERROR", f"Error downloading launcher from GitHub: {e}")
        return False

def download_brave_installer(version, output_path):
    urls = [
        "https://brave-browser-downloads.s3.brave.com/latest/brave_installer-x64.exe",
        "https://brave-browser-downloads.s3.brave.com/latest/brave_installer-x64.exe",  # TODO: add alternate URL
    ]
    for i, url in enumerate(urls):
        try:
            response = requests.get(url, stream=True, timeout=TIMEOUT_DOWNLOAD)
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            if total_size < 1024 * 1024:
                log("ERROR", f"Downloaded file is suspiciously small ({total_size} bytes) - likely a redirect or error page")
                print("\nError: Downloaded file is too small, the download URL may have changed.")
                return False
            downloaded_size = 0
            start_time = time.time()
            try:
                with open(output_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        elapsed_time = time.time() - start_time
                        download_speed = downloaded_size / (elapsed_time * 1024 * 1024)
                        percent_completed = (downloaded_size / total_size) * 100
                        print(f"Downloaded: {percent_completed:.2f}% | Speed: {download_speed:.2f} MB/s", end="\r")
                return True
            except Exception as e:
                log("ERROR", f"Error writing installer file: {e}")
                return False
        except requests.RequestException as e:
            if i < len(urls) - 1:
                print("\nTrying alternate source...")
            else:
                log("ERROR", f"All download attempts failed: {e}")
    return False

# --- Utilities ---
def is_file_locked(filepath):
    try:
        with open(filepath, "a"):
            return False
    except IOError:
        return True

def is_process_running(process_name):
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {process_name}"],
            capture_output=True, text=True
        )
        return process_name.lower() in result.stdout.lower()
    except Exception:
        return False

def rmtree_with_retry(path, retries=5, delay=2):
    """Retry rmtree several times with a delay - handles briefly locked files on Windows."""
    for attempt in range(retries):
        try:
            shutil.rmtree(path)
            return True
        except Exception:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise
    return False

def extract_archive(archive_path, output_dir):
    seven_zip_path = os.path.join(os.getcwd(), "7zip", "7z.exe")
    if not os.path.isfile(seven_zip_path):
        log("ERROR", f"7-Zip not found at {seven_zip_path}")
        return False
    command = [seven_zip_path, "x", archive_path, f"-o{output_dir}", "-y"]
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as e:
        log("ERROR", f"7-Zip extraction failed: {e}")
        return False

def find_file_or_folder(base_path, target_name, find_dir=False):
    """Case-insensitive search for a file or folder anywhere under base_path."""
    for root, dirs, files in os.walk(base_path):
        targets = dirs if find_dir else files
        for item in targets:
            if item.lower() == target_name.lower():
                return os.path.join(root, item)
    return None

# --- Main logic ---
current_folder = os.path.basename(os.getcwd())
if "brave" not in current_folder.lower():
    log("ERROR", "Script not run from a folder containing 'brave' in its name")
    print("Error: This script must be run from a folder containing 'brave' in its name.")
    print("Make sure you have moved this script to the right location.")
    input("\nPress Enter to exit...")
    sys.exit(1)

latest_version = get_latest_brave_version()
if not latest_version:
    print("Failed to fetch the latest Brave version. Exiting.")
    input("\nPress Enter to exit...")
    sys.exit(1)

launcher_portable_exe = os.path.join(os.getcwd(), "brave-portable.exe")
portable_mode = os.path.exists(launcher_portable_exe)
launcher_version = None

if portable_mode:
    launcher_version = get_latest_launcher_version()
    if not launcher_version:
        log("ERROR", "Failed to fetch latest launcher version - will only update Brave files")
        print("Failed to fetch the latest launcher version. Will only update official Brave files.")

last_installed_version = get_last_installed_version()
last_launcher_version = get_last_launcher_version()
standard_update_needed = last_installed_version != latest_version
launcher_update_needed = portable_mode and launcher_version and last_launcher_version != launcher_version

if not standard_update_needed and not launcher_update_needed:
    print("Both Brave and the launcher are already up to date.")
    if portable_mode and launcher_version:
        print(f"Brave version: {latest_version}")
        print(f"Launcher version: {launcher_version}")
    log("INFO", "Already up to date - no updates needed")
    input("\nPress Enter to exit...")
    sys.exit(0)

update_message = "New version available:"
if standard_update_needed:
    installed_display = last_installed_version or "None"
    update_message += f"\n- Brave: {latest_version} (Installed: {installed_display})"
if launcher_update_needed:
    launcher_display = last_launcher_version or "None"
    update_message += f"\n- Launcher: {launcher_version} (Installed: {launcher_display})"
print(update_message)
log("INFO", update_message.replace("\n", " | "))

launcher_updated = False

if portable_mode and launcher_update_needed:
    temp_launcher_portable_exe = os.path.join(os.getcwd(), "brave-portable-win64.exe")
    if os.path.exists(temp_launcher_portable_exe):
        print("Removing old temporary files...")
        os.remove(temp_launcher_portable_exe)
    if download_portable_launcher(launcher_version, temp_launcher_portable_exe):
        try:
            if is_file_locked(launcher_portable_exe):
                log("ERROR", "brave-portable.exe is in use - cannot update launcher")
                print("Error: brave-portable.exe is currently in use. Please close the application and try again.")
                sys.exit(1)
            backup_launcher = os.path.join(os.getcwd(), "brave-portable.exe.bak")
            if os.path.exists(launcher_portable_exe):
                shutil.copy2(launcher_portable_exe, backup_launcher)
                os.remove(launcher_portable_exe)
            os.rename(temp_launcher_portable_exe, launcher_portable_exe)
            print("brave-portable.exe updated successfully.")
            log("INFO", f"Launcher updated to {launcher_version}")
            launcher_updated = True
            update_log(launcher_version, is_launcher=True)
            if not standard_update_needed:
                input("\nPress Enter to exit...")
                sys.exit(0)
        except Exception as e:
            log("ERROR", f"Error updating brave-portable.exe: {e}")
            print(f"Error updating brave-portable.exe: {e}")
            print("Attempting to restore from backup...")
            if os.path.exists(backup_launcher):
                try:
                    shutil.copy2(backup_launcher, launcher_portable_exe)
                    print("Restored from backup successfully.")
                    log("INFO", "Launcher restored from backup")
                except Exception as restore_error:
                    log("ERROR", f"Failed to restore launcher from backup: {restore_error}")
                    print(f"Failed to restore from backup: {restore_error}")
            print("brave-portable.exe update failed.")
    else:
        print("Failed to download the launcher.")

if standard_update_needed:
    installer_exe = os.path.join(os.getcwd(), "brave_setup.exe")
    if os.path.exists(installer_exe):
        os.remove(installer_exe)

    if not download_brave_installer(latest_version, installer_exe):
        log("ERROR", "Failed to download Brave installer")
        print("Failed to download latest Brave. Exiting.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    print("")
    print("Extracting installer...")
    log("INFO", "Extracting installer")

    exe_extract_folder = os.path.join(os.getcwd(), "portable-temp")
    if os.path.exists(exe_extract_folder):
        shutil.rmtree(exe_extract_folder)
    os.makedirs(exe_extract_folder, exist_ok=True)

    seven_zip_path = os.path.join(os.getcwd(), "7zip", "7z.exe")
    if not os.path.isfile(seven_zip_path):
        log("ERROR", f"7-Zip not found at {seven_zip_path}")
        print(f"Error: 7-Zip not found at {seven_zip_path}. Please ensure the 7zip folder is present.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    if not extract_archive(installer_exe, exe_extract_folder):
        log("ERROR", "Failed to extract Brave installer")
        print("Failed to extract installer. 7-Zip error?")
        input("\nPress Enter to exit...")
        sys.exit(1)

    chrome_7z_path = find_file_or_folder(exe_extract_folder, "chrome.7z", find_dir=False)
    if not chrome_7z_path:
        log("ERROR", "chrome.7z not found in extracted installer - Brave may have changed their installer structure")
        print("Error: chrome.7z not found in extracted files. Brave may have changed their installer structure.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    print("Extracting chrome.7z...")
    log("INFO", "Extracting chrome.7z")

    chrome_extract_folder = os.path.join(os.getcwd(), "chrome-temp")
    if os.path.exists(chrome_extract_folder):
        shutil.rmtree(chrome_extract_folder)
    os.makedirs(chrome_extract_folder, exist_ok=True)

    if not extract_archive(chrome_7z_path, chrome_extract_folder):
        log("ERROR", "Failed to extract chrome.7z")
        print("Failed to extract chrome.7z. 7-Zip error?")
        input("\nPress Enter to exit...")
        sys.exit(1)

    chrome_bin_path = find_file_or_folder(chrome_extract_folder, "chrome-bin", find_dir=True)
    if not chrome_bin_path:
        log("ERROR", "Chrome-bin folder not found in extracted chrome.7z - Brave may have changed their installer structure")
        print("Error: Chrome-bin folder not found. Brave may have changed their installer structure.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    brave_exe_path = find_file_or_folder(chrome_bin_path, "brave.exe", find_dir=False)
    if not brave_exe_path:
        log("ERROR", "brave.exe not found in Chrome-bin - extraction may be corrupt")
        print("Error: brave.exe not found in Chrome-bin. Extraction may be corrupt.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    if is_process_running("brave.exe"):
        log("ERROR", "brave.exe is running - cannot replace app folder files")
        print("Error: Brave is currently running. Please close Brave and run the updater again.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    app_folder = os.path.join(os.getcwd(), "app")
    backup_folder = os.path.join(os.getcwd(), f"app-backup-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}")

    print("Backing up current app folder...")
    log("INFO", f"Backing up app folder to {os.path.basename(backup_folder)}")
    if os.path.exists(app_folder):
        shutil.copytree(app_folder, backup_folder)
    else:
        os.makedirs(app_folder, exist_ok=True)

    print("Copying new files...")
    log("INFO", "Copying new Brave files to app folder")
    try:
        if os.path.exists(app_folder):
            rmtree_with_retry(app_folder)
        shutil.copytree(chrome_bin_path, app_folder)
    except Exception as e:
        log("ERROR", f"Failed to copy new files to app folder: {e}")
        print(f"Error copying files: {e}")
        print("Attempting to restore from backup...")
        try:
            if os.path.exists(app_folder):
                rmtree_with_retry(app_folder)
            shutil.copytree(backup_folder, app_folder)
            print("Restored from backup successfully.")
            log("INFO", "App folder restored from backup")
        except Exception as restore_error:
            log("ERROR", f"Failed to restore app folder from backup: {restore_error}")
            print(f"Failed to restore from backup: {restore_error}")
        input("\nPress Enter to exit...")
        sys.exit(1)

    print("Files copied successfully.")
    log("INFO", f"Brave updated to {latest_version}")
    update_log(latest_version)

    print("Cleaning up temporary files...")
    temp_files = [exe_extract_folder, chrome_extract_folder, installer_exe]
    for temp in temp_files:
        if os.path.exists(temp):
            try:
                shutil.rmtree(temp) if os.path.isdir(temp) else os.remove(temp)
            except Exception as e:
                log("ERROR", f"Failed to delete temp file {temp}: {e}")

    backup_files = []
    launcher_backup = os.path.join(os.getcwd(), "brave-portable.exe.bak")
    if os.path.exists(launcher_backup):
        backup_files.append(launcher_backup)
    for item in os.listdir(os.getcwd()):
        if item.startswith("app-backup-") and os.path.isdir(os.path.join(os.getcwd(), item)):
            backup_files.append(os.path.join(os.getcwd(), item))
    for backup in backup_files:
        try:
            shutil.rmtree(backup) if os.path.isdir(backup) else os.remove(backup)
        except Exception as e:
            log("ERROR", f"Failed to delete backup {backup}: {e}")

    print("")
    print("Update complete.")
    log("INFO", "Update complete")

print("")
print("")
print("")
input("\nPress Enter to exit...")
