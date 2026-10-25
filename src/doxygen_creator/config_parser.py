"""!
********************************************************************************
@file   config_parser.py
@brief  Load and store settings from doxyfile.
********************************************************************************
"""

import re
import logging

log = logging.getLogger(__name__)

ConfigValue = str | list[str]

KEY_PATTERN = re.compile(r"\w+")
LINE_CONTINUATION = "\\"
COMMENT_PREFIX = "#"


class ParseException(Exception):
    """!
    @brief Exception thrown when a doxyfile line can not be parsed.
    """


def unquote(value: str) -> str:
    """!
    @brief Remove surrounding double quotes from value.
    @param value : value from doxyfile
    @return value without surrounding double quotes
    """
    if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def quote(value: str, force: bool = False) -> str:
    """!
    @brief Surround value with double quotes if it contains spaces or quotes are forced.
    @param value : value to write to doxyfile
    @param force : [True] always add quotes; [False] add quotes only if required
    @return value for doxyfile
    """
    if force or (" " in value):
        return f'"{value}"'
    return value


class ConfigParser:
    """!
    @brief Parse and store a doxygen configuration file (doxyfile).
           Single line options are returned as string, multi line options (lines ending with backslash) as list.
    """

    def load_configuration(self, doxyfile: str) -> dict[str, ConfigValue]:
        """!
        @brief Load doxygen configuration file.
        @param doxyfile : path to the doxygen configuration file
        @return dictionary with all doxygen settings
        """
        configuration: dict[str, ConfigValue] = {}
        open_list: list[str] | None = None  # values of the multi line option that is continued in next line

        with open(doxyfile, mode="r", encoding="utf-8") as file:
            for line_number, raw_line in enumerate(file, start=1):
                line = raw_line.strip()
                if not line or line.startswith(COMMENT_PREFIX):
                    continue

                is_continued = line.endswith(LINE_CONTINUATION)
                if is_continued:
                    line = line[:-len(LINE_CONTINUATION)].rstrip()

                if open_list is not None:
                    open_list.append(unquote(line))
                else:
                    key, separator, value = line.partition("=")
                    key = key.strip()
                    if not separator or not KEY_PATTERN.fullmatch(key):
                        raise ParseException(f"{doxyfile}:{line_number}: invalid line '{raw_line.rstrip()}'")
                    value = unquote(value.strip())
                    if is_continued:
                        open_list = [value]
                        configuration[key] = open_list
                    else:
                        configuration[key] = value

                if not is_continued:
                    open_list = None

        return configuration

    def store_configuration(self, config: dict[str, ConfigValue], doxyfile: str) -> None:
        """!
        @brief Store doxygen configuration file. An existing file will be overwritten.
        @param config : dictionary with doxygen settings
        @param doxyfile : path to the doxygen configuration file
        """
        log.debug("Store configuration in %s", doxyfile)

        lines = []
        for key, value in config.items():
            if isinstance(value, str):
                lines.append(f"{key} = {quote(value)}")
            elif len(value) <= 1:
                lines.append(f"{key} = {quote(value[0], force=True) if value else ''}")
            else:
                quoted_values = [quote(entry, force=True) for entry in value]
                lines.append(f"{key} = {quoted_values[0]} {LINE_CONTINUATION}")
                lines.extend(f"\t{entry} {LINE_CONTINUATION}" for entry in quoted_values[1:-1])
                lines.append(f"\t{quoted_values[-1]}")

        with open(doxyfile, mode="w", encoding="utf-8") as file:
            file.write("\n".join(lines))
