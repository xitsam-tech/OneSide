#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_DIR="$ROOT_DIR/server"
REQUIREMENTS_FILE="$ROOT_DIR/requirements.txt"
ENV_EXAMPLE_FILE="$ROOT_DIR/.env.example"
ENV_FILE="$ROOT_DIR/.env"

print_step() {
  echo
  echo "==> $1"
}

check_required_tools() {
  local tools=(node npm python3 pip)
  local missing=()

  for tool in "${tools[@]}"; do
    if ! command -v "$tool" >/dev/null 2>&1; then
      missing+=("$tool")
    fi
  done

  if (( ${#missing[@]} > 0 )); then
    echo "❌ Fehlende Tools: ${missing[*]}"
    echo "Bitte installiere die fehlenden Tools und starte das Setup erneut."
    exit 1
  fi

  echo "✅ Alle benötigten Tools sind vorhanden: ${tools[*]}"
}

install_js_dependencies() {
  if [[ ! -d "$SERVER_DIR" ]]; then
    echo "❌ Server-Ordner nicht gefunden: $SERVER_DIR"
    exit 1
  fi

  if [[ ! -f "$SERVER_DIR/package.json" ]]; then
    echo "❌ package.json fehlt in: $SERVER_DIR"
    exit 1
  fi

  if [[ ! -f "$SERVER_DIR/package-lock.json" ]]; then
    echo "⚠️  package-lock.json fehlt. Erzeuge Lockfile mit npm install --package-lock-only ..."
    (
      cd "$SERVER_DIR"
      npm install --package-lock-only
    )
  fi

  echo "Installiere JavaScript-Abhängigkeiten (npm ci) in $SERVER_DIR ..."
  (
    cd "$SERVER_DIR"
    npm ci
  )
  echo "✅ JavaScript-Abhängigkeiten installiert."
}

install_python_dependencies() {
  if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
    echo "⚠️  requirements.txt nicht gefunden ($REQUIREMENTS_FILE). Überspringe Python-Installation."
    return
  fi

  if grep -Eq '^[[:space:]]*[^#[:space:]]' "$REQUIREMENTS_FILE"; then
    echo "Installiere Python-Abhängigkeiten aus requirements.txt ..."
    pip install -r "$REQUIREMENTS_FILE"
    echo "✅ Python-Abhängigkeiten installiert."
  else
    echo "ℹ️  requirements.txt ist leer (oder enthält nur Kommentare). Keine Python-Abhängigkeiten zu installieren."
  fi
}

create_env_file() {
  if [[ ! -f "$ENV_EXAMPLE_FILE" ]]; then
    echo "❌ .env.example fehlt im Repo-Root ($ENV_EXAMPLE_FILE)."
    exit 1
  fi

  if [[ -f "$ENV_FILE" ]]; then
    echo "ℹ️  .env existiert bereits. Keine Änderungen vorgenommen."
    return
  fi

  cp "$ENV_EXAMPLE_FILE" "$ENV_FILE"
  echo "✅ .env wurde aus .env.example erstellt."
}

main() {
  print_step "Prüfe benötigte Tools"
  check_required_tools

  print_step "Installiere JS-Abhängigkeiten"
  install_js_dependencies

  print_step "Installiere Python-Abhängigkeiten"
  install_python_dependencies

  print_step "Erzeuge .env falls nötig"
  create_env_file

  echo
  echo "🎉 Setup abgeschlossen."
}

main "$@"
