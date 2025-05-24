// filepath: d:\Workspace\my-textual-hanazawa\build.py
import os
import platform
import subprocess
import shutil
import zipfile
from pathlib import Path

def run_command(command):
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, check=True)
    return result

def create_zip(folder_path, output_zip):
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))

def main():
    # Determine system
    system = platform.system()
    print(f"Building for {system}")

    # Clean previous builds
    dist_dir = Path("dist")
    build_dir = Path("build")

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)

    # Run PyInstaller
    run_command("pyinstaller my-textual-hanazawa.spec")

    # Create release directory
    release_dir = Path("release")
    release_dir.mkdir(exist_ok=True)

    # Create zip of the build
    build_name = f"my-textual-hanazawa-{system.lower()}"
    zip_name = f"{build_name}.zip"
    zip_path = release_dir / zip_name

    # Create zip
    create_zip(dist_dir / "my-textual-hanazawa", zip_path)

    print(f"Build completed: {zip_path}")

if __name__ == "__main__":
    main()