import typer
import sys
import os
import subprocess
from pathlib import Path
import ast
import toml
from hashlib import sha256
from typing_extensions import Annotated, Optional

app = typer.Typer()

def find_venv():
    cwd_hash = sha256(str(Path.cwd()).encode()).hexdigest()
    venv_name = "venv_" + cwd_hash[:8]
    pypip_folder_path = Path.home() / ".pypip"
    venv_path = str(pypip_folder_path / venv_name)
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
    return list(required_packages)

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
                required_packages.add(f"{package}=={version}")
        current_dir = os.path.dirname(current_dir)  # Move to the parent directory
    
    return list(required_packages)  # Return the list of required packages

def find_imports(file_in):
    imports = []
    with open(file_in, 'r') as file:
        tree = ast.parse(file.read(), filename=file_in)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])  # Take only the master package
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    imports.append(node.module.split('.')[0])  # Take only the master package
    return imports

def find_packages(file_in):
    package_names = []
    package_names.extend(find_requirements_txt(file_in))
    package_names.extend(find_pyproject_toml(file_in))
    package_names.extend(find_imports(file_in))
    return package_names

def check_packages(venv_path, package_names):
    result = subprocess.run([os.path.join(venv_path, 'bin', 'pip'), 'freeze'], capture_output=True, text=True)
    installed_packages = [line.split()[0] for line in result.stdout.splitlines()[2:]]
    missing_packages = [pkg for pkg in package_names if pkg not in installed_packages]
    return missing_packages

def install_packages(venv_path, missing_packages):
    with open(os.devnull, 'w') as devnull:
        for pkg in missing_packages:
            command = [os.path.join(venv_path, 'bin', 'pip'), 'install', pkg]
            subprocess.run(command, stderr=devnull)

def run_script(venv_path, file_in, args):
    subprocess.run([os.path.join(venv_path, 'bin', 'python'), file_in] + args)

def reset_callback(value: bool):
    if value:
        print(f"Resetting the PyPip Virtual Environment...")
        venv_path = find_venv()
        packages =  subprocess.run([os.path.join(venv_path, 'bin', 'pip'), "freeze"], capture_output=True, text=True).stdout.split()
        if not packages == []:
            subprocess.run([os.path.join(venv_path, 'bin', 'pip'), "uninstall", "-y"] + packages, check=True)
        raise typer.Exit()
    
@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def main(file: Path, 
         ctx: typer.Context,
         reset: Annotated[Optional[bool], typer.Option("--reset", callback=reset_callback)] = None,):
    # Find the venv hash
    venv_path = find_venv()

    if not os.path.exists(venv_path):
        subprocess.run([sys.executable, '-m', 'virtualenv', venv_path])
        
    package_names = find_packages(file)
    missing_packages = check_packages(venv_path, package_names)

    install_packages(venv_path, missing_packages)
    run_script(venv_path, file, ctx.args)
    