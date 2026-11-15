@echo off
cd /d "%~dp0.."
python collectors\nhs_collect.py
pause
