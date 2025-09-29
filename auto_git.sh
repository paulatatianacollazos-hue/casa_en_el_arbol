#!/bin/bash

# Ruta al repositorio
cd /ruta/a/tu/repositorio || exit

# Sube cambios locales si los hay
if [ -n "$(git status --porcelain)" ]; then
  git add .
  git commit -m "Auto commit: $(date '+%Y-%m-%d %H:%M:%S')"
  git push origin main  # o tu rama
fi

# Trae cambios del remoto
git pull origin main  # o tu rama
