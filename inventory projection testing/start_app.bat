@echo off
setlocal
cd /d "%~dp0"
start "Spruce Inventory Reorder Tool" http://localhost:8501
python -m streamlit run app.py --server.address=127.0.0.1 --server.port=8501
