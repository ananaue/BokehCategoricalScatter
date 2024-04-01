@echo off
for %%a in (*.txt) do (
    "..\dragdrop.py" "%%a"
    "..\dragdrop_svgpng.py" "%%a"
)
pause