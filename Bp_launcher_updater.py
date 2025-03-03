import subprocess
import os
import sys
import shutil
import requests
from datetime import datetime
import time
from bs4 import BeautifulSoup



os.system('title portapps.io brave-portable.exe updater v1.0 (mirbyte)')

os.makedirs("log", exist_ok=True)
log_file = os.path.join(os.getcwd(), "log", "launcher_updater_log.txt")


def normalize_version(version_str):
    if version_str and isinstance(version_str, str) and version_str.startswith('v'):
        return version_str[1:]
    return version_str


def get_last_installed_version():
    if not os.path.exists(log_file):
        return None
    
    with open(log_file, "r") as file:
        lines = file.readlines()
        for line in reversed(lines):
            if "Updated to version:" in line:
                return line.split("Updated to version:")[-1].strip()
    return None


def update_log(message):
    today_str = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a") as file:
        file.write(f"{today_str}: {message}\n")


def get_latest_github_version():
    url = "https://github.com/portapps/brave-portable/releases"
    try:
        print("Fetching latest version from GitHub releases...")
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        release_tag = soup.select_one("a.Link--primary[href*='/releases/tag/']")
        if not release_tag:
            # fallback to original
            release_tag = soup.find("a", href=lambda x: x and "/releases/tag/" in x)
        
        if release_tag:
            latest_version = release_tag.text.strip()
            print(f"Latest Brave Portable version on GitHub: {latest_version}")
            return latest_version
    except requests.RequestException as e:
        print(f"Error fetching GitHub releases: {e}")
    return None


def is_file_locked(file_path):
    try:
        with open(file_path, 'a'):
            return False
    except IOError:
        return True


def download_brave_portable(version):
    base_url = f"https://github.com/portapps/brave-portable/releases/download/{version}"
    filenames = ["brave-portable-win64.exe", "brave-portable.exe"]
    
    for filename in filenames:
        download_url = f"{base_url}/{filename}"
        output_path = os.path.join(os.getcwd(), filename)
        
        try:
            print("")
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0
            start_time = time.time()
            
            with open(output_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    elapsed_time = time.time() - start_time
                    percent_completed = (downloaded_size / total_size) * 100 if total_size else 100
                    print(f"Downloaded: {percent_completed:.2f}%", end="\r")
            
            if filename == "brave-portable-win64.exe":
                new_output_path = os.path.join(os.getcwd(), "brave-portable.exe")
                if os.path.exists(new_output_path):
                    print("Removing old brave-portable.exe...")
                    os.remove(new_output_path)
                
                # retry renaming
                for _ in range(5):
                    if not is_file_locked(output_path):
                        os.rename(output_path, new_output_path)
                        print("Renamed the .exe")
                        return True
                    print("File is locked, retrying in 2 seconds...")
                    time.sleep(2)
                
                print("Failed to rename after multiple attempts. Please close any process using the file and try again.")
                return False
        except requests.RequestException as e:
            print(f"\nError downloading {filename}: {e}")
    return False

# Main execution
latest_version = get_latest_github_version()
if not latest_version:
    print("Failed to fetch the latest Brave Portable version. Exiting.")
    input("\nPress Enter to exit...")
    sys.exit(1)

last_installed_version = get_last_installed_version()

if normalize_version(last_installed_version) == normalize_version(latest_version):
    print("Brave Portable is already up to date.")
    update_log(f"No update needed. Current version: {last_installed_version}, Latest version: {latest_version}")
    input("\nPress Enter to exit...")
    sys.exit(0)


if not download_brave_portable(latest_version):
    print("Failed to download the latest Brave Portable version. Exiting.")
    input("\nPress Enter to exit...")
    sys.exit(1)


if normalize_version(get_last_installed_version()) != normalize_version(latest_version):
    update_log(f"Updated to version: {latest_version}")
    print("Update completed.")
else:
    print("Version was already updated, skipping duplicate log entry.")

print("")
input("\nPress Enter to exit...")
