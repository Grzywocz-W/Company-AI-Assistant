@echo off
title Serwer FastAPI - Backend
:: Przejdz do folderu, w ktorym znajduje sie ten plik
cd /d "%~dp0"

uvicorn main:react --reload


pause