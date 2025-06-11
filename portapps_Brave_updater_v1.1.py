import os
import sys
import shutil
import requests
from datetime import datetime
import time
from bs4 import BeautifulSoup
import subprocess


os.system('title portapps.io Brave updater v1.1 (mirbyte)')


def get_latest_launcher_version():
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
        print(f"Error fetching GitHub releases: {e}")
    return None


def download_portable_launcher(version, output_path):
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
                    download_speed = downloaded_size / (elapsed_time * 1024 * 1024)
                    percent_completed = (downloaded_size / total_size) * 100
                    
                    print(
                        f"Downloaded: {percent_completed:.2f}% | "
                        f"Speed: {download_speed:.2f} MB/s",
                        end="\r",
                    )
            return True
        except Exception as e:
            print(f"\nError writing file: {e}")
            return False
    except requests.RequestException as e:
        print(f"\nError downloading from GitHub: {e}")
        return False



# Logging setup
os.makedirs("log", exist_ok=True)
log_file = os.path.join("log", "brave_updater_log.txt")
portable_log_file = os.path.join("log", "launcher_updater_log.txt")


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
    log = portable_log_file if is_launcher else log_file
    with open(log, "w") as file:
        file.write(version)


def get_latest_brave_version():
    url = "https://brave.com/latest/"
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # first <h3> tag with an id starting with "desktop-release-notes-"
        release_notes = soup.find("h3", id=lambda x: x and x.startswith("desktop-release-notes-"))
        if release_notes:
            # version number from the text
            version = release_notes.text.split("Release Notes v")[1].split()[0]
            print(f"Latest Brave version: {version}")
            print("")
            print("")
            return version
        else:
            print("Error: Could not find the latest Brave version on the page.")
            return None
    except requests.RequestException as e:
        print(f"Error fetching Brave release notes: {e}")
        return None


def is_file_locked(file_path):
    try:
        with open(file_path, 'a'):
            return False
    except IOError:
        return True


def download_brave_installer(version, output_path):
    urls = [
        # add more later
        f"https://brave-browser-downloads.s3.brave.com/latest/brave_installer-x64.exe",
        f"https://brave-browser-downloads.s3.brave.com/latest/brave_installer-x64.exe"
    ]
    for i, url in enumerate(urls):
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
                        download_speed = downloaded_size / (elapsed_time * 1024 * 1024)
                        percent_completed = (downloaded_size / total_size) * 100
                        
                        print(
                            f"Downloaded: {percent_completed:.2f}% | "
                            f"Speed: {download_speed:.2f} MB/s",
                            end="\r",
                        )
                return True
            except Exception as e:
                print(f"\nError writing file: {e}")
                return False
        except requests.RequestException as e:
            print("Trying alternate source...")
            continue
    print("All download attempts failed.")
    return False

# Main script logic
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
    input("\nPress Enter to exit...")
    sys.exit(0)

update_message = "New version available:"
if standard_update_needed:
    update_message += f"\n- Brave: {latest_version} (Installed: {last_installed_version or 'None'})"
if launcher_update_needed:
    update_message += f"\n- Launcher: {launcher_version} (Installed: {last_launcher_version or 'None'})"
print(update_message)

# Check if the script is running from the correct folder
current_folder = os.path.basename(os.getcwd())
if "brave" not in current_folder.lower():
    print("Error: This script must be run from a folder containing 'brave' in its name. Make sure you have moved this script to the right location.")
    input("\nPress Enter to exit...")
    sys.exit(1)


launcher_updated = False


if portable_mode and launcher_update_needed:
    temp_launcher_portable_exe = os.path.join(os.getcwd(), "brave-portable-win64.exe")
    if os.path.exists(temp_launcher_portable_exe):
        print("Removing old temporary files...")
        os.remove(temp_launcher_portable_exe)
    if download_portable_launcher(launcher_version, temp_launcher_portable_exe):
        try:
            # Check if the current launcher is locked
            if is_file_locked(launcher_portable_exe):
                print("Error: brave-portable.exe is currently in use. Please close the application and try again.")
                sys.exit(1)

            backup_launcher = os.path.join(os.getcwd(), "brave-portable.exe.bak")
            if os.path.exists(launcher_portable_exe):
                shutil.copy2(launcher_portable_exe, backup_launcher)
            if os.path.exists(launcher_portable_exe):
                os.remove(launcher_portable_exe)
            os.rename(temp_launcher_portable_exe, launcher_portable_exe)
            print("brave-portable.exe updated successfully.")
            launcher_updated = True
            if launcher_updated:
                update_log(launcher_version, is_launcher=True)
                if not standard_update_needed:
                    input("\nPress Enter to exit...")
                    sys.exit(0)

        except Exception as e:
            print(f"Error updating brave-portable.exe: {e}")
            print("Attempting to restore from backup...")
            if os.path.exists(backup_launcher):
                try:
                    shutil.copy2(backup_launcher, launcher_portable_exe)
                    print("Restored from backup successfully.")
                except Exception as restore_error:
                    print(f"Failed to restore from backup: {restore_error}")
            print("brave-portable.exe update failed.")
    else:
        print("Failed to download the launcher.")


if standard_update_needed:
    installer_exe = os.path.join(os.getcwd(), "brave_setup.exe")
    if os.path.exists(installer_exe):
        os.remove(installer_exe)
    if not download_brave_installer(latest_version, installer_exe):
        print("Failed to download latest Brave. Exiting.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    exe_extract_folder = os.path.join(os.getcwd(), "portable-temp")
    if os.path.exists(exe_extract_folder):
        shutil.rmtree(exe_extract_folder)
    os.makedirs(exe_extract_folder, exist_ok=True)
    seven_zip_path = os.path.join(os.getcwd(), "7zip", "7z.exe")
    if not os.path.isfile(seven_zip_path):
        print(f"Error: 7-Zip not found at {seven_zip_path}. Please ensure the 7zip folder is present.")
        input("\nPress Enter to exit...")
        sys.exit(1)
        
    def extract_archive(archive_path, output_dir):
        command = [seven_zip_path, "x", archive_path, f"-o{output_dir}", "-y"]
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error extracting file: {e}")
            return False

    if not extract_archive(installer_exe, exe_extract_folder):
        print("Failed to extract installer. 7zip error?")
        input("\nPress Enter to exit...")
        sys.exit(1)
        
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
        print("Error: chrome.7z not found in extracted files! Problem with extraction process.")
        input("\nPress Enter to exit...")
        sys.exit(1)
        
    chrome_extract_folder = os.path.join(os.getcwd(), "chrome-temp")
    if os.path.exists(chrome_extract_folder):
        shutil.rmtree(chrome_extract_folder)
    os.makedirs(chrome_extract_folder, exist_ok=True)
    
    if not extract_archive(chrome_7z_path, chrome_extract_folder):
        print("Failed to extract chrome.7z. 7zip error?")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    chrome_bin_path = None
    for root, dirs, files in os.walk(chrome_extract_folder):
        for dir in dirs:
            if dir.lower() == "chrome-bin":
                chrome_bin_path = os.path.join(root, dir)
                break
        if chrome_bin_path:
            break
            
    if not chrome_bin_path:
        print("Error: Chrome-bin folder not found in extracted chrome.7z!")
        input("\nPress Enter to exit...")
        sys.exit(1)

    app_folder = os.path.join(os.getcwd(), "app")
    backup_folder = os.path.join(os.getcwd(), f"app-backup-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}")
    
    if os.path.exists(app_folder):
        shutil.copytree(app_folder, backup_folder)
    else:
        os.makedirs(app_folder, exist_ok=True)

    # Check if brave.exe exists, so we are on the right path
    brave_found = False
    for root, dirs, files in os.walk(chrome_bin_path):
        for file in files:
            if file.lower() == "brave.exe":
                brave_found = True
                break
        if brave_found:
            break
    if not brave_found:
        print("Error: brave.exe not found in Chrome-bin folder! Problem with extraction process.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Copy files
    if os.path.exists(app_folder):
        shutil.rmtree(app_folder)
    shutil.copytree(chrome_bin_path, app_folder)
    print("Files copied successfully.")
                
    # Clean up temporary files
    temp_files = [exe_extract_folder, chrome_extract_folder, installer_exe]
    for temp in temp_files:
        if os.path.exists(temp):
            shutil.rmtree(temp) if os.path.isdir(temp) else os.remove(temp)

    update_log(latest_version)
    print("\nBrave files updated.")


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
        print(f"Failed to delete {backup}: {e}")


print("")
print("")
print("")
input("\nPress Enter to exit...")
