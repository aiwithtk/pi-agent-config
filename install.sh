#!/usr/bin/env bash
#
# install.sh — installe la configuration pi de Thierno dans le home de l'utilisateur.
#
# Usage :
#   ./install.sh              installe sans écraser les fichiers déjà présents
#   ./install.sh --force      écrase (avec sauvegarde .bak.<timestamp>)
#   ./install.sh --dry-run    montre ce qui serait fait
#
# Ce script copie :
#   dot-pi/       -> ~/.pi/
#   dot-agents/   -> ~/.agents/
# puis installe les dépendances npm (lib, npm, extensions) et crée les
# fichiers de configuration à partir des *.example (sans écraser l'existant).

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORCE=0
DRY=0

for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --dry-run) DRY=1 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "Option inconnue : $arg" >&2; exit 2 ;;
  esac
done

run() {
  if [ "$DRY" = "1" ]; then
    echo "  [dry-run] $*"
  else
    eval "$@"
  fi
}

echo "==> Cible : HOME=$HOME"
echo

# ----------------------------------------------------------------------------
# 1. Copie des arborescences
# ----------------------------------------------------------------------------
copy_tree() {
  local src="$1" dst="$2"
  echo "==> $src -> $dst"
  run "mkdir -p \"$dst\""
  if [ "$FORCE" = "1" ] && [ -e "$dst" ] && [ ! "$DRY" = "1" ]; then
    cp -a "$dst" "$dst.bak.$(date +%Y%m%d-%H%M%S)"
  fi
  if [ "$DRY" = "1" ]; then
    rsync -a --dry-run --itemize-changes "$src/" "$dst/" | sed 's/^/  [dry-run] /'
  elif [ "$FORCE" = "1" ]; then
    rsync -a "$src/" "$dst/"
  else
    rsync -a --ignore-existing "$src/" "$dst/"
  fi
  echo
}

copy_tree "$REPO_DIR/dot-pi" "$HOME/.pi"
copy_tree "$REPO_DIR/dot-agents" "$HOME/.agents"

# ----------------------------------------------------------------------------
# 2. Fichiers de configuration à partir des exemples
# ----------------------------------------------------------------------------
create_from_example() {
  local example="$1" target="$2" sub="${3:-}"
  [ -f "$example" ] || return 0
  if [ -f "$target" ] && [ "$FORCE" != "1" ]; then
    echo "  = $target (déjà présent, conservé)"
    return 0
  fi
  local dir; dir="$(dirname "$target")"
  run "mkdir -p \"$dir\""
  if [ "$DRY" = "1" ]; then
    echo "  [dry-run] générer $target depuis $(basename "$example")"
  else
    if [ -n "$sub" ]; then
      sed "s|VOTRE_UTILISATEUR|$USER|g; s|YOUR_MACOS_USER|$USER|g" "$example" > "$target"
    else
      sed "s|VOTRE_UTILISATEUR|$USER|g; s|YOUR_MACOS_USER|$USER|g" "$example" > "$target"
    fi
    echo "  + $target"
  fi
}

echo "==> Fichiers de configuration"
create_from_example "$REPO_DIR/dot-pi/agent/mcp.json.example"                      "$HOME/.pi/agent/mcp.json"
create_from_example "$REPO_DIR/dot-pi/agent/auth.json.example"                     "$HOME/.pi/agent/auth.json"
create_from_example "$REPO_DIR/dot-pi/agent/trust.json.example"                    "$HOME/.pi/agent/trust.json"
create_from_example "$REPO_DIR/dot-pi/agent/pi-langfuse/config.example.json"       "$HOME/.pi/agent/pi-langfuse/config.json"
echo

# ----------------------------------------------------------------------------
# 3. Droits d'exécution
# ----------------------------------------------------------------------------
echo "==> chmod +x des scripts"
run "chmod +x $HOME/.pi/agent/bin/* 2>/dev/null || true"
echo

# ----------------------------------------------------------------------------
# 4. Dépendances npm
# ----------------------------------------------------------------------------
npm_install() {
  local dir="$1"
  [ -f "$dir/package.json" ] || return 0
  echo "==> npm install dans ${dir/#$HOME/~}"
  if [ "$DRY" = "1" ]; then
    echo "  [dry-run] npm install --prefix \"$dir\""
  else
    ( cd "$dir" && npm install --no-audit --no-fund )
  fi
  echo
}

npm_install "$HOME/.pi/agent/lib"
npm_install "$HOME/.pi/agent/npm"

for ext in "$REPO_DIR"/dot-pi/agent/extensions/*/; do
  if [ -f "$ext/package.json" ]; then
    npm_install "$HOME/.pi/agent/extensions/$(basename "$ext")"
  fi
done

# ----------------------------------------------------------------------------
# 5. Rappel
# ----------------------------------------------------------------------------
cat <<'EOF'
==> Terminé.

Étapes manuelles restantes (secrets, non versionnés) :

  1. Remplis les clés API dans  ~/.pi/agent/auth.json
     (xai, deepseek, moonshotai, zai) — voir auth.json.example.

  2. Renseigne les secrets MCP / prestataires :
       • MongoDB local + Atlas : stocke les URI dans le Trousseau macOS
             security add-generic-password -s pi-mongod-local-agent -a "$USER" -w 'mongodb://...'
             security add-generic-password -s pi-mongodb-atlas      -a "$USER" -w 'mongodb+srv://...'
       • Jev      : security add-generic-password -s pi-jev-api     -a "$USER" -w '<cle>'
       • treg     : security add-generic-password -s pi-treg-token  -a "$USER" -w '<token>'
       • n8n      : exporte N8N_API_URL et N8N_API_KEY avant de lancer pi
       • Langfuse : remplis ~/.pi/agent/pi-langfuse/config.json

  3. Recherche web Google : crée ~/.pi/agent/extensions/web-search/auth.json
     à partir de auth.example.json (api key + CSE id).

  4. Initialise la base de mémoire :  ~/.pi/agent/bin/brain init

  5. Lance pi puis :  /reload   (ou redémarre le CLI).

Voir README.md pour le détail de chaque composant.
EOF
