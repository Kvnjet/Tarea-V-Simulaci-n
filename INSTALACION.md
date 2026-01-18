# Guía de Instalación de Compilador C++

Para compilar el proyecto, necesitas instalar un compilador C++. Aquí hay varias opciones:

## Opción 1: MinGW-w64 (Recomendado para Windows)

### Descarga e Instalación

1. **Descargar MinGW-w64**:
   - Ir a: https://www.mingw-w64.org/downloads/
   - Descargar la versión más reciente (online installer)

2. **Ejecutar instalador**:
   - Seguir los pasos del instalador
   - Elegir:
     - Architecture: x86_64 (para sistemas de 64 bits)
     - Threads: posix
     - Exception: seh

3. **Agregar al PATH**:
   - Abrir Variables de Entorno en Windows
   - Editar variable `PATH` del sistema
   - Agregar la carpeta `bin` de MinGW (ej: `C:\mingw-w64\bin`)
   - Reiniciar PowerShell/cmd

4. **Verificar instalación**:
   ```powershell
   g++ --version
   ```

## Opción 2: Usar WSL 2 (Windows Subsystem for Linux)

Si tienes WSL 2 instalado, dentro de Linux:

```bash
sudo apt update
sudo apt install build-essential
g++ --version
```

Luego compilar con:
```bash
cd "/mnt/c/Users/kvnes/OneDrive/Documentos/GitHub/Tarea-V-Simulaci-n"
make
./bin/simulation
```

## Opción 3: Visual Studio Community (Alternativa)

1. Descargar Visual Studio Community (gratis)
2. Instalar "Desktop development with C++"
3. Usar Visual Studio IDE para compilar y ejecutar

## Opción 4: Online Compiler (Para pruebas rápidas)

- Usar compiladores online como:
  - https://www.onlinegdb.com/
  - https://replit.com/
  - https://godbolt.org/

## Después de Instalar MinGW

### En PowerShell:

```powershell
# Navegar al directorio del proyecto
cd "C:\Users\kvnes\OneDrive\Documentos\GitHub\Tarea-V-Simulaci-n"

# Compilar
g++ -std=c++17 -O2 src/main.cpp src/simulation.cpp -o bin/simulation.exe

# Ejecutar
.\bin\simulation.exe
```

### En CMD:

```cmd
cd "C:\Users\kvnes\OneDrive\Documentos\GitHub\Tarea-V-Simulaci-n"

REM Compilar
g++ -std=c++17 -O2 src\main.cpp src\simulation.cpp -o bin\simulation.exe

REM Ejecutar
bin\simulation.exe
```

## Requisitos Mínimos

- **Compilador**: g++ versión 7.0 o superior
- **Standard**: C++17 o superior
- **Librerías**: Solo STL (incluidas en el compilador)

## Instalación Rápida con Chocolatey

Si tienes Chocolatey instalado:

```powershell
choco install mingw
```

## Solución de Problemas

### Error: "g++ no se reconoce"

1. Verificar que MinGW está instalado
2. Verificar que está en el PATH
3. Reiniciar PowerShell después de cambiar PATH

### Error: "std::random no encontrado"

Necesitas usar `-std=c++17` al compilar. Algunos archivos .bat ya lo hacen.

### El ejecutable no se encuentra

Asegúrate de que la carpeta `bin/` existe o créala manualmente:
```powershell
mkdir bin
```

---

Una vez instalado el compilador, ejecuta desde el directorio raíz del proyecto:

```powershell
.\compile.bat
```

¡La compilación debería ser exitosa!
