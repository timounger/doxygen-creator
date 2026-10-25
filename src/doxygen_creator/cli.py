"""!
********************************************************************************
@file   cli.py
@brief  Command line interface to create doxygen documentation without own script.
********************************************************************************
"""

import sys
import logging
import argparse

from .creator import DoxygenCreator, DoxygenCreatorError, DEFAULT_OUTPUT_FOLDER, PYTHON_PATTERN, add_open_argument

log = logging.getLogger(__name__)


def get_cmd_args(argv: list[str] | None = None) -> argparse.Namespace:
    """!
    @brief Define CMD arguments.
    @param argv : command line arguments (None: use sys.argv)
    @return argument parser.
    """
    parser = argparse.ArgumentParser(prog="doxygen-creator",
                                     description="Create doxygen documentation with uniform settings and styling.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    add_open_argument(parser)
    parser.add_argument("-p", "--project-dir", default=".", help="root folder of the project to document")
    parser.add_argument("-n", "--name", default="MyProject", help="PROJECT_NAME")
    parser.add_argument("-v", "--version", dest="number", help="PROJECT_NUMBER")
    parser.add_argument("-b", "--brief", help="PROJECT_BRIEF")
    parser.add_argument("--logo", help="PROJECT_LOGO")
    parser.add_argument("--icon", help="PROJECT_ICON")
    parser.add_argument("--author", help="DOCSET_PUBLISHER_NAME")
    parser.add_argument("-w", "--website", help="URL for GitHub corner")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_FOLDER, help="OUTPUT_DIRECTORY")
    parser.add_argument("--patterns", nargs="*", default=[PYTHON_PATTERN, "*.md"], help="FILE_PATTERNS")
    parser.add_argument("--exclude", nargs="*", default=[".venv"], help="EXCLUDE_PATTERNS")
    parser.add_argument("-s", "--set", action="append", default=[], metavar="KEY=VALUE",
                        help="any other doxygen setting (can be used multiple times)")
    parser.add_argument("--tools-dir", help="folder for downloaded doxygen and plantuml (default: user cache folder)")
    parser.add_argument("--doxygen", help="use this doxygen executable instead of the downloaded one")
    parser.add_argument("--no-plantuml", action="store_true", help="do not download plantuml.jar")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """!
    @brief Command line entry point.
    @param argv : command line arguments (None: use sys.argv)
    @return exit code: 0 no warnings; 1 warnings exist; 2 error
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = get_cmd_args(argv)

    doxygen_creator = DoxygenCreator(args.website, project_dir=args.project_dir, tools_dir=args.tools_dir,
                                     doxygen_exe=args.doxygen, plantuml=not args.no_plantuml)
    optional_settings = {
        "PROJECT_NUMBER": args.number,
        "PROJECT_BRIEF": args.brief,
        "PROJECT_LOGO": args.logo,
        "PROJECT_ICON": args.icon,
        "DOCSET_PUBLISHER_NAME": args.author,
    }
    doxygen_creator.set_configuration("PROJECT_NAME", args.name)
    doxygen_creator.set_configuration("OUTPUT_DIRECTORY", args.output)
    doxygen_creator.set_configuration("FILE_PATTERNS", args.patterns)
    doxygen_creator.set_configuration("EXCLUDE_PATTERNS", args.exclude)
    for key, value in optional_settings.items():
        if value is not None:
            doxygen_creator.set_configuration(key, value)
    for entry in args.set:
        key, separator, value = entry.partition("=")
        if not separator:
            log.error("Invalid setting '%s'. Use KEY=VALUE", entry)
            return 2
        doxygen_creator.set_configuration(key.strip(), value.strip())

    try:
        has_warnings = doxygen_creator.run_doxygen(open_doxygen_output=args.open)
    except DoxygenCreatorError as e:
        log.error(e)
        return 2
    return 1 if has_warnings else 0


if __name__ == "__main__":
    sys.exit(main())
