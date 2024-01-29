import typer
import virtualenv
import sys
import os
import subprocess
from pathlib import Path
import ast
import toml

app = typer.Typer()
venv_name = ".pypip"

def detect_pypip_folder(venv_name, file_path):
    directory_containing_file = file_path.parent
    pypip_folder = directory_containing_file / venv_name
    if pypip_folder.exists() and pypip_folder.is_dir():
        return True
    else:
        return False
    
def create_virtualenv(venv_name):
    subprocess.run([sys.executable, '-m', 'virtualenv', venv_name])

def find_requirements_txt(file_path):
    required_packages = set()  # Using a set to avoid duplicate entries
    current_dir = os.path.dirname(os.path.abspath(file_path))
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

def find_pyproject_toml(file_path):
    required_packages = set()  # Using a set to avoid duplicate entries
    current_dir = os.path.dirname(os.path.abspath(file_path))
    while current_dir != os.path.expanduser('~'):
        pyproject_toml_file = os.path.join(current_dir, 'pyproject.toml')
        if os.path.exists(pyproject_toml_file):
            try:
                with open(pyproject_toml_file, 'r') as f:
                    pyproject_toml_data = toml.load(f)
                # Extract dependencies from the 'tool.poetry.dependencies' section
                dependencies = pyproject_toml_data.get('tool', {}).get('poetry', {}).get('dependencies', {})
                for package, version in dependencies.items():
                    required_packages.add(f"{package}=={version}")
                return list(required_packages)  # Return the list of required packages
            except Exception as e:
                print(f"Error while parsing pyproject.toml: {e}")
                return []  # Return an empty list if there's an error parsing the file
        current_dir = os.path.dirname(current_dir)  # Move to the parent directory
    
    # If no pyproject.toml file is found, return an empty list
    return []

def find_imports(file_path):
    imports = []
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read(), filename=file_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])  # Take only the master package
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    imports.append(node.module.split('.')[0])  # Take only the master package
    return imports

def install_packages(venv_name, package_names):
    with open(os.devnull, 'w') as devnull:
        for package_name in package_names:
            command = [os.path.join(venv_name, 'bin', 'pip'), 'install', package_name]
            subprocess.run(command, stderr=devnull)

def run_script(venv_name, file, args):
    subprocess.run([os.path.join(venv_name, 'bin', 'python'), file] + args)

@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def main(file: Path, ctx: typer.Context):

    try:
        run_script(venv_name, file, ctx.args)
    except:
        if not detect_pypip_folder(venv_name, file):
            create_virtualenv(venv_name)
            package_names = find_requirements_txt(file)
            if len(package_names) == 0:
                package_names = find_pyproject_toml(file)
                if len(package_names) == 0:
                    package_names = find_imports(file)
            install_packages(venv_name, package_names)
        run_script(venv_name, file, ctx.args)
    