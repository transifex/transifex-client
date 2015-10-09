@echo off
pyinstaller -y tx
if %ERRORLEVEL% == 0 goto success
goto error

:success
echo Success packaging, now renaming to Python 3
copy dist\tx.exe win\tx-py3.exe
goto end

:error
echo Unable to create binary
goto end

:end
echo Done