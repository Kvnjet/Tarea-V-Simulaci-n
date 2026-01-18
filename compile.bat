@echo off
REM Script de compilación para Windows
REM Asegúrate de tener g++ instalado (MinGW o similar)

setlocal enabledelayedexpansion

echo ====================================
echo Compilacion - Sistema de Colas
echo ====================================
echo.

REM Crear directorios si no existen
if not exist build mkdir build
if not exist bin mkdir bin

REM Compilar archivos
echo Compilando archivos...
g++ -std=c++17 -Wall -Wextra -O2 -c src/main.cpp -o build/main.o
g++ -std=c++17 -Wall -Wextra -O2 -c src/simulation.cpp -o build/simulation.o

if errorlevel 1 (
    echo.
    echo ERROR: Falló la compilación de los archivos objeto
    goto end
)

echo Compilacion completada.
echo.
echo Enlazando...
g++ -std=c++17 -O2 build/main.o build/simulation.o -o bin/simulation.exe

if errorlevel 1 (
    echo ERROR: Falló el enlazamiento
    goto end
)

echo.
echo ====================================
echo Compilacion exitosa!
echo Ejecutable: bin/simulation.exe
echo ====================================
echo.
echo Ejecutar: bin\simulation.exe

:end
endlocal
