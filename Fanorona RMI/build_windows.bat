@echo off
python -m pip install -r requirements-dev.txt
python -m PyInstaller --noconfirm --clean --onefile --windowed --name FanoronaPyro main.py
echo Executavel criado em dist\FanoronaPyro.exe
