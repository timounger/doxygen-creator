# Doxygen Creator

Python-Package, das ein Doxyfile mit einheitlichen Einstellungen und eigenem Styling erzeugt und Doxygen ausführt.
Der Bericht wird geöffnet und vorhandene Warnungen werden angezeigt.

## Funktionen

- Lädt die festgelegte Doxygen-Version (1.16.1, Windows) automatisch herunter, kein Eintrag in `Path` nötig
- Styling mit [Doxygen Awesome v2.4.2](https://github.com/jothepro/doxygen-awesome-css/releases/tag/v2.4.2) (Darkmode, Copy-Button, Paragraph-Links, Interactive-TOC, Tabs)
- [GitHub Corner](https://tholman.com/github-corners/) mit Link zum Repository
- PlantUML-Diagramme (`plantuml.jar` wird automatisch geladen, Java erforderlich)
- `DoxyfileDiff.html`: Unterschiede zwischen Default- und verwendetem Doxyfile
- `DoxyPyChecker`: prüft in Python-Dateien, ob alle Parameter und Rückgabewerte mit `@param`/`@return` dokumentiert sind
- Ungültige Doxygen-Einstellungen werden mit Vorschlag gemeldet (`Did you mean ...?`)

## Installation

Voraussetzung: Python >= 3.10.

```bash
pip install "doxygen-creator @ git+https://github.com/timounger/DoxygenCreator.git@v1.0.0"
```

Mit Poetry (z. B. in einer `docs`-Gruppe):

```toml
[tool.poetry.group.docs.dependencies]
doxygen-creator = { git = "https://github.com/timounger/DoxygenCreator.git", tag = "v1.0.0" }
```

oder in einer `requirements.txt`:

```text
doxygen-creator @ git+https://github.com/timounger/DoxygenCreator.git@v1.0.0
```

## Verwendung

### Als Python-Skript im Projekt

```python
import sys
from doxygen_creator import DoxygenCreator, get_cmd_args, PYTHON_PATTERN

args = get_cmd_args()  # -o / --open: Ausgabe nach Erstellung öffnen
doxygen_creator = DoxygenCreator("https://github.com/user/MyProject", project_dir="../")
doxygen_creator.set_configuration("PROJECT_NAME", "MyProject")
doxygen_creator.set_configuration("PROJECT_NUMBER", "1.0.0")  # wird zu "v1.0.0"
doxygen_creator.set_configuration("FILE_PATTERNS", [PYTHON_PATTERN, "*.md"])
doxygen_creator.set_configuration("EXCLUDE_PATTERNS", [".venv", "Documentation"])
sys.exit(doxygen_creator.run_doxygen(open_doxygen_output=args.open))
```

Ein vollständiges Beispiel liegt in [examples/create_doxygen.py](examples/create_doxygen.py).

`run_doxygen()` gibt `True` zurück, wenn Warnungen gefunden wurden. Damit lässt sich z. B. ein CI-Job fehlschlagen lassen.

### Als Kommandozeilentool

```bash
doxygen-creator -p . -n MyProject -v 1.0.0 -w https://github.com/user/MyProject -o
doxygen-creator --help
```

Beliebige weitere Doxygen-Einstellungen: `--set KEY=VALUE` (mehrfach möglich).

Der Doku-Checker kann auch einzeln laufen:

```bash
doxy-py-checker -p Source
```

## Optionen von `DoxygenCreator`

| Parameter      | Default            | Beschreibung                                                                    |
| -------------- | ------------------ | ------------------------------------------------------------------------------- |
| `website`      | `None`             | URL für den GitHub Corner                                                       |
| `project_dir`  | `"."`              | Projektwurzel: Default für `INPUT`, `IMAGE_PATH`, `README.md` als Hauptseite    |
| `tools_dir`    | Benutzer-Cache     | Ablage für Doxygen und PlantUML                                                 |
| `doxygen_exe`  | `None`             | Eigene Doxygen-Installation statt Download verwenden                            |
| `plantuml`     | `True`             | `plantuml.jar` laden und `PLANTUML_JAR_PATH` setzen                             |
| `config_diff`  | `True`             | `DoxyfileDiff.html` erzeugen                                                    |
| `py_checker`   | `True`             | `DoxyPyChecker` ausführen, wenn `*.py` in `FILE_PATTERNS` enthalten ist         |
| `auto_version` | `True`             | Gültige Versionsnummern in `PROJECT_NUMBER` mit `v` versehen                    |

Relative Pfade (z. B. `OUTPUT_DIRECTORY`, `INPUT`, `project_dir`) beziehen sich auf das aktuelle Arbeitsverzeichnis.
Die Ausgabe landet standardmäßig in `Output_Doxygen/`.

`set_configuration(key, value, override=False)` setzt einen Wert nur, wenn er noch nicht gesetzt ist; Listen werden dann erweitert statt ersetzt.

### Tool-Ordner

Doxygen und PlantUML werden versioniert abgelegt in:

1. Umgebungsvariable `DOXYGEN_CREATOR_HOME`, sonst
2. `%LOCALAPPDATA%\doxygen_creator` (Windows), sonst
3. `~/.cache/doxygen_creator`

Auf Linux/macOS wird kein Download durchgeführt, sondern `doxygen` aus `PATH` verwendet (oder `doxygen_exe`).

## Hinweise zum Styling

### Emoji 😀

Es sollten nur Emojis in `UNICODE`-Schreibweise verwendet werden, damit sie von Doxygen korrekt angezeigt werden.

```markdown
# Beispiel für 🤣

&#x1F923;
```

Einfacher ist es, das Emoji per Copy & Paste einzufügen.

## Entwicklung

```bash
setup.bat                 # Abhängigkeiten installieren (Poetry)
tests\run_tests.bat       # Unit-Tests ausführen (Argumente gehen an pytest, z. B. -v)
examples\run_example.bat  # Doku dieses Repos mit examples/create_doxygen.py erstellen und öffnen
```

## CI und Release

Die GitHub-Action [.github/workflows/github-ci.yml](.github/workflows/github-ci.yml) läuft bei jedem Push auf `main`, bei Pull Requests und manuell:

1. **static-Test**: PyLint und MyPy
2. **dynamic-Test**: PyTest unter Python 3.10 und 3.14
3. **build-Package**: Wheel und sdist bauen, Wheel in einer frischen Umgebung installieren und prüfen
4. **run-Example**: `examples/create_doxygen.py` erzeugt die Doku dieses Repos (schlägt bei Doxygen-Warnungen fehl)
5. **create-Release**: Tag `v<version>` und GitHub-Release mit Wheel und sdist

Neue Version veröffentlichen: Änderungen in [CHANGELOG.md](CHANGELOG.md) eintragen, `version` in `pyproject.toml` anheben und auf `main` pushen.
Ändert sich die Version, werden Tag und Release automatisch erstellt.
Alternativ manuell über *Actions → DoxygenCreator CI → Run workflow → Create Release*.

## Lizenz

[MIT](LICENSE) © Timo Unger

Enthaltene Fremdkomponenten:

- [Doxygen Awesome](https://github.com/jothepro/doxygen-awesome-css) (`src/doxygen_creator/assets/doxygen-awesome*`): MIT, © jothepro
- Doxygen und PlantUML werden nicht mitgeliefert, sondern zur Laufzeit von den offiziellen Quellen geladen und unterliegen ihren eigenen Lizenzen (GPL-2.0 bzw. GPL-3.0).
