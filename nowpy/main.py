import typer
import sys
import os
import subprocess
from pathlib import Path
import ast
import toml
from hashlib import sha256
from typing_extensions import Annotated, Optional
import random
import shutil

app = typer.Typer()

def find_venv():
    cwd_hash = sha256(str(Path.cwd()).encode()).hexdigest()
    venv_name = "venv_" + cwd_hash[:8]
    nowpy_folder_path = Path.home() / ".nowpy"
    venv_path = str(nowpy_folder_path / venv_name)
    return venv_path

def find_requirements_txt(file_in):
    required_packages = set()  # Using a set to avoid duplicate entries
    current_dir = os.path.dirname(os.path.abspath(file_in))
    while current_dir != os.path.expanduser('~'):
        requirements_file = os.path.join(current_dir, 'requirements.txt')
        if os.path.exists(requirements_file):
            with open(requirements_file, 'r') as f:
                for line in f:
                    package = line.strip()
                    if package:  # Check if the line is not empty
                        required_packages.add(package)
            break  # Stop searching once requirements.txt is found
        current_dir = os.path.dirname(current_dir)  # Move to the parent directory
    return required_packages

def find_pyproject_toml(file_in):
    required_packages = set()  # Using a set to avoid duplicate entries
    current_dir = os.path.dirname(os.path.abspath(file_in))
    while current_dir != os.path.expanduser('~'):
        pyproject_toml_file = os.path.join(current_dir, 'pyproject.toml')
        if os.path.exists(pyproject_toml_file):
            with open(pyproject_toml_file, 'r') as f:
                pyproject_toml_data = toml.load(f)
                # Extract dependencies from the 'tool.poetry.dependencies' section
            dependencies = pyproject_toml_data.get('tool', {}).get('poetry', {}).get('dependencies', {})
            for package, version in dependencies.items():
                version = version.lstrip('^')
                required_packages.add(f"{package}=={version}")
        current_dir = os.path.dirname(current_dir)  # Move to the parent directory
    
    return required_packages  # Return the list of required packages

def find_required_packages(file_in):
    required_packages = set()
    requirements_packages = find_requirements_txt(file_in) or find_pyproject_toml(file_in)
    unversioned_requirements_packages = set()
    for item in requirements_packages:
        package_name = item.split("==")[0]
        unversioned_requirements_packages.add(package_name)
    required_packages -= required_packages.intersection(unversioned_requirements_packages)
    required_packages.update(requirements_packages)
    return required_packages

def find_existing_packages(venv_path):
    result = subprocess.run([os.path.join(venv_path, 'bin', 'pip'), 'freeze'], capture_output=True, text=True)
    existing_packages = set(result.stdout.strip().split('\n'))
    return existing_packages

def find_imports(file_in):
    imports = set()
    with open(file_in, 'r') as file:
        tree = ast.parse(file.read(), filename=file_in)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])  # Take only the master package
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    imports.add(node.module.split('.')[0])  # Take only the master package                  
    return imports

def find_missing_imports(file_in, required_packages, existing_packages):
    missing_imports = set()
    imports = find_imports(file_in)

    unversioned_required_packages = set()
    for item in required_packages:
        package_name = item.split("==")[0]
        unversioned_required_packages.add(package_name)

    unversioned_existing_packages = set()
    for item in existing_packages:
        package_name = item.split("==")[0]
        unversioned_existing_packages.add(package_name)

    for item in imports:
        if item not in unversioned_required_packages:
            if item not in unversioned_existing_packages:
                missing_imports.add(item)
    return missing_imports

def install_packages(venv_path, missing_packages):
    with open(os.devnull, 'w') as devnull:
        for pkg in missing_packages:
            command = [os.path.join(venv_path, 'bin', 'pip'), 'install', pkg]
            subprocess.run(command, stderr=devnull)

def run_script(venv_path, file_in, args):
    subprocess.run([os.path.join(venv_path, 'bin', 'python'), file_in] + args)

def clean_nowpy_directory():
    cwd_hash = sha256(str(Path.cwd()).encode()).hexdigest()
    venv_name = "venv_" + cwd_hash[:8]

    nowpy_folder_path = Path.home() / ".nowpy"
    if not nowpy_folder_path.exists():
        return

    folders = [item for item in nowpy_folder_path.iterdir() if item.is_dir()]
    if len(folders) <= 10:
        return

    folders_to_delete = random.sample(folders, len(folders) - 10)
    for folder_to_delete in folders_to_delete:
        if not folder_to_delete.name == venv_name:
            try:
                shutil.rmtree(folder_to_delete)
            except Exception as e:
                pass

def reset_callback(value: bool):
    if value:
        print(f"Resetting the nowpy Virtual Environment...")
        venv_path = find_venv()
        packages =  subprocess.run([os.path.join(venv_path, 'bin', 'pip'), "freeze"], capture_output=True, text=True).stdout.split()
        if not packages == []:
            subprocess.run([os.path.join(venv_path, 'bin', 'pip'), "uninstall", "-y"] + packages, check=True)
        raise typer.Exit()

def version_callback(value: bool):
    if value:
        print("nowpy 0.1.0")
        raise typer.Exit()
@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def main(file: Path, 
         ctx: typer.Context,
         reset: Annotated[Optional[bool], typer.Option("--reset", callback=reset_callback)] = None,
         version: Annotated[Optional[bool], typer.Option("--version", callback=version_callback, is_eager=True)] = None):

    venv_path = find_venv()
    if not os.path.exists(venv_path):
        print("Creating Virtualenv...")
        subprocess.run([sys.executable, '-m', 'virtualenv', '-q', venv_path])
    
    clean_nowpy_directory()

    required_packages = find_required_packages(file)
    existing_packages = find_existing_packages(venv_path)
    missing_imports = find_missing_imports(file, required_packages, existing_packages)
    missing_packages = required_packages - existing_packages
    missing_packages.update(missing_imports)

    install_packages(venv_path, missing_packages)
    print("Running Script...")
    print("")
    run_script(venv_path, file, ctx.args)
    