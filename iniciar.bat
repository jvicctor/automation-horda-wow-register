@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo WoW Forever em portugues, janela ou janela sem bordas, 1920x1080.
echo A classe e os nomes estao em personagem.txt
echo Para parar: Ctrl+C nesta janela, ou jogue o mouse no canto superior esquerdo.
echo.
"%~dp0.venv\Scripts\python.exe" "%~dp0criar_personagem.py" %*
echo.
pause
