# Simulador de Crédito - Banco Guayaquil
## Automatización RPA con Power Automate Desktop

---

## 📋 Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Arquitectura de la Solución](#arquitectura-de-la-solución)
- [Componentes](#componentes)
- [Flujo Implementado](#flujo-implementado)
- [Variables de Configuración](#variables-de-configuración)
- [Endpoints API](#endpoints-api)
- [Instalación y Configuración](#instalación-y-configuración)
- [Uso](#uso)
- [Mantenimiento](#mantenimiento)

---

## 📝 Descripción General

Solución RPA que automatiza la generación de simulaciones de crédito del Banco Guayaquil, integrando un microservicio web con Power Automate Desktop para generar archivos PDF y Excel con tablas de amortización, almacenarlos en OneDrive y enviarlos por correo electrónico.

### Objetivos Cumplidos

✅ Generación automatizada de PDF y Excel con tabla de amortización
✅ Integración con API REST desplegada en Render
✅ Almacenamiento en OneDrive for Business
✅ Envío de correos con adjuntos formateados
✅ Sistema de logging para auditoría
✅ Validación de entradas de usuario

---

## 🏗️ Arquitectura de la Solución

```
┌─────────────────────────────────────────────────────────────┐
│                    POWER AUTOMATE DESKTOP                    │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. INICIALIZACIÓN                                      │ │
│  │    - Trigger Manual                                    │ │
│  │    - Inicialización de 12 Variables Globales          │ │
│  │    - Logging de inicio de ejecución                   │ │
│  └────────────────────────────────────────────────────────┘ │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 2. VALIDACIÓN DE ENTRADAS                             │ │
│  │    - Condición: ValidarEntradas                       │ │
│  │    - Validación de monto, meses, tipo amortización    │ │
│  └────────────────────────────────────────────────────────┘ │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 3. GENERACIÓN DE ARCHIVOS (Rama True)                 │ │
│  │    - HTTP POST: /generar-pdf                          │ │
│  │    - HTTP POST: /generar-excel                        │ │
│  │    - Validación de respuestas HTTP 200                │ │
│  │    - Logging de generación exitosa                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 4. ALMACENAMIENTO                                      │ │
│  │    - OneDrive: Guardar PDF                            │ │
│  │    - OneDrive: Guardar Excel                          │ │
│  │    - Logging de archivos guardados                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 5. NOTIFICACIÓN                                        │ │
│  │    - Send Email V2 con adjuntos PDF/Excel             │ │
│  │    - Cuerpo HTML formateado profesional               │ │
│  │    - Logging de email enviado                         │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                          ↓
                  ┌───────────────┐
                  │  MICROSERVICIO │
                  │   (Render)     │
                  │                │
                  │  Playwright    │
                  │  + Chromium    │
                  │  + Python      │
                  └───────────────┘
                          ↓
            ┌─────────────────────────┐
            │ Banco Guayaquil Website │
            │  (Simulador Crédito)    │
            └─────────────────────────┘
```

---

## 🔧 Componentes

### 1. Microservicio Python (Backend)
- **Ubicación**: Render Cloud
- **Framework**: FastAPI + Playwright
- **Funcionalidad**: Web scraping del simulador oficial de Banco Guayaquil
- **Endpoints**: `/generar-pdf`, `/generar-excel`

### 2. Power Automate Desktop (Orquestador)
- **Tipo**: Flujo de nube (Cloud Flow)
- **Trigger**: Manual
- **Conectores**: HTTP, OneDrive for Business, Office 365 Outlook

---

## 🔄 Flujo Implementado

### Paso 1: Inicialización de Variables

| Variable | Tipo | Valor por Defecto | Descripción |
|----------|------|-------------------|-------------|
| `var_URL_API_Base` | String | URL de Render | Endpoint base del microservicio |
| `var_Timeout_HTTP_Segundos` | Integer | 180 | Timeout para llamadas HTTP |
| `var_Reintentos_Max` | Integer | 2 | Número máximo de reintentos |
| `var_Path_OneDrive` | String | `/Simulaciones` | Carpeta de OneDrive |
| `var_Email_Admin` | String | admin@empresa.com | Email de notificaciones |
| `var_Timestamp_Ejecucion` | String | `formatDateTime(utcNow())` | Timestamp de ejecución |
| `var_ID_Ejecucion` | String | `guid()` | ID único de ejecución |
| `var_Log_Mensajes` | Array | `[]` | Array de logs |
| `var_Input_Monto` | Float | (Usuario) | Monto del crédito |
| `var_Input_Meses` | Integer | (Usuario) | Plazo en meses |
| `var_Input_Amortizacion` | String | (Usuario) | "frances" o "aleman" |
| `var_Input_Correo` | String | (Usuario) | Email destino |

### Paso 2: Validación de Entradas

**Condición**: `ValidarEntradas`
```javascript
and(
  and(
    greaterOrEquals(variables('var_Input_Monto'), 500),
    lessOrEquals(variables('var_Input_Monto'), 100000)
  ),
  and(
    greaterOrEquals(variables('var_Input_Meses'), 6),
    lessOrEquals(variables('var_Input_Meses'), 360)
  ),
  or(
    equals(toLower(variables('var_Input_Amortizacion')), 'frances'),
    equals(toLower(variables('var_Input_Amortizacion')), 'aleman')
  )
)
```

### Paso 3: Generación de Archivos

#### HTTP GenerarPDF
```http
POST {var_URL_API_Base}/generar-pdf
Content-Type: application/json

{
  "monto": @{variables('var_Input_Monto')},
  "meses": @{variables('var_Input_Meses')},
  "amortizacion": "@{variables('var_Input_Amortizacion')}",
  "correo": "@{variables('var_Input_Correo')}"
}
```

#### HTTP GenerarExcel
```http
POST {var_URL_API_Base}/generar-excel
Content-Type: application/json

{
  "monto": @{variables('var_Input_Monto')},
  "meses": @{variables('var_Input_Meses')},
  "amortizacion": "@{variables('var_Input_Amortizacion')}",
  "correo": "@{variables('var_Input_Correo')}"
}
```

### Paso 4: Validación de Respuestas

**Condición**: `ValidarRespuestaPDF`
```javascript
equals(outputs('HTTP_GenerarPDF')?['statusCode'], 200)
```

### Paso 5: Almacenamiento en OneDrive

**Acción**: `OneDrive_GuardarPDF`
- Ruta: `@{variables('var_Path_OneDrive')}`
- Nombre: `Simulacion_@{variables('var_Input_Correo')}_@{variables('var_Timestamp_Ejecucion')}.pdf`
- Contenido: `@{body('HTTP_GenerarPDF')}`

**Acción**: `OneDrive_GuardarExcel`
- Ruta: `@{variables('var_Path_OneDrive')}`
- Nombre: `Simulacion_@{variables('var_Input_Correo')}_@{variables('var_Timestamp_Ejecucion')}.xlsx`
- Contenido: `@{body('HTTP_GenerarExcel')}`

### Paso 6: Envío de Email

**Acción**: `Send an email (V2)`
- **Para**: `@{variables('var_Input_Correo')}`
- **Asunto**: `Simulación de Crédito - $@{variables('var_Input_Monto')} USD`
- **Cuerpo**: HTML formateado con tabla de detalles
- **Adjuntos**: PDF y Excel generados

---

## 🔌 Endpoints API

### Base URL
```
https://[tu-servicio].onrender.com
```

### POST /generar-pdf

Genera archivo PDF con tabla de amortización completa.

**Request Body**:
```json
{
  "monto": 5000,
  "meses": 24,
  "amortizacion": "frances",
  "correo": "cliente@ejemplo.com"
}
```

**Response**:
- Content-Type: `application/pdf`
- Status: 200 OK

### POST /generar-excel

Genera archivo Excel editable con tabla de amortización.

**Request Body**:
```json
{
  "monto": 5000,
  "meses": 24,
  "amortizacion": "aleman",
  "correo": "cliente@ejemplo.com"
}
```

**Response**:
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Status: 200 OK

### GET /health

Verifica estado del servicio.

**Response**:
```json
{
  "status": "healthy"
}
```

---

## ⚙️ Instalación y Configuración

### Requisitos Previos

- Power Automate Desktop instalado
- Cuenta de OneDrive for Business
- Cuenta de Office 365 (Outlook)
- Microservicio desplegado en Render

### Configuración del Flujo

1. **Importar flujo en Power Automate**
   - Archivo: `[nombre-del-flujo].zip`

2. **Actualizar variables**:
   ```
   var_URL_API_Base → URL de tu servicio en Render
   var_Path_OneDrive → Ruta de tu OneDrive
   var_Email_Admin → Tu email administrativo
   ```

3. **Configurar conexiones**:
   - OneDrive for Business
   - Office 365 Outlook

4. **Variables de entorno en Render**:
   ```bash
   ENVIRONMENT=production
   HEADLESS=true
   USE_PROXY_LIST=false
   ```

---

## 🚀 Uso

### Ejecución Manual

1. Abrir Power Automate Desktop
2. Seleccionar flujo "Simulador BG"
3. Click en "Run"
4. Ingresar parámetros:
   - Monto: 500 - 100000
   - Meses: 6, 12, 24, 36, 48, 60
   - Amortización: "frances" o "aleman"
   - Correo: email válido

### Salidas Generadas

```
OneDrive/Simulaciones/
├── Simulacion_cliente@ejemplo.com_2026-06-22_140530.pdf
└── Simulacion_cliente@ejemplo.com_2026-06-22_140530.xlsx
```

### Ejemplo de Email Enviado

**Asunto**: Simulación de Crédito - $5000 USD

**Adjuntos**:
- PDF: Tabla de amortización (formato imprimible)
- Excel: Datos editables para análisis

---

## 🛠️ Mantenimiento

### Logs de Ejecución

Los logs se almacenan en la variable `var_Log_Mensajes` con formato:

```json
{
  "timestamp": "2026-06-22T14:05:30Z",
  "nivel": "INFO",
  "capa": "Orquestación",
  "mensaje": "Archivos generados exitosamente",
  "idEjecucion": "abc123-def456"
}
```

### Monitoreo

- **Historial de ejecuciones**: Power Automate Portal
- **Logs del microservicio**: Render Dashboard
- **Errores HTTP**: Revisar respuestas en logs

### Mejoras Futuras

- [ ] Manejo de errores con Scope y notificación al admin
- [ ] Guardar logs en SharePoint
- [ ] Implementar reintentos con backoff exponencial
- [ ] Dashboard de métricas en Power BI
- [ ] Validación avanzada de inputs

---

## 📊 Arquitectura del Microservicio

### Stack Tecnológico

- **Lenguaje**: Python 3.11+
- **Framework**: FastAPI
- **Automatización**: Playwright + Chromium
- **Generación PDF**: ReportLab
- **Generación Excel**: OpenPyXL
- **Deployment**: Render (Container)

### Características

- ✅ Web scraping con Playwright Stealth
- ✅ Manejo de sliders con `.fill()` para React
- ✅ Extracción de tasa de interés nominal
- ✅ Scroll inteligente para cargar todas las filas (hasta 60 meses)
- ✅ Delays humanizados anti-detección
- ✅ Rotación de User-Agents
- ✅ Soporte para proxies (opcional)

---

## 📄 Licencia

Este proyecto fue desarrollado como prueba técnica para Binaria.

---

## 👤 Autor

**Carlos Israel Jiménez**
Fecha: Junio 2026
Versión: 1.0.0

---

## 📞 Soporte

Para dudas o problemas:
- Revisar logs en Power Automate Portal
- Verificar estado del servicio en Render
- Consultar documentación de Playwright

---

**Última actualización**: 22 de junio de 2026
