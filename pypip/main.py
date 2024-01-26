import typer
import virtualenv
import sys
import os
import subprocess
from pathlib import Path
import ast

app = typer.Typer()

def create_virtualenv(venv_name):
    subprocess.run([sys.executable, '-m', 'virtualenv', venv_name])

def find_imports(file_path):
    imports = []
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read(), filename=file_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)
    return imports

def install_packages(venv_name, package_names):
    for package_name in package_names:
        subprocess.run([os.path.join(venv_name, 'bin', 'pip'), 'install', package_name])

def run_script(venv_name, file):
    subprocess.run([os.path.join(venv_name, 'bin', 'python'), file])

def detect_pypip_folder(venv_name, file):
    directory_containing_file = file.parent
    pypip_folder = directory_containing_file / 'pypip'
    if pypip_folder.exists() and pypip_folder.is_dir():
        return True
    else:
        return False
    
@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def main(file: Path, ctx: typer.Context):
    venv_name = "pypip"
    if not detect_pypip_folder(venv_name, file):
        create_virtualenv(venv_name)

    package_names = find_imports(file)
    install_packages(venv_name, package_names)

    print("File is: ", file)
    print("Args are: ", ctx.args)
    run_script(venv_name, file)
