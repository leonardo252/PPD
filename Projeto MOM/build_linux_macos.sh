#!/bin/sh
set -eu
python3 -m pip install -r requirements-dev.txt
python3 -m PyInstaller --noconfirm --clean --onefile --windowed --name MOM-Cliente client_app.py
python3 -m PyInstaller --noconfirm --clean --onefile --windowed --name MOM-Dashboard dashboard_app.py
python3 -m PyInstaller --noconfirm --clean --onefile --console --name MOM-Worker worker_app.py
echo "Executaveis criados na pasta dist/."
