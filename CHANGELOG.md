# Changelog 📋️

## v1.0.0

Erste Version als eigenständiges Python-Package, ausgelagert aus `BonPrinter/Documentation/DoxygenCreator`.

### Features

- Installierbar per `pip`/Poetry direkt aus GitHub (`doxygen-creator @ git+https://github.com/timounger/DoxygenCreator.git@v1.0.0`)
- Doxygen 1.16.1 und PlantUML 1.2026.5 werden automatisch in einen versionierten Tool-Ordner geladen (`%LOCALAPPDATA%\doxygen_creator`, änderbar über `DOXYGEN_CREATOR_HOME` oder `tools_dir`)
- Styling mit Doxygen Awesome v2.4.2 und eigener `header.html` sind im Package enthalten
- Neue Parameter für `DoxygenCreator`: `project_dir`, `tools_dir`, `doxygen_exe`, `plantuml`, `config_diff`, `py_checker`, `auto_version`
- Kommandozeilentools `doxygen-creator` und `doxy-py-checker`
- `DoxyPyChecker` mit Option `check_typing` statt globaler Konstante
- Unter Linux/macOS wird `doxygen` aus `PATH` verwendet
- Beispielskript `examples/create_doxygen.py` liest Name, Version, Beschreibung, Autor und URL aus der `pyproject.toml`
- GitHub CI: PyLint, MyPy, PyTest (Python 3.10 und 3.14), Package-Build, Beispiel-Doku und automatisches Release mit Tag

### Änderungen

- Projektspezifische Imports (`Source.*`, `Documentation.DoxygenCreator.*`) und feste Pfade (`MAIN_FOLDER`) entfernt
- Lizenz: MIT
- Doxyfile-Parser `config_parser.py` neu geschrieben (ersetzt den aus GPL-3.0-Code abgeleiteten `configParser.py`); ungültige Zeilen lösen jetzt `ParseException` aus statt ignoriert zu werden
- Abhängigkeit `astunparse` entfernt (ersetzt durch `ast.unparse`)
- Fehler beim Doxygen-Download lösen `DoxygenCreatorError` aus statt `sys.exit`
- Version wird nur noch in der `pyproject.toml` gepflegt

### Bug fixes

- Einstellungen wurden als Klassenvariable zwischen mehreren `DoxygenCreator`-Instanzen geteilt
- `-o False` hat die Ausgabe trotzdem geöffnet (`type=bool`); jetzt funktionieren `-o`, `-o True` und `-o False`
- Listen mit einem Eintrag wurden doppelt ins Doxyfile geschrieben, leere Listen führten zu einem Absturz
- Anführungszeichen in mehrzeiligen Doxyfile-Werten wurden beim Einlesen nicht entfernt
