"""!
********************************************************************************
@file   creator.py
@brief  Create doxygen documentation.
********************************************************************************
"""

import os
import sys
import copy
import shutil
import logging
import subprocess
import webbrowser
import time
import argparse
import zipfile
from pathlib import Path
from typing import Any
from threading import Thread
from difflib import get_close_matches, HtmlDiff
import requests
import packaging.version

from .config_parser import ConfigParser
from .doxy_py_checker import DoxyPyChecker

log = logging.getLogger(__name__)

YES = "YES"
NO = "NO"
WARNING_FAIL = "FAIL_ON_WARNINGS"

ASSETS_DIR = Path(__file__).parent / "assets"
TOOLS_DIR_ENV = "DOXYGEN_CREATOR_HOME"  # environment variable to override the folder for downloaded tools
DEFAULT_OUTPUT_FOLDER = "Output_Doxygen"

DOXYGEN_VERSION = "1.16.1"
DOXYGEN_URL = f"https://sourceforge.net/projects/doxygen/files/rel-{DOXYGEN_VERSION}/doxygen-{DOXYGEN_VERSION}.windows.x64.bin.zip/download"
DOXYGEN_ZIP = f"doxygen-{DOXYGEN_VERSION}.windows.x64.bin.zip"
DOXYGEN_PATH = "doxygen.exe"  # archive member / local file name of the doxygen binary
DOXYGEN_DLL = "libclang.dll"

PLANT_UML_VERSION = "1.2026.5"
PLANTUML_JAR_URL = f"https://github.com/plantuml/plantuml/releases/download/v{PLANT_UML_VERSION}/plantuml-{PLANT_UML_VERSION}.jar"
PLANTUML_JAR_NAME = "plantuml.jar"

WARNING_FILE_PREFIX = "Doxygen_warnings_"
WARNING_FILE_SUFFIX = ".log"
INDEX_FILE = "html/index.html"
TIMEOUT = 60  # timeout for tool download
CHUNK_SIZE = 1024 * 1024

PYTHON_PATTERN = "*.py"

DOXY_DIFF_HTML_NAME = "DoxyfileDiff.html"
DOXY_FILE_DEFAULT_NAME = "Default.Doxyfile"
WRAP_LENGTH = 100

AWESOME_EXTRA_FILES = ["doxygen-awesome-darkmode-toggle.js",
                       "doxygen-awesome-fragment-copy-button.js",
                       "doxygen-awesome-paragraph-link.js",
                       "doxygen-awesome-interactive-toc.js",
                       "doxygen-awesome-tabs.js"]
AWESOME_STYLESHEETS = ["doxygen-awesome.css",
                       "doxygen-awesome-sidebar-only.css",
                       "doxygen-awesome-sidebar-only-darkmode-toggle.css"]
HEADER_FILE = "header.html"

GITHUB_CORNER_FIRST = "<a href="
GITHUB_CORNER_LAST = """ class="github-corner" aria-label="View source on GitHub"><svg width="80" height="80" viewBox="0 0 250 250" style="fill:#151513; color:#fff; position: absolute; top: 0; border: 0; right: 0;" aria-hidden="true"><path d="M0,0 L115,115 L130,115 L142,142 L250,250 L250,0 Z"></path><path d="M128.3,109.0 C113.8,99.7 119.0,89.6 119.0,89.6 C122.0,82.7 120.5,78.6 120.5,78.6 C119.2,72.0 123.4,76.3 123.4,76.3 C127.3,80.9 125.5,87.3 125.5,87.3 C122.9,97.6 130.6,101.9 134.4,103.2" fill="currentColor" style="transform-origin: 130px 106px;" class="octo-arm"></path><path d="M115.0,115.0 C114.9,115.1 118.7,116.5 119.8,115.4 L133.7,101.6 C136.9,99.2 139.9,98.4 142.2,98.6 C133.8,88.0 127.5,74.4 143.8,58.0 C148.5,53.4 154.0,51.2 159.7,51.0 C160.3,49.4 163.2,43.6 171.4,40.1 C171.4,40.1 176.1,42.5 178.8,56.2 C183.1,58.6 187.2,61.8 190.9,65.4 C194.5,69.0 197.7,73.2 200.1,77.6 C213.8,80.2 216.3,84.9 216.3,84.9 C212.7,93.1 206.9,96.0 205.4,96.6 C205.1,102.4 203.0,107.8 198.3,112.5 C181.9,128.9 168.3,122.5 157.7,114.1 C157.9,116.9 156.7,120.9 152.7,124.9 L141.0,136.5 C139.8,137.7 141.6,141.9 141.8,141.8 Z" fill="currentColor" class="octo-body"></path></svg></a><style>.github-corner:hover .octo-arm{animation:octocat-wave 560ms ease-in-out}@keyframes octocat-wave{0%,100%{transform:rotate(0)}20%,60%{transform:rotate(-25deg)}40%,80%{transform:rotate(10deg)}}@media (max-width:500px){.github-corner:hover .octo-arm{animation:none}.github-corner .octo-arm{animation:octocat-wave 560ms ease-in-out}}</style>"""

DEFAULT_SETTINGS: dict[str, str | list[str] | int] = {
    "PROJECT_NAME": "MyProject",  # important to define default user name to create output folder and files
    "OUTPUT_DIRECTORY": DEFAULT_OUTPUT_FOLDER,
    "ABBREVIATE_BRIEF": "",  # Each string in this list, will be stripped from the text ("" to prevent warning)
    "FULL_PATH_NAMES": NO,
    "JAVADOC_AUTOBRIEF": YES,  # first line (until the first dot) of a Javadoc-style comment as the brief description
    "OPTIMIZE_OUTPUT_JAVA": YES,
    "TIMESTAMP": YES,
    "EXTRACT_ALL": YES,
    "INTERNAL_DOCS": YES,  # documentation after internal command is included
    "HIDE_SCOPE_NAMES": YES,  # full class and namespace scopes in the documentation
    "SORT_BRIEF_DOCS": YES,  # sort the brief descriptions of file namespace and class members alphabetically by member name
    "SORT_BY_SCOPE_NAME": YES,
    "WARN_NO_PARAMDOC": YES,
    "WARN_AS_ERROR": WARNING_FAIL,
    "FILE_PATTERNS": [],
    "RECURSIVE": YES,
    "SOURCE_BROWSER": YES,
    "INLINE_SOURCES": YES,
    "HTML_COLORSTYLE": "LIGHT",  # required with Doxygen >= 1.9.5
    "HTML_COLORSTYLE_HUE": 209,  # required for Doxygen Awesome
    "HTML_COLORSTYLE_SAT": 255,  # required for Doxygen Awesome
    "HTML_COLORSTYLE_GAMMA": 113,  # required for Doxygen Awesome
    "HTML_DYNAMIC_SECTIONS": YES,
    "HTML_COPY_CLIPBOARD": NO,  # required for Doxygen Awesome
    "DISABLE_INDEX": NO,  # required for Doxygen Awesome
    "GENERATE_TREEVIEW": YES,  # required for Doxygen Awesome
    "FULL_SIDEBAR": NO,  # required for Doxygen Awesome
    "SEARCHENGINE": YES,
    "SERVER_BASED_SEARCH": NO,
    "EXTERNAL_SEARCH": NO,
    "GENERATE_LATEX": NO,
    "LATEX_CMD_NAME": "latex",
    "UML_LOOK": YES,
    "DOT_IMAGE_FORMAT": "svg",
    "INTERACTIVE_SVG": YES,
    "DOT_MULTI_TARGETS": YES,
    "DOT_CLEANUP": YES,
}


class DoxygenCreatorError(Exception):
    """!
    @brief Exception thrown when the doxygen documentation can not be created.
    """


def get_default_tools_dir() -> Path:
    """!
    @brief Get folder to store downloaded tools (doxygen, plantuml).
    @return tools folder
    """
    env_dir = os.environ.get(TOOLS_DIR_ENV)
    if env_dir:
        return Path(env_dir)
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "doxygen_creator"
    return Path.home() / ".cache" / "doxygen_creator"


def download_file(url: str, file_path: Path) -> None:
    """!
    @brief Download file. Use temporary file to prevent incomplete downloads.
    @param url : URL to download
    @param file_path : file to store download
    """
    tmp_path = file_path.with_name(file_path.name + ".part")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, timeout=TIMEOUT, stream=True) as response:
        response.raise_for_status()
        with open(tmp_path, mode="wb") as file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                file.write(chunk)
    os.replace(tmp_path, file_path)


def as_doxy_path(path: Path) -> str:
    """!
    @brief Convert path to doxyfile format. Forward slashes prevent that a trailing backslash is read as line continuation.
    @param path : path to convert
    @return path string for doxyfile
    """
    return path.as_posix()


class OpenNotepad(Thread):
    """!
    @brief Class to open Notepad in thread to prevent program stop until close file.
    @param file : file to open
    """

    def __init__(self, file: str):
        Thread.__init__(self)
        self.file = file
        self.start()

    def run(self) -> None:
        """!
        @brief Open file with notepad.
        """
        time.sleep(1)
        with subprocess.Popen(["notepad.exe", self.file]):
            pass


class DoxygenCreator:
    """!
    @brief Class to generate Doxygen documentation for any code documentation with uniform settings and styling.
    @param website : URL to website (shown as GitHub corner)
    @param project_dir : root folder of the project to document (used as default for INPUT, IMAGE_PATH and README.md)
    @param tools_dir : folder for downloaded doxygen and plantuml (None: user cache folder)
    @param doxygen_exe : use this doxygen executable instead of the downloaded one
    @param plantuml : [True] download plantuml.jar and enable PlantUML diagrams
    @param config_diff : [True] create html diff between default and used doxyfile
    @param py_checker : [True] check python files for valid doxygen parameter and return documentation
    @param auto_version : [True] prefix valid version numbers in PROJECT_NUMBER with "v"
    """

    def __init__(self, website: str | None = None, project_dir: str = ".", tools_dir: str | None = None,
                 doxygen_exe: str | None = None, plantuml: bool = True, config_diff: bool = True,
                 py_checker: bool = True, auto_version: bool = True) -> None:
        self.website = website
        self.project_dir = project_dir
        self.tools_dir = Path(tools_dir) if tools_dir else get_default_tools_dir()
        self.doxygen_exe = doxygen_exe
        self.plantuml = plantuml
        self.config_diff = config_diff
        self.py_checker = py_checker
        self.auto_version = auto_version
        self.settings: dict[str, str | list[str] | int] = copy.deepcopy(DEFAULT_SETTINGS)
        self.warnings: list[str] = []
        self.output_dir = ""
        self.doxyfile_name = ""
        self.warning_name = ""

    @property
    def doxygen_dir(self) -> Path:
        """!
        @brief Folder of the downloaded doxygen version.
        @return doxygen folder
        """
        return self.tools_dir / f"doxygen-{DOXYGEN_VERSION}"

    @property
    def plantuml_jar(self) -> Path:
        """!
        @brief Path of the downloaded plantuml.jar.
        @return plantuml.jar path
        """
        return self.tools_dir / f"plantuml-{PLANT_UML_VERSION}" / PLANTUML_JAR_NAME

    def create_default_doxyfile(self, file_name: str) -> None:
        """!
        @brief Create default doxyfile.
        @param file_name : doxygen file name
        """
        subprocess.call([self.get_doxygen_exe(), "-g", file_name])

    def set_configuration(self, key: str, value: Any, override: bool = True) -> None:
        """!
        @brief Set doxygen configuration.
        @param key : type to set in configuration
        @param value : value to set for key in configuration
        @param override : [True] replace existing value; [False] keep existing value (lists will be extended)
        """
        if isinstance(value, list):
            if override or (key not in self.settings):
                self.settings[key] = []
            list_to_extend = self.settings[key]  # Now mypy knows this is a list
            if isinstance(list_to_extend, list):
                list_to_extend.extend(value)
            else:
                log.warning("Not possible to append value to %s", key)
        else:
            if override or (key not in self.settings):
                self.settings[key] = value

    def get_configuration(self, key: str) -> Any:
        """!
        @brief Get type in doxygen configuration.
        @param key : type in configuration get setting
        @return configuration settings
        """
        if key in self.settings:
            value = self.settings[key]
        else:
            value = None  # is default value
        return value

    def prepare_doxyfile_configuration(self) -> None:
        """!
        @brief Prepare doxyfile configuration with default settings that depend on other parameters.
               Parameters that set before as fix parameter or by user will not override.
               This allows the user to make settings that differ from the default configuration.
        """
        # set filenames and directories needed to save/open files
        self.output_dir = self.get_configuration('OUTPUT_DIRECTORY')  # save output directory which used for other file names
        project_name = self.get_configuration("PROJECT_NAME")
        self.doxyfile_name = os.path.join(self.output_dir, f"{project_name}.Doxyfile")
        self.warning_name = os.path.join(self.output_dir, f"{WARNING_FILE_PREFIX}{project_name}{WARNING_FILE_SUFFIX}")

        # set uniform doxygen configuration that depend on other parameters
        self.set_configuration("PROJECT_BRIEF", f"{project_name}-Documentation", override=False)  # use project name as default if nothing defined
        self.set_configuration("WARN_LOGFILE", self.warning_name, override=False)
        self.set_configuration("EXCLUDE_PATTERNS", [self.output_dir], override=False)
        if self.get_configuration("INPUT") is None:
            self.set_configuration("INPUT", [self.project_dir])
        self.set_configuration("IMAGE_PATH", self.project_dir, override=False)
        readme = os.path.join(self.project_dir, "README.md")
        if os.path.exists(readme):
            self.set_configuration("USE_MDFILE_AS_MAINPAGE", readme, override=False)

        if self.auto_version:
            # write version prefix for version numbers as project number
            version = self.get_configuration("PROJECT_NUMBER")
            if version:
                try:
                    packaging.version.Version(version)  # test if version is a valid versions string
                    self.set_configuration("PROJECT_NUMBER", f"v{version}")
                except packaging.version.InvalidVersion:
                    pass  # not a valid version, do not prefix with "v"

        # set doxygen awesome settings which depends on path
        extra_files = [as_doxy_path(ASSETS_DIR / name) for name in AWESOME_EXTRA_FILES]
        self.set_configuration("HTML_EXTRA_FILES", extra_files, override=False)
        extra_stylesheets = [as_doxy_path(ASSETS_DIR / name) for name in AWESOME_STYLESHEETS]
        self.set_configuration("HTML_EXTRA_STYLESHEET", extra_stylesheets, override=False)  # doxygen styling code
        self.set_configuration("HTML_HEADER", as_doxy_path(ASSETS_DIR / HEADER_FILE), override=False)  # use own doxygen header

        if self.plantuml:
            self.set_configuration("PLANTUML_JAR_PATH", as_doxy_path(self.plantuml_jar), override=False)

    def edit_select_doxyfile_settings(self) -> None:
        """!
        @brief Override default settings in doxyfile with selected settings.
        """
        # load the default doxygen template file
        config_parser = ConfigParser()
        configuration = config_parser.load_configuration(self.doxyfile_name)
        existing_keys = list(configuration.keys())

        # write doxygen settings
        for key, value in self.settings.items():
            if key in existing_keys:
                if isinstance(value, list):
                    configuration[key] = list(value)
                else:
                    if isinstance(value, int):
                        value = str(value)  # integer can only write as string to doxyfile
                    configuration[key] = value
            else:
                text = f"'{key}' is an invalid doxygen setting"
                similar_key = get_close_matches(key, existing_keys, n=1)
                if similar_key:
                    text += f". Did you mean: '{similar_key[0]}'?"
                self.warnings.append(text)

        # store the configuration in doxyfile
        config_parser.store_configuration(configuration, self.doxyfile_name)

    def add_warnings(self) -> None:
        """!
        @brief Add warnings to warning file.
        """
        if self.warnings:
            with open(self.warning_name, mode="a", encoding="utf-8") as file:
                for warning in self.warnings:
                    file.write(warning + "\n")

    def download_plantuml_jar(self) -> None:
        """!
        @brief Download PlantUML Jar.
        """
        if not self.plantuml_jar.exists():
            log.info("Download %s ...", self.plantuml_jar)
            try:
                download_file(PLANTUML_JAR_URL, self.plantuml_jar)
            except requests.Timeout:
                log.error("Timeout for download %s!", PLANTUML_JAR_NAME)
            except requests.RequestException as e:
                log.error("Can not download %s! %s", PLANTUML_JAR_NAME, e)
        else:
            log.info("%s already exist!", self.plantuml_jar)

    def get_doxygen_exe(self) -> str:
        """!
        @brief Get doxygen executable that is used for generation.
        @return path to doxygen executable
        """
        if self.doxygen_exe:
            return self.doxygen_exe
        if sys.platform == "win32":
            return str(self.doxygen_dir / DOXYGEN_PATH)
        doxygen = shutil.which("doxygen")
        if doxygen is None:
            raise DoxygenCreatorError("Doxygen not found! Install doxygen or set doxygen_exe.")
        return doxygen

    def download_doxygen(self) -> None:
        """!
        @brief Download the pinned Doxygen to the tools folder if not already present.
               PATH is intentionally ignored on Windows: the downloaded copy is always used,
               so a different doxygen.exe on PATH can never be picked up by mistake.
        """
        if self.doxygen_exe or sys.platform != "win32":
            return  # own executable or no windows binary available
        doxygen_path = self.doxygen_dir / DOXYGEN_PATH
        dll_path = self.doxygen_dir / DOXYGEN_DLL
        if not doxygen_path.exists() or not dll_path.exists():
            zip_path = self.tools_dir / DOXYGEN_ZIP
            if not zip_path.exists():
                log.info("Download %s ...", DOXYGEN_ZIP)
                try:
                    download_file(DOXYGEN_URL, zip_path)
                except requests.Timeout as e:
                    raise DoxygenCreatorError(f"Timeout for download {DOXYGEN_ZIP}!") from e
                except requests.RequestException as e:
                    raise DoxygenCreatorError(f"Can not download {DOXYGEN_ZIP}! {e}") from e
            else:
                log.info("%s already exist!", zip_path)
            with zipfile.ZipFile(zip_path, mode="r") as zip_ref:
                zip_ref.extract(DOXYGEN_PATH, self.doxygen_dir)
                zip_ref.extract(DOXYGEN_DLL, self.doxygen_dir)
            zip_path.unlink()
        else:
            log.info("%s already exist!", doxygen_path)

    def check_doxygen_warnings(self, open_warning_file: bool = True) -> bool:
        """!
        @brief Check for doxygen Warnings.
        @param open_warning_file : [True] open warning file; [False] only check for warnings
        @return status if doxygen warnings exist
        """
        has_warnings = False

        if os.path.exists(self.warning_name):
            with open(self.warning_name, mode="r", encoding="utf-8") as file:
                lines = file.readlines()
                if lines:
                    has_warnings = True
                    log.warning("Doxygen Warnings found!!!")
                    for line in lines:
                        log.warning("  %s", line.rstrip())

        if open_warning_file and has_warnings and sys.platform == "win32":
            OpenNotepad(self.warning_name)

        return has_warnings

    def generate_doxygen_output(self, open_doxygen_output: bool = True) -> None:
        """!
        @brief Generate Doxygen output depend on existing doxyfile.
        @param open_doxygen_output : [True] open output in browser; [False] only generate output
        """
        subprocess.call([self.get_doxygen_exe(), self.doxyfile_name])

        if open_doxygen_output:
            # open doxygen output
            index_file = Path(self.output_dir, INDEX_FILE).resolve()
            webbrowser.open_new_tab(index_file.as_uri())

    def add_github_corner(self) -> None:
        """!
        @brief Add Github corner to all html files.
        """
        if self.website is None:
            return
        folder = os.path.join(self.output_dir, "html")
        corner_text = GITHUB_CORNER_FIRST + self.website + GITHUB_CORNER_LAST
        for html_file in os.listdir(folder):
            if html_file.endswith(".html"):
                with open(os.path.join(folder, html_file), mode="a", encoding="utf-8") as file:
                    file.write(corner_text + "\n")

    def add_nojekyll_file(self) -> None:
        """!
        @brief Add .nojekyll file so that files with underscores are visible.
        """
        file_name = ".nojekyll"
        with open(os.path.join(self.output_dir, "html", file_name), mode="w", encoding="utf-8") as file:
            file.write("")

    def generate_configuration_diff(self) -> None:
        """!
        @brief Generate doxyfile diff to view changes.
        """
        default_doxyfile = os.path.join(self.output_dir, DOXY_FILE_DEFAULT_NAME)

        # create and read default doxyfile
        self.create_default_doxyfile(default_doxyfile)
        config_parser = ConfigParser()
        configuration = config_parser.load_configuration(default_doxyfile)
        config_parser.store_configuration(configuration, default_doxyfile)
        with open(default_doxyfile, mode="r", encoding="utf-8") as file:
            default_config = file.read()
        os.remove(default_doxyfile)

        # read modified doxyfile
        with open(self.doxyfile_name, mode="r", encoding="utf-8") as file:
            modified_config = file.read()

        diff_file_name = os.path.join(self.output_dir, DOXY_DIFF_HTML_NAME)
        difference = HtmlDiff(wrapcolumn=WRAP_LENGTH).make_file(default_config.splitlines(), modified_config.splitlines(), "Default", "Modified")
        with open(diff_file_name, mode="w", encoding="utf-8") as file:
            file.write(difference)

    def run_doxy_py_checker(self) -> None:
        """!
        @brief Check for valid doxygen specification in python files if python files are documented.
        """
        file_patterns = self.settings["FILE_PATTERNS"]
        if isinstance(file_patterns, list):
            pattern_list = [str(pattern) for pattern in file_patterns]
        else:
            pattern_list = [str(file_patterns)]
        if PYTHON_PATTERN in pattern_list:
            exclude_patterns = self.settings.get("EXCLUDE_PATTERNS", [])
            exclude_folders = [str(pattern) for pattern in exclude_patterns] if isinstance(exclude_patterns, list) else [str(exclude_patterns)]
            doxy_checker = DoxyPyChecker(self.project_dir, exclude_folders=exclude_folders)
            findings = doxy_checker.run_check()
            self.warnings.extend(findings)

    def run_doxygen(self, open_doxygen_output: bool = True) -> bool:
        """!
        @brief Generate Doxyfile and Doxygen output depend on doxyfile settings.
        @param open_doxygen_output : [True] open output in browser; [False] only generate output
        @return status for found doxygen warning
        """
        self.download_doxygen()
        if self.plantuml:
            self.download_plantuml_jar()
        self.prepare_doxyfile_configuration()
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.create_default_doxyfile(self.doxyfile_name)
        self.edit_select_doxyfile_settings()
        self.generate_doxygen_output(open_doxygen_output)
        self.add_github_corner()
        self.add_nojekyll_file()
        if self.config_diff:
            self.generate_configuration_diff()
        if self.py_checker:
            self.run_doxy_py_checker()

        self.add_warnings()  # add own warnings to warning file
        has_warnings = self.check_doxygen_warnings(open_doxygen_output)

        return has_warnings


def str_to_bool(value: str) -> bool:
    """!
    @brief Convert command line string to bool.
    @param value : string value like True/False, yes/no, 1/0
    @return converted bool value
    """
    if value.lower() in ("true", "yes", "1", "on"):
        return True
    if value.lower() in ("false", "no", "0", "off"):
        return False
    raise argparse.ArgumentTypeError(f"Boolean value expected, got '{value}'")


def add_open_argument(parser: argparse.ArgumentParser) -> None:
    """!
    @brief Add argument to open output. Supports "-o" and "-o True/False".
    @param parser : argument parser to extend
    """
    parser.add_argument("-o", "--open",
                        type=str_to_bool,
                        nargs="?",
                        const=True,
                        default=False,
                        help="open output files after generation")


def get_cmd_args(argv: list[str] | None = None) -> argparse.Namespace:
    """!
    @brief Function to define CMD arguments.
    @param argv : command line arguments (None: use sys.argv)
    @return Function returns argument parser.
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    add_open_argument(parser)
    return parser.parse_args(argv)
