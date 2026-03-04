@echo off
if "%1"=="" goto help
if "%1"=="create-venv" goto create-venv
if "%1"=="activate" goto activate
if "%1"=="install" goto install
if "%1"=="lint" goto lint
if "%1"=="test" goto test
if "%1"=="clean" goto clean
goto help

:create-venv
echo Creating virtual environment...
python -m venv venv
echo Done! Run: tasks.bat activate
goto end

:activate
echo Activating virtual environment...
call .\venv\Scripts\activate
goto end

:install
echo Installing dependencies...
call venv\Scripts\activate.bat && pip install -r requirements.txt
goto end

:lint
echo Running linting...
call venv\Scripts\activate.bat && flake8 .
goto end

:test
echo Running tests...
call venv\Scripts\activate.bat && pytest
goto end

:clean
echo Removing virtual environment...
rmdir /s /q venv
goto end

:help
echo Usage: tasks.bat [command]
echo.
echo Commands:
echo   create-venv  - Create virtual environment
echo   activate     - Activate virtual environment
echo   install      - Install dependencies from requirements.txt
echo   lint         - Run flake8 linting
echo   test         - Run pytest tests
echo   clean        - Remove virtual environment
goto end

:end
