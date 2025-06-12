import subprocess
import sys

# Define the dependencies for the server and client
dependencies = {
    "server": [
        "Flask",
        "Flask-SQLAlchemy",
        "Flask-JWT-Extended",
        "Flask-Cors",
        "psycopg2-binary",
        "python-dotenv"
    ],
    "client": [
        "requests",
        "PyQt5",
        "cryptography"
    ]
}

def install_or_update(package):
    """Install or update a package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])
        print(f"✔ {package} is installed and up-to-date.")
    except subprocess.CalledProcessError:
        print(f"✘ Failed to install or update {package}. Please check your environment.")

def check_dependencies():
    """Check and install/update dependencies for both server and client."""
    print("Checking dependencies for the server...")
    for package in dependencies["server"]:
        install_or_update(package)

    print("\nChecking dependencies for the client...")
    for package in dependencies["client"]:
        install_or_update(package)

if __name__ == "__main__":
    check_dependencies()