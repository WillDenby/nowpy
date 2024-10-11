# TODO make sure that Python==XXX is removed from packages to install

"""A CLI tool for running Python scripts - hassle-free"""

# Standard library imports
import os
import sys
import ast
import random
import shutil
import subprocess
from typing import List
from pathlib import Path
from hashlib import sha256
from typing_extensions import Annotated, Optional

# Third party imports
import toml
import typer
from typeguard import typechecked

app = typer.Typer()


# Computes what the venv name for a given directory should be, based on its hash.
@typechecked
def find_venv() -> str:
    cwd_hash = sha256(str(Path.cwd()).encode()).hexdigest()
    venv_name = "venv_" + cwd_hash[:8]
    nowpy_folder_path = Path.home() / ".nowpy"
    venv_path = str(nowpy_folder_path / venv_name)
    return venv_path


@typechecked
def find_requirements_txt(file_in: Path) -> set:
    required_packages = set()
    current_dir = os.path.dirname(os.path.abspath(file_in))
    while current_dir != os.path.expanduser("~"):
        requirements_file = os.path.join(current_dir, "requirements.txt")
        if os.path.exists(requirements_file):
            with open(requirements_file, "r") as f:
                for line in f:
                    package = line.strip()
                    if package:
                        required_packages.add(package)
            break
        current_dir = os.path.dirname(current_dir)
    return required_packages


@typechecked
def find_poetry_pyproject_toml(file_in: Path) -> set:
    required_packages = set()
    current_dir = os.path.dirname(os.path.abspath(file_in))
    while current_dir != os.path.expanduser("~"):
        poetry_pyproject_toml_file = os.path.join(current_dir, "pyproject.toml")
        if os.path.exists(poetry_pyproject_toml_file):
            with open(poetry_pyproject_toml_file, "r") as f:
                poetry_pyproject_toml_data = toml.load(f)
            dependencies = (
                poetry_pyproject_toml_data.get("tool", {})
                .get("poetry", {})
                .get("dependencies", {})
            )
            for package, version in dependencies.items():
                version = version.lstrip("^")
                required_packages.add(f"{package}=={version}")
        current_dir = os.path.dirname(current_dir)
    return required_packages


# This finds packages required in either requirements.txt or pyproject.toml (Poetry-flavoured only currently).
@typechecked
def find_required_packages(file_in: Path) -> set:
    required_packages = set()
    requirements_packages = find_requirements_txt(
        file_in
    ) or find_poetry_pyproject_toml(file_in)
    unversioned_requirements_packages = set()
    for item in requirements_packages:
        package_name = item.split("==")[0]
        unversioned_requirements_packages.add(package_name)
    required_packages -= required_packages.intersection(
        unversioned_requirements_packages
    )
    required_packages.update(requirements_packages)
    return required_packages


# This returns packages already installed in the relevant venv, for set substraction by missing_imports function.
@typechecked
def find_existing_packages(venv_path: str) -> set[str]:
    result = subprocess.run(
        [os.path.join(venv_path, "bin", "pip"), "freeze"],
        capture_output=True,
        text=True,
    )
    existing_packages = set(result.stdout.strip().split("\n"))
    return existing_packages


# This finds all imports required from the file.
@typechecked
def find_imports(file_in: Path) -> set:
    imports = set()
    with open(file_in, "r") as file:
        tree = ast.parse(file.read(), filename=file_in)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    imports.add(node.module.split(".")[0])
    return imports


# Find any packages which are not already existing OR aren't already going to be requested.
# Version requirements can exist in requirements.txt/pyproject.toml, hence they take primacy.
@typechecked
def find_missing_imports(
    file_in: Path, required_packages: set, existing_packages: set[str]
) -> set:
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


@typechecked
def install_packages(venv_path: str, missing_packages: set) -> None:
    with open(os.devnull, "w") as devnull:
        if missing_packages:
            command = [os.path.join(venv_path, "bin", "pip"), "install"] + list(
                missing_packages
            )
            subprocess.run(command, stderr=devnull)


@typechecked
def run_script(venv_path: str, file_in: Path, args: List[str]) -> None:
    subprocess.run([os.path.join(venv_path, "bin", "python"), file_in] + args)


# This ensures that venvs don't build up over time!
def clean_nowpy_directory() -> None:
    cwd_hash = sha256(str(Path.cwd()).encode()).hexdigest()
    venv_name = "venv_" + cwd_hash[:8]
    nowpy_folder_path = Path.home() / ".nowpy"
    if not nowpy_folder_path.exists():
        return
    folders = [item for item in nowpy_folder_path.iterdir() if item.is_dir()]
    if len(folders) <= 5:
        return
    folders_to_delete = random.sample(folders, len(folders) - 5)
    for folder_to_delete in folders_to_delete:
        if folder_to_delete.name != venv_name:
            try:
                shutil.rmtree(folder_to_delete)
            except Exception:
                print("Can't clean up venvs in .nowpy folder")
                raise typer.Abort()


def reset_callback(value: bool) -> None:
    if value:
        print("Resetting venv...")
        venv_path = find_venv()
        packages = subprocess.run(
            [os.path.join(venv_path, "bin", "pip"), "freeze"],
            capture_output=True,
            text=True,
        ).stdout.split()
        if packages != []:
            subprocess.run(
                [os.path.join(venv_path, "bin", "pip"), "uninstall", "-y"] + packages,
                check=True,
            )
        raise typer.Exit()


def version_callback(value: bool) -> None:
    if value:
        print("nowpy 0.1.4")
        raise typer.Exit()


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def main(
    file: Path,
    ctx: typer.Context,
    reset: Annotated[
        Optional[bool], typer.Option("--reset", callback=reset_callback)
    ] = None,
    version: Annotated[
        Optional[bool],
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = None,
):
    venv_path = find_venv()
    if not os.path.exists(venv_path):
        print("Creating venv...")
        subprocess.run([sys.executable, "-m", "virtualenv", "-q", venv_path])
    clean_nowpy_directory()  # Stops nowpy venvs building up over time
    required_packages = find_required_packages(
        file
    )  # Finds packages required by requirements.txt or Poetry-flavoured pyproject.toml
    existing_packages = find_existing_packages(
        venv_path
    )  # Finds packages already in the venv
    missing_imports = find_missing_imports(
        file, required_packages, existing_packages
    )  # Identifies any packages required by import statements
    missing_packages = (
        required_packages - existing_packages
    )  # Identifies packages to install
    missing_packages.update(
        missing_imports
    )  # Adds any which are found via import statements
    missing_packages = {
        pkg for pkg in missing_packages if not pkg.startswith("python=")
    }
    install_packages(venv_path, missing_packages)  # Hassle-free!
    print("Running Script...")
    print("")
    run_script(venv_path, file, ctx.args)
