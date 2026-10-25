"""!
********************************************************************************
@file   test_doxygen_creator.py
@brief  Unit tests for doxygen_creator (without running doxygen).
********************************************************************************
"""

from pathlib import Path

import pytest

from doxygen_creator import ConfigParser, ParseException, DoxygenCreator, DoxyPyChecker, get_cmd_args
from doxygen_creator.creator import ASSETS_DIR, AWESOME_EXTRA_FILES, AWESOME_STYLESHEETS, HEADER_FILE


def test_assets_are_packaged() -> None:
    """!
    @brief All styling files must be part of the package.
    """
    for name in AWESOME_EXTRA_FILES + AWESOME_STYLESHEETS + [HEADER_FILE]:
        assert (ASSETS_DIR / name).is_file(), name


def test_config_parser_roundtrip(tmp_path: Path) -> None:
    """!
    @brief Stored configuration can be loaded again.
    @param tmp_path : temporary folder
    """
    doxyfile = tmp_path / "Test.Doxyfile"
    config: dict[str, str | list[str]] = {"PROJECT_NAME": "My Project", "INPUT": ["a", "b c"], "RECURSIVE": "YES"}
    ConfigParser().store_configuration(config, str(doxyfile))
    assert ConfigParser().load_configuration(str(doxyfile)) == config


def test_config_parser_short_lists(tmp_path: Path) -> None:
    """!
    @brief Lists with zero or one entry are written as single line without duplicates.
    @param tmp_path : temporary folder
    """
    doxyfile = tmp_path / "Test.Doxyfile"
    ConfigParser().store_configuration({"INPUT": ["src"], "FILE_PATTERNS": []}, str(doxyfile))
    assert doxyfile.read_text(encoding="utf-8").splitlines() == ['INPUT = "src"', "FILE_PATTERNS = "]
    assert ConfigParser().load_configuration(str(doxyfile)) == {"INPUT": "src", "FILE_PATTERNS": ""}


def test_config_parser_load_doxyfile(tmp_path: Path) -> None:
    """!
    @brief Comments are skipped, quotes removed and invalid lines rejected.
    @param tmp_path : temporary folder
    """
    doxyfile = tmp_path / "Test.Doxyfile"
    doxyfile.write_text('# comment\n\nPROJECT_BRIEF = "My brief"\nABBREVIATE_BRIEF = "The $name class" \\\n'
                        '                   is \\\n                   the\nINPUT = C:\\path\\to\\src\n', encoding="utf-8")
    assert ConfigParser().load_configuration(str(doxyfile)) == {"PROJECT_BRIEF": "My brief",
                                                                "ABBREVIATE_BRIEF": ["The $name class", "is", "the"],
                                                                "INPUT": "C:\\path\\to\\src"}
    doxyfile.write_text("NO_ASSIGNMENT\n", encoding="utf-8")
    with pytest.raises(ParseException):
        ConfigParser().load_configuration(str(doxyfile))


def test_settings_are_independent_per_instance() -> None:
    """!
    @brief Settings of one instance must not leak into another instance.
    """
    first = DoxygenCreator()
    first.set_configuration("FILE_PATTERNS", ["*.py"])
    first.set_configuration("PROJECT_NAME", "First")
    second = DoxygenCreator()
    assert second.get_configuration("FILE_PATTERNS") == []
    assert second.get_configuration("PROJECT_NAME") == "MyProject"


def test_prepare_configuration(tmp_path: Path) -> None:
    """!
    @brief Defaults depending on other parameters are set without overriding user settings.
    @param tmp_path : temporary folder
    """
    (tmp_path / "README.md").write_text("# Test", encoding="utf-8")
    creator = DoxygenCreator(project_dir=str(tmp_path), tools_dir=str(tmp_path / "tools"))
    creator.set_configuration("PROJECT_NAME", "Demo")
    creator.set_configuration("PROJECT_NUMBER", "1.2.3")
    creator.set_configuration("EXCLUDE_PATTERNS", [".venv"])
    creator.prepare_doxyfile_configuration()

    assert creator.get_configuration("PROJECT_NUMBER") == "v1.2.3"
    assert creator.get_configuration("PROJECT_BRIEF") == "Demo-Documentation"
    assert creator.get_configuration("INPUT") == [str(tmp_path)]
    assert creator.get_configuration("EXCLUDE_PATTERNS") == [".venv", "Output_Doxygen"]
    assert creator.get_configuration("USE_MDFILE_AS_MAINPAGE") == str(tmp_path / "README.md")
    assert Path(creator.get_configuration("HTML_HEADER")).is_file()
    assert creator.get_configuration("PLANTUML_JAR_PATH").endswith("plantuml.jar")
    assert "\\" not in creator.get_configuration("PLANTUML_JAR_PATH")


def test_open_argument() -> None:
    """!
    @brief Open argument supports flag and explicit bool value.
    """
    assert get_cmd_args([]).open is False
    assert get_cmd_args(["-o"]).open is True
    assert get_cmd_args(["-o", "True"]).open is True
    assert get_cmd_args(["-o", "False"]).open is False


def test_doxy_py_checker(tmp_path: Path) -> None:
    """!
    @brief Checker finds undocumented parameters and missing return documentation.
    @param tmp_path : temporary folder
    """
    code = '''
def good(value):
    """!
    @brief Good.
    @param value : value
    @return value
    """
    return value


def bad(value, other):
    """!
    @brief Bad.
    @param value : value
    """
    return value
'''
    (tmp_path / "module.py").write_text(code, encoding="utf-8")
    findings = DoxyPyChecker(str(tmp_path), print_checked_files=False).run_check()
    assert len(findings) == 1
    assert "bad" in findings[0]
    assert "other is not documented" in findings[0]
    assert "Return type is not documented" in findings[0]
