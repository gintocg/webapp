@echo off
echo Starting College Bus Tracker Web Application...
cd %~dp0
set FLASK_APP=app.py
set FLASK_ENV=development
python app.py
