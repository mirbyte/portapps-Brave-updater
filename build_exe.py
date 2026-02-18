import os
import sys
import shutil
import subprocess

# --- Config ---
APP_NAME = "portapps_Brave_updater"
SCRIPT   = "portapps_Brave_updater.py"
ICON     = "icon.ico"
USE_UPX  = False

HIDDEN_IMPORTS = [
    "requests",
    "bs4",
    "charset_normalizer",
    "idna",
    "certifi",
    "urllib3",
    "html.parser",
]

COLLECT_SUBMODULES = [
    "requests",
    # bs4 removed: --collect-submodules walks bs4.tests which requires pytest
]

EXCLUDES = [
    "tkinter",
    "matplotlib",
    "numpy",
    "pandas",
    "scipy",
    "PIL",
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6",
    "wx",
    "IPython",
    "jupyter",
    "lxml",
    "sqlite3",
    "unittest",
    "doctest",
    "pydoc",
    "xmlrpc",
    "ftplib",
    "imaplib",
    "poplib",
    "smtplib",
    "telnetlib",
    "nntplib",
    "bs4.tests",
    "pygame",
]


def check_requirements():
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or newer is required.")
        sys.exit(1)

    if not os.path.isfile(SCRIPT):
        print(f"ERROR: Source script '{SCRIPT}' not found in current directory.")
        sys.exit(1)

    if not os.path.isfile(ICON):
        print(f"ERROR: '{ICON}' not found in current directory.")
        sys.exit(1)

    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("ERROR: PyInstaller is not installed. Run: pip install pyinstaller")
        sys.exit(1)


def clean():
    for path in ["build", "dist", f"{APP_NAME}.spec"]:
        if os.path.exists(path):
            print(f"Removing: {path}")
            shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)


def build():
    env = os.environ.copy()
    env["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--clean",
        "--log-level", "WARN",
        f"--name={APP_NAME}",
        f"--icon={ICON}",
    ]

    if not USE_UPX:
        cmd.append("--noupx")

    for imp in HIDDEN_IMPORTS:
        cmd += ["--hidden-import", imp]

    for mod in COLLECT_SUBMODULES:
        cmd += ["--collect-submodules", mod]

    for exc in EXCLUDES:
        cmd += ["--exclude-module", exc]

    cmd.append(SCRIPT)

    print("Running PyInstaller...\n")
    result = subprocess.run(cmd, check=False, env=env)

    if result.returncode == 0:
        exe = os.path.join("dist", f"{APP_NAME}.exe")
        size_mb = os.path.getsize(exe) / (1024 * 1024)
        print(f"\nBuild successful -> {exe}  ({size_mb:.1f} MB)")
        print(
            "\nDEPLOYMENT REMINDER:"
            "\n  Place the exe in your Brave portable folder (name must contain 'brave')."
            "\n  The 7zip/ folder must be present next to the exe at runtime."
        )
    else:
        print(f"\nBuild failed (exit code {result.returncode})")
        sys.exit(result.returncode)


if __name__ == "__main__":
    check_requirements()
    clean()
    build()
