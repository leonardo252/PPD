@echo off
python -m pip install -r requirements-dev.txt
python -m PyInstaller --noconfirm --clean --onefile --windowed --name MOM-Cliente client_app.py
python -m PyInstaller --noconfirm --clean --onefile --windowed --name MOM-Dashboard dashboard_app.py
python -m PyInstaller --noconfirm --clean --onefile --console --name MOM-Worker worker_app.py
echo Executaveis criados na pasta dist.
