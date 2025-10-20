# Guía de Importación de Excel - Valores Registrados

## Funcionalidad Implementada ✅

Se ha agregado la funcionalidad de **importación masiva de valores desde archivos Excel** al Sistema de Registro de Bonos de Panamá.

## Ubicación de la Funcionalidad

**Panel de Administración → Pestaña "Valores ISIN"**

- **Botón "Seleccionar Archivo"**: Para elegir el archivo Excel
- **Botón "Importar Excel"**: Aparece después de seleccionar un archivo válido

## Formato Requerido del Excel

El archivo Excel debe contener las siguientes columnas **en este orden exacto**:

| Columna | Descripción | Requerido | Ejemplo |
|---------|-------------|-----------|---------|
| **Código ISIN** | Código internacional del valor | Opcional* | US698299BK05 |
| **Código Latinex** | Código regional del valor | Opcional* | RPMA033620231A |
| **Descripción del Valor** | Nombre descriptivo del bono | **Sí** | República de Panamá - Bono Serie A |
| **Cupón** | Tasa de interés | **Sí** | 8.500% |
| **Fecha de Emisión** | Fecha de emisión del bono | **Sí** | 2023-01-15 |
| **Fecha de Vencimiento** | Fecha de vencimiento | **Sí** | 2033-01-15 |

*Al menos un código (ISIN o Latinex) es requerido

## Instrucciones de Uso

### 1. Preparar el Archivo Excel
- Use el formato de exportación como referencia
- Nombre recomendado para la hoja: "Valores_ISIN"
- Formatos aceptados: `.xlsx`, `.xls`

### 2. Proceso de Importación
1. Iniciar sesión como administrador
2. Ir a **Panel de Administración** → **Valores ISIN**
3. Hacer clic en **"Seleccionar Archivo"**
4. Elegir el archivo Excel preparado
5. Hacer clic en **"Importar Excel"**
6. Revisar el mensaje de confirmación

### 3. Resultados de la Importación
El sistema mostrará:
- ✅ **Valores importados exitosamente**
- ⚠️ **Errores encontrados** (si los hay)
- 📊 **Resumen estadístico**

## Validaciones Implementadas

### ✅ Validaciones de Formato
- **Tipo de archivo**: Solo acepta .xlsx y .xls
- **Estructura**: Verifica columnas requeridas
- **Datos mínimos**: Al menos ISIN o Latinex requerido

### ✅ Validaciones de Negocio
- **Duplicados**: Previene valores con códigos existentes
- **Campos requeridos**: Valida descripción, cupón y fechas
- **Integridad**: Verifica formato de datos

### ✅ Manejo de Errores
- **Reporte detallado**: Lista errores por fila
- **Importación parcial**: Importa valores válidos aunque otros fallen
- **Logs de depuración**: Información técnica en consola

## Ejemplo de Archivo de Prueba

```
Código ISIN    | Código Latinex      | Descripción del Valor              | Cupón   | Fecha de Emisión | Fecha de Vencimiento
US698299BK05   | RPMA033620231A     | República de Panamá - Bono Serie A | 8.500%  | 2023-01-15      | 2033-01-15
US698299CK04   | RPMA033620241B     | República de Panamá - Bono Serie B | 7.750%  | 2024-02-20      | 2034-02-20
               | RPME093750429C     | República de Panamá - Bono Local   | 9.375%  | 2024-04-01      | 2029-04-01
US698299DK03   |                    | República de Panamá - Bono Int'l   | 6.250%  | 2024-06-15      | 2031-06-15
```

## API Endpoint

**POST** `/api/admin/import/excel`
- **Autenticación**: Token JWT de administrador
- **Content-Type**: `multipart/form-data`
- **Parámetro**: `file` (archivo Excel)

### Respuesta Ejemplo:
```json
{
  "message": "Importación completada: 4 valores importados",
  "imported_count": 4,
  "total_errors": 0,
  "errors": []
}
```

## Beneficios de la Funcionalidad

✅ **Importación masiva**: Cargue múltiples valores simultáneamente
✅ **Validación robusta**: Previene datos inconsistentes
✅ **Manejo de errores**: Información clara sobre problemas
✅ **Integración completa**: Actualiza automáticamente la base consolidada
✅ **Formato estándar**: Compatible con exportaciones del sistema

## Usuarios Autorizados

Solo **administradores** pueden usar esta funcionalidad:
- `admin` / `admin123` (administrador por defecto)
- `superadmin` / `Panama2025!` (super administrador)

## Notas Técnicas

- **Rendimiento**: Optimizado para archivos grandes
- **Transaccional**: Operación atómica por valor
- **Consolidación**: Actualiza automáticamente la base de datos maestra
- **Logs**: Registro completo de operaciones de importación