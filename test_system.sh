#!/bin/bash

echo "============================================"
echo "   SISTEMA DE BONOS DE PANAMA - TESTING"
echo "============================================"
echo

echo "[1/4] Verificando estado de servicios..."
sudo supervisorctl status
echo

echo "[2/4] Testing Backend API..."
if curl -X POST https://bondholding.preview.emergentagent.com/api/auth/login \
   -H "Content-Type: application/json" \
   -d '{"username":"admin","password":"admin123"}' \
   -s > /dev/null; then
    echo "✅ Backend API respondiendo correctamente"
else
    echo "❌ Error en Backend API"
fi
echo

echo "[3/4] Testing aplicación web..."
if curl -I https://bondholding.preview.emergentagent.com -s | grep -q "200 OK"; then
    echo "✅ Aplicación web respondiendo correctamente"  
else
    echo "❌ Error en aplicación web"
fi
echo

echo "[4/4] Ejecutando suite completa de testing backend..."
cd /app
python backend_test.py
echo

echo "============================================"
echo "TESTING COMPLETADO"
echo "============================================"
echo
echo "URLS DE ACCESO:"
echo "- Aplicación: https://bondholding.preview.emergentagent.com"
echo "- Admin: usuario 'admin', contraseña 'admin123'"
echo
echo "ARCHIVOS DE TESTING:"
echo "- Backend: /app/backend_test.py"
echo "- Verificación: /app/verify_securities.py" 
echo "- Guías: /app/*.md"
echo