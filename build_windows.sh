#!/usr/bin/env bash
set -e

# ============================
# Configurações
# ============================
PROJECT_NAME="GRASS"
ENTRYPOINT="src/main.py"
ASSETS_DIR="assets"
ICON_FILE="icon.png"

PYTHON_VERSION="3.11.8"
PYTHON_INSTALLER="python-${PYTHON_VERSION}-amd64.exe"

WINEPREFIX="$HOME/.wine-pyinstaller"
WINEARCH="win64"

# ============================
# Ambiente Wine
# ============================
export WINEPREFIX
export WINEARCH

echo "🍷 Usando WINEPREFIX: $WINEPREFIX"

# ============================
# Criar prefix se não existir
# ============================
if [ ! -d "$WINEPREFIX" ]; then
  echo "🧱 Criando Wine prefix..."
  winecfg >/dev/null 2>&1
fi

# ============================
# Verificar Python
# ============================
if ! wine python --version >/dev/null 2>&1; then
  echo "🐍 Python não encontrado no Wine."
  echo "➡️ Instale o Python ${PYTHON_VERSION} para Windows e marque 'Add to PATH'."
  echo "Arquivo esperado: ${PYTHON_INSTALLER}"
  exit 1
fi

echo "✅ Python encontrado:"
wine python --version

# ============================
# Dependências Python
# ============================
echo "📦 Instalando dependências Python..."
wine pip install pygame pyinstaller

# ============================
# Limpar builds antigos
# ============================
echo "🧹 Limpando builds antigos..."
rm -rf build dist *.spec

# ============================
# Build
# ============================
echo "🚀 Buildando ${PROJECT_NAME}.exe..."

wine pyinstaller \
  --noconfirm \
  --windowed \
  --name "$PROJECT_NAME" \
  --add-data "${ASSETS_DIR};${ASSETS_DIR}" \
  --icon "$ICON_FILE" \
  "$ENTRYPOINT"

# ============================
# Final
# ============================
echo ""
echo "🎉 Build concluído com sucesso!"
echo "📁 Executável:"
echo "dist/${PROJECT_NAME}/${PROJECT_NAME}.exe"
echo ""
echo "▶️ Teste com:"
echo "wine dist/${PROJECT_NAME}/${PROJECT_NAME}.exe"

