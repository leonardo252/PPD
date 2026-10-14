#!/bin/sh
set -eu
python3 -m pip install -r requirements-dev.txt
python3 -m PyInstaller --noconfirm --clean --onefile --windowed --name FanoronaPyro main.py
echo "Executavel criado na pasta dist/"
