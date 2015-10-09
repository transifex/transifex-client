@echo off
pyinstaller -y tx
if %ERRORLEVEL% == 0 goto success
goto error

:success
echo Success packaging, now renaming to Python 2.7
copy dist\tx.exe win\tx-py27.exe
goto end

:error
echo Unable to create binary
goto end

:end
echo Done