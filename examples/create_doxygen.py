"""!
********************************************************************************
@file   create_doxygen.py
@brief  Example: create doxygen documentation for a project with doxygen_creator.
        Project name, version, description, author and repository URL are read from pyproject.toml.
        Copy this file into your project (e.g. Documentation/create_doxygen.py) and adapt it.
********************************************************************************
"""

import sys
import logging
import tomllib

from doxygen_creator import DoxygenCreator, get_cmd_args, PYTHON_PATTERN

PROJECT_DIR = "../"  # root of the project relative to the working directory
PYPROJECT_FILE = f"{PROJECT_DIR}pyproject.toml"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

if __name__ == "__main__":
    args = get_cmd_args()
    with open(PYPROJECT_FILE, mode="rb") as file:
        project = tomllib.load(file)["project"]

    doxygen_creator = DoxygenCreator(project["urls"]["Repository"], project_dir=PROJECT_DIR)
    doxygen_creator.set_configuration("PROJECT_NAME", project["name"])
    doxygen_creator.set_configuration("PROJECT_NUMBER", project["version"])
    doxygen_creator.set_configuration("PROJECT_BRIEF", project["description"])
    doxygen_creator.set_configuration("DOCSET_PUBLISHER_NAME", project["authors"][0]["name"])
    doxygen_creator.set_configuration("FILE_PATTERNS", [PYTHON_PATTERN, "*.md"])
    doxygen_creator.set_configuration("EXCLUDE_PATTERNS", [".venv", "CLAUDE.md"])

    sys.exit(doxygen_creator.run_doxygen(open_doxygen_output=args.open))
