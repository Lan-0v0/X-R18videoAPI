@echo off
call "D:\AstrBot\AstrBot-deploy\venv\Scripts\activate.bat"
#路径仅供参考
pip install flask>=2.0.0 requests>=2.25.0 beautifulsoup4>=4.9.0
python AstrBot_X-R18videoAPI.py
pause
