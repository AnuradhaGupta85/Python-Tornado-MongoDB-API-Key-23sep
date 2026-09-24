@echo off
setlocal
if not defined PORT set PORT=25350
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt -q
python main.py
