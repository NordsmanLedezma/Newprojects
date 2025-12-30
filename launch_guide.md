# 🚀 GUÍA DE LANZAMIENTO Y TESTING - Sistema de Bonos de Panamá

## 📋 ESTADO ACTUAL DEL SISTEMA

### ✅ **Aplicación Ya Ejecutándose:**
La aplicación está **ACTIVA** y ejecutándose automáticamente via supervisord:
- **Frontend**: Puerto 3000 (React)
- **Backend**: Puerto 8001 (FastAPI) 
- **Base de datos**: MongoDB activa
- **URL Pública**: https://bondholding.preview.emergentagent.com

---

## 🧪 ARCHIVOS PARA TESTING

### **1. Testing Automatizado Backend** 
```bash
# Archivo principal de testing backend
/app/backend_test.py

# Ejecutar testing completo backend:
cd /app
python backend_test.py
```

### **2. Testing Manual API**
```bash
# Testing de login
curl -X POST https://bondholding.preview.emergentagent.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Testing de valores ISIN
curl -X GET https://bondholding.preview.emergentagent.com/api/admin/securities \
  -H "Authorization: Bearer [TOKEN]"
```

### **3. Verificación de Datos**
```bash
# Verificar valores importados
cd /app
python verify_securities.py
```

---

## 🚀 COMANDOS DE LANZAMIENTO

### **Opción 1: Sistema ya Activo (RECOMENDADO)**
```bash
# Verificar estado actual
sudo supervisorctl status

# Debe mostrar:
# backend    RUNNING
# frontend   RUNNING  
# mongodb    RUNNING
```

### **Opción 2: Reinicio Completo**
```bash
# Reiniciar todos los servicios
sudo supervisorctl restart all

# Verificar que estén ejecutándose
sudo supervisorctl status
```

### **Opción 3: Lanzamiento Manual (Solo si supervisord falla)**
```bash
# Terminal 1 - Backend
cd /app/backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2 - Frontend  
cd /app/frontend
npm start

# Terminal 3 - MongoDB (si no está activo)
sudo systemctl start mongod
```

---

## 🌐 ACCESO A LA APLICACIÓN

### **URLs de Acceso:**
- **Aplicación Web**: https://bondholding.preview.emergentagent.com
- **API Backend**: https://bondholding.preview.emergentagent.com/api
- **Documentación API**: https://bondholding.preview.emergentagent.com/docs

### **Credenciales de Administrador:**
```
Usuario: admin
Contraseña: admin123

Usuario Alternativo: superadmin  
Contraseña: Panama2025!
```

---

## 🧪 TESTING PASO A PASO

### **1. Testing Backend (API)**
```bash
# Cambiar al directorio principal
cd /app

# Ejecutar suite completa de testing backend
python backend_test.py

# Resultado esperado:
# ✅ Tests run: 12+
# ✅ Tests passed: 12+  
# ✅ Success rate: 100%
```

### **2. Testing Frontend (Navegador)**
```bash
# Abrir en navegador
https://bondholding.preview.emergentagent.com

# Pasos de testing manual:
1. Login como admin (admin/admin123)
2. Navegar a "Valores ISIN" 
3. Verificar tabla con 39+ valores
4. Probar editar un valor (botón ✏️)
5. Probar importar Excel
6. Probar funciones de administrador
```

### **3. Testing de Integración Completa**
```bash
# Testing automatizado completo (requiere navegador)
cd /app
python -c "
import requests
print('🔐 Testing login...')
response = requests.post('https://bondholding.preview.emergentagent.com/api/auth/login', 
                        json={'username':'admin','password':'admin123'})
if response.status_code == 200:
    print('✅ Login successful')
    token = response.json()['access_token']
    
    print('📊 Testing securities...')
    securities = requests.get('https://bondholding.preview.emergentagent.com/api/admin/securities',
                            headers={'Authorization': f'Bearer {token}'})
    if securities.status_code == 200:
        count = len(securities.json())
        print(f'✅ Securities loaded: {count} values')
    else:
        print('❌ Securities failed')
else:
    print('❌ Login failed')
"
```

---

## 📁 ARCHIVOS CLAVE DEL SISTEMA

### **Aplicación Principal:**
```
/app/backend/server.py          # API FastAPI principal
/app/frontend/src/App.js        # Interfaz React principal  
/app/frontend/src/App.css       # Estilos de la aplicación
```

### **Configuración:**
```
/app/backend/.env               # Variables backend
/app/frontend/.env              # Variables frontend
/app/backend/requirements.txt   # Dependencias Python
/app/frontend/package.json      # Dependencias Node.js
```

### **Datos de Testing:**
```
/app/panama_bonds_formatted.xlsx    # Excel con bonos importados
/app/valores_test_import.xlsx       # Excel de testing
/app/verify_securities.py           # Verificación de datos
```

### **Testing y Documentación:**
```
/app/backend_test.py                # Testing automatizado backend
/app/guia_edicion_valores.md        # Guía de edición 
/app/guia_importacion_excel.md      # Guía de importación
/app/launch_guide.md                # Esta guía
```

---

## ⚡ COMANDOS RÁPIDOS DE VERIFICACIÓN

### **Estado de Servicios:**
```bash
# Ver todos los servicios
sudo supervisorctl status

# Ver logs en tiempo real
tail -f /var/log/supervisor/backend*.log
tail -f /var/log/supervisor/frontend*.log
```

### **Testing Rápido:**
```bash
# Test backend API
curl https://bondholding.preview.emergentagent.com/api/admin/securities

# Test aplicación web
curl -I https://bondholding.preview.emergentagent.com
```

### **Base de Datos:**
```bash
# Conectar a MongoDB
mongo

# Ver base de datos
use bondregistry
db.securities.count()  # Debe mostrar ~39
```

---

## 🚨 SOLUCIÓN DE PROBLEMAS

### **Si los servicios no están ejecutándose:**
```bash
# Reiniciar supervisor
sudo systemctl restart supervisor

# Reiniciar servicios individuales
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
sudo supervisorctl restart mongodb
```

### **Si hay errores de dependencias:**
```bash
# Backend
cd /app/backend
pip install -r requirements.txt

# Frontend  
cd /app/frontend
yarn install
```

### **Si hay errores de base de datos:**
```bash
# Verificar MongoDB
sudo systemctl status mongod
sudo systemctl start mongod
```

---

## ✅ CHECKLIST DE VERIFICACIÓN

### **Sistema Funcionando Correctamente Cuando:**
- [ ] `sudo supervisorctl status` muestra todos RUNNING
- [ ] https://bondholding.preview.emergentagent.com carga correctamente
- [ ] Login admin/admin123 funciona
- [ ] Tabla "Valores ISIN" muestra 39+ bonos
- [ ] `python backend_test.py` pasa todos los tests
- [ ] APIs responden correctamente con curl

### **Funcionalidades Operativas:**
- [ ] ✅ Login de administradores
- [ ] ✅ Crear usuarios de casas de corretaje  
- [ ] ✅ Gestionar valores ISIN/Latinex
- [ ] ✅ Editar valores individuales
- [ ] ✅ Importar desde Excel
- [ ] ✅ Exportar a Excel
- [ ] ✅ Registrar tenencias
- [ ] ✅ Base de datos consolidada

---

## 📞 SOPORTE

**Estado Actual**: ✅ **SISTEMA COMPLETAMENTE OPERATIVO**

Para testing adicional o problemas técnicos, todos los archivos de testing y documentación están disponibles en `/app/`.