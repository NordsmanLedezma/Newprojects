@echo off
echo ============================================
echo    SISTEMA DE BONOS DE PANAMA - TESTING
echo ============================================
echo.

echo [1/4] Verificando estado de servicios...
sudo supervisorctl status
echo.

echo [2/4] Testing Backend API...
curl -X POST https://bondregistry.preview.emergentagent.com/api/auth/login -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"admin123\"}" 2>nul
if %errorlevel% equ 0 (
    echo ✅ Backend API respondiendo correctamente
) else (
    echo ❌ Error en Backend API
)
echo.

echo [3/4] Testing aplicacion web...
curl -I https://bondregistry.preview.emergentagent.com 2>nul | findstr "200 OK" >nul
if %errorlevel% equ 0 (
    echo ✅ Aplicacion web respondiendo correctamente
) else (
    echo ❌ Error en aplicacion web
)
echo.

echo [4/4] Ejecutando suite completa de testing backend...
cd /app
python backend_test.py
echo.

echo ============================================
echo TESTING COMPLETADO
echo ============================================
echo.
echo URLS DE ACCESO:
echo - Aplicacion: https://bondregistry.preview.emergentagent.com
echo - Admin: usuario 'admin', contraseña 'admin123'
echo.
echo ARCHIVOS DE TESTING:
echo - Backend: /app/backend_test.py
echo - Verificacion: /app/verify_securities.py
echo - Guias: /app/*.md
echo.
pause