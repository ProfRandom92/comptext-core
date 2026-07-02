# Rust Token Killer (RTK) Terminal Proxy Setup (rtk-proxy.md)

Dieses Dokument beschreibt, wie Entwickler den **RTK (Rust Token Killer)** terminal-proxy lokal vorschalten können, um redundante Compiler- und Test-Rückgaben zu filtern. Dies spart im Entwicklungs- und Testbetrieb **über 70% der Token** ein, wenn LLMs Terminals auswerten.

---

## 1. Was ist RTK?

Der **RTK (Rust Token Killer)** fängt Konsolenausgaben (wie den Output von `pytest` oder Compilern) ab. Er analysiert diese in Echtzeit und kürzt:
- Sich wiederholende Zeilen (z. B. lange Ladebalken, Fortschrittsanzeigen).
- Redundante Stapelüberwachungsausgaben (Stacktraces), die sich in mehreren fehlgeschlagenen Tests wiederholen.
- Compiler-Warnungen, die für das aktuelle Testziel irrelevant sind.

Repository: [https://github.com/rtk-ai/rtk](https://github.com/rtk-ai/rtk)

---

## 2. Installation und Einrichtung

### A. Installation via Cargo (Rust erforderlich)
```bash
cargo install rtk-proxy
```

### B. Konfigurationsdatei `.rtk.toml` erstellen
Erstelle eine Konfigurationsdatei `.rtk.toml` im Projektverzeichnis, um Filterregeln zu definieren:
```toml
# .rtk.toml
[filter]
# Ignoriere sich wiederholende Warnungen (z. B. Deprecation Warnings)
exclude_patterns = [
    ".*PendingDeprecationWarning.*",
    ".*import multipart.*"
]

# Kürze lange Stacktraces bei Fehlern
max_traceback_lines = 15
```

---

## 3. Nutzung im Testbetrieb

Entwickler können Befehle einfach durch das Vorschalten von `rtk run` ausführen.

### Pytest über RTK ausführen:
```bash
rtk run pytest -v
```

### Automatisierungsskript (`bin/rtk-test.sh`)
Du kannst folgendes Skript nutzen, um Tests automatisch über den Proxy laufen zu lassen:
```bash
#!/bin/bash
# bin/rtk-test.sh
if command -v rtk &> /dev/null; then
    echo "Running tests via RTK Token Killer Proxy..."
    rtk run pytest -v "$@"
else
    echo "RTK proxy not found. Running standard pytest..."
    pytest -v "$@"
fi
```
Make the script executable:
```bash
chmod +x bin/rtk-test.sh
```
