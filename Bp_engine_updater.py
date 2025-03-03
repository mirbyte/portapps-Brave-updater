import os
import sys
import shutil
import requests
from datetime import datetime, timedelta
import time
from bs4 import BeautifulSoup
import subprocess

os.system('title portapps.io brave chromium updater v1.0 (mirbyte)')


os.makedirs("log", exist_ok=True)
log_file = os.path.join("log", "chromium_updater_log.txt")


def can_run_installer():
    if not os.path.exists(log_file):
        return True

    with open(log_file, "r") as file:
        last_run_date_str = file.read().strip()

    try:
        last_run_date = datetime.strptime(last_run_date_str, "%Y-%m-%d")
        today = datetime.now().date()
        return last_run_date.date() < today
    except ValueError:
        return True


def update_log():
    today_str = datetime.now().strftime("%Y-%m-%d")
    with open(log_file, "w") as file:
        file.write(today_str)


def get_latest_brave_version():
    url = "https://brave.com/latest/"
    try:
        print("*THIS SCRIPT HAS NO ABILITY TO CHECK INSTALLED VERSION*")
        print("")
        print("")
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
            return version
        else:
            print("Error: Could not find the latest Brave version on the page.")
            return None
    except requests.RequestException as e:
        print(f"Error fetching Brave release notes: {e}")
        return None


if not can_run_installer():
    print("The installer can only be run once per day. Please try again tomorrow.")
    input("\nPress Enter to exit...")
    sys.exit(1)


current_folder = os.path.basename(os.getcwd())
if "brave" not in current_folder.lower():
    print("Error: This script must be run from a folder containing 'brave' in its name.")
    input("\nPress Enter to exit...")
    sys.exit(1)


# paths
seven_zip_path = os.path.join(os.getcwd(), "7zip", "7z.exe")
exe_archive = os.path.join(os.getcwd(), "brave_installer-x64.exe")
update_temp_folder = os.path.join(os.getcwd(), "update-temp")
app_folder = os.path.join(os.getcwd(), "app")
backup_folder = os.path.join(os.getcwd(), f"app-backup-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}")


if not os.path.isfile(seven_zip_path):
    print(f"Error: 7-Zip not found at {seven_zip_path}. Please ensure the 7zip folder is present.")
    input("\nPress Enter to exit...")
    sys.exit(1)


def download_brave_installer(url, output_path):
    try:
        print(f"Downloading Brave installer from {url}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))
        downloaded_size = 0
        start_time = time.time()

        with open(output_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
                downloaded_size += len(chunk)
                elapsed_time = time.time() - start_time
                download_speed = downloaded_size / (elapsed_time * 1024 * 1024)  # Speed in MB/s
                percent_completed = (downloaded_size / total_size) * 100

                print(
                    f"Downloaded: {percent_completed:.2f}% | "
                    f"Speed: {download_speed:.2f} MB/s",
                    end="\r",
                )

        print("\n")
        print("")
    except requests.RequestException as e:
        print(f"\nError downloading Brave installer: {e}")
        return False
    return True


latest_version = get_latest_brave_version()
if not latest_version:
    print("Failed to fetch the latest Brave version. Exiting.")
    input("\nPress Enter to exit...")
    sys.exit(1)


if os.path.exists(exe_archive):
    print(f"Old Brave installer found at {exe_archive}. Deleting it...")
    os.remove(exe_archive)
    print("Old Brave installer deleted.")


if not os.path.isfile(exe_archive):
    brave_installer_url = f"https://brave-browser-downloads.s3.brave.com/latest/brave_installer-x64.exe"
    if not download_brave_installer(brave_installer_url, exe_archive):
        print("Failed to download Brave installer. Exiting.")
        input("\nPress Enter to exit...")
        sys.exit(1)


os.makedirs(update_temp_folder, exist_ok=True)


def extract_archive(archive_path, output_dir):
    command = [seven_zip_path, "x", archive_path, f"-o{output_dir}", "-y"]
    try:
        # Redirect output to subprocess.DEVNULL to suppress logs
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Extraction completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error extracting file: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False
    return True


if not extract_archive(exe_archive, update_temp_folder):
    print("Failed to extract the Brave installer. Exiting.")
    input("\nPress Enter to exit...")
    sys.exit(1)


chrome_7z_path = os.path.join(update_temp_folder, "chrome.7z")
if not os.path.isfile(chrome_7z_path):
    print(f"Error: chrome.7z not found at {chrome_7z_path}. The extraction may have failed.")
    input("\nPress Enter to exit...")
    sys.exit(1)


chrome_output_folder = os.path.join(update_temp_folder, "chrome")
os.makedirs(chrome_output_folder, exist_ok=True)

if not extract_archive(chrome_7z_path, chrome_output_folder):
    print("Failed to extract chrome.7z. Exiting.")
    input("\nPress Enter to exit...")
    sys.exit(1)


# backup
if os.path.exists(app_folder):
    shutil.copytree(app_folder, backup_folder)
    print(f"Backup completed successfully.")
else:
    print(f"No app folder found at {app_folder}.")

# copy with override
chrome_bin_folder = os.path.join(chrome_output_folder, "Chrome-bin")
if not os.path.exists(chrome_bin_folder):
    print(f"Error: Chrome-bin folder not found at {chrome_bin_folder}.")
    input("\nPress Enter to exit...")
    sys.exit(1)


if os.path.exists(app_folder):
    shutil.rmtree(app_folder)
shutil.copytree(chrome_bin_folder, app_folder)
print("Copy completed successfully.")


print("Removing temporary files...")
if os.path.exists(update_temp_folder):
    shutil.rmtree(update_temp_folder)
if os.path.exists(exe_archive):
    os.remove(exe_archive)
print("Cleanup completed.")
print("")


update_log()

print("")
input("\nPress Enter to exit...")

