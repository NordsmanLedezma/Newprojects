# 👥 USUARIOS Y CREDENCIALES DEL SISTEMA

## 🔐 ADMINISTRADORES DEL SISTEMA

### **Administrador Principal**
```
Usuario: admin
Contraseña: admin123
Email: admin@sistema.com
Tipo: Administrador por defecto
Estado: ✅ ACTIVO
Creado: 2025-10-05
```

### **Super Administrador**
```
Usuario: superadmin  
Contraseña: Panama2025!
Email: superadmin@bonos.gob.pa
Tipo: Super administrador
Estado: ✅ ACTIVO
Creado: 2025-10-05
```

---

## 👨‍💼 USUARIOS DE CASAS DE CORRETAJE

### **Usuario Activo 1**
```
Usuario: testuser
Contraseña: testpassword123
Email: test@example.com
Casa de Corretaje: Casa de Prueba
Estado: ✅ ACTIVO
Creado: 2025-10-05
```

### **Usuario Activo 2**
```
Usuario: testuser_11622
Contraseña: testpassword123
Email: testuser_11622@test.com
Casa de Corretaje: Test Brokerage  
Estado: ✅ ACTIVO
Creado: 2025-10-20
```

### **Usuarios de Prueba (Inactivos)**
Los siguientes usuarios fueron creados durante testing y están desactivados:

```
Usuario: testuser_170729
Contraseña: testpassword123
Estado: ❌ INACTIVO

Usuario: testuser_170943  
Contraseña: testpassword123
Estado: ❌ INACTIVO

Usuario: testuser_161804
Contraseña: testpassword123
Estado: ❌ INACTIVO

Usuario: testuser_170444
Contraseña: testpassword123
Estado: ❌ INACTIVO

Usuario: testuser_174126
Contraseña: testpassword123
Estado: ❌ INACTIVO

Usuario: testuser_132347
Contraseña: testpassword123
Estado: ❌ INACTIVO

Usuario: testuser_023355
Contraseña: testpassword123
Estado: ❌ INACTIVO
```

---

## 🎯 CREDENCIALES PARA TESTING

### **Login de Administrador (Acceso Completo)**
```
URL: https://bondholding.preview.emergentagent.com
Usuario: admin
Contraseña: admin123
```

### **Login de Administrador Alternativo**
```
URL: https://bondholding.preview.emergentagent.com
Usuario: superadmin
Contraseña: Panama2025!
```

### **Login de Usuario de Casa de Corretaje**
```
URL: https://bondholding.preview.emergentagent.com
Usuario: testuser
Contraseña: testpassword123
```

---

## 🔧 PERMISOS POR TIPO DE USUARIO

### **👑 ADMINISTRADORES (admin, superadmin)**
- ✅ Crear/editar/eliminar usuarios de casas de corretaje
- ✅ Gestionar valores ISIN/Latinex (crear, editar, eliminar, importar, exportar)
- ✅ Ver todas las tenencias de todos los usuarios
- ✅ Crear administradores adicionales
- ✅ Exportar reportes a Excel
- ✅ Limpiar base de datos
- ✅ Acceso a panel de administración completo

### **👨‍💼 USUARIOS DE CASAS DE CORRETAJE**
- ✅ Registrar nuevas tenencias de bonos
- ✅ Ver sus propias tenencias registradas
- ✅ Buscar valores ISIN/Latinex existentes
- ❌ No pueden gestionar otros usuarios
- ❌ No pueden editar valores ISIN
- ❌ No pueden ver tenencias de otros usuarios

---

## 🚨 NOTAS DE SEGURIDAD

### **Contraseñas Utilizadas:**
- **Administradores**: Contraseñas específicas y seguras
- **Usuarios de prueba**: Todos usan `testpassword123` (solo para testing)

### **Recomendaciones para Producción:**
1. **Cambiar contraseñas por defecto** antes del lanzamiento
2. **Eliminar usuarios de prueba** inactivos
3. **Implementar políticas de contraseñas** más robustas
4. **Activar logs de auditoría** para monitoreo

### **Estados de Usuario:**
- **Activos**: Pueden iniciar sesión y usar el sistema
- **Inactivos**: No pueden iniciar sesión (deshabilitados por admin)

---

## 📊 RESUMEN DE USUARIOS

| Tipo | Activos | Inactivos | Total |
|------|---------|-----------|-------|
| Administradores | 2 | 0 | 2 |
| Usuarios Corretaje | 2 | 7 | 9 |
| **TOTAL** | **4** | **7** | **11** |

---

## 🔐 TESTING RÁPIDO DE CREDENCIALES

### **Verificar Login Admin:**
```bash
curl -X POST https://bondholding.preview.emergentagent.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### **Verificar Login Usuario:**
```bash
curl -X POST https://bondholding.preview.emergentagent.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpassword123"}'
```

---

**Todas las credenciales están listas para uso inmediato en el sistema de bonos de Panamá.**