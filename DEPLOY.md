# Guía de Despliegue en Render

## Microservicio Simulador de Multicrédito Banco Guayaquil

Este servicio scrape el simulador de crédito de Banco Guayaquil y lo expone como API REST.

## Despliegue en Render

### Paso 1: Preparar el repositorio

El código ya está listo para desplegar. Asegúrate de tener todos estos archivos:

- `simulador_service.py` - Servicio principal
- `requirements.txt` - Dependencias de Python
- `render.yaml` - Configuración de Render
- `.gitignore` - Archivos a ignorar
- `start.sh` - Script de inicio

### Paso 2: Crear repositorio en GitHub

1. Crea un nuevo repositorio en GitHub (puede ser privado)
2. Sube el código:

```bash
git add .
git commit -m "Initial commit: Simulador BG microservice"
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

### Paso 3: Conectar con Render

1. Ve a https://render.com
2. Conecta tu cuenta de GitHub
3. Crea un nuevo "Web Service"
4. Selecciona el repositorio que acabas de crear
5. Render detectará automáticamente el `render.yaml`

### Paso 4: Configurar Variables de Entorno (Opcional)

En el dashboard de Render, puedes configurar:

- `ENVIRONMENT=production` (ya configurado por defecto)
- `HEADLESS=true` (ya configurado para producción)

### Paso 5: Desplegar

Render empezará a construir y desplegar automáticamente. El proceso toma ~5-10 minutos.

## Endpoints Disponibles

Una vez desplegado, el servicio estará disponible en: `https://simulador-bg.onrender.com`

### POST /simular
Ejecuta una simulación de crédito.

**Request:**
```json
{
  "monto": 10000,
  "meses": 24,
  "amortizacion": "aleman",
  "correo": "test@example.com"
}
```

**Response:**
```json
{
  "monto": 10000.0,
  "meses": 24,
  "amortizacion": "Alemán",
  "cuota_mensual": "1005.47",
  "capital": "$10,000.00",
  "impuesto_solca": "$50.00",
  "total_interes": "$848.01",
  "total_seguros": "$338.15",
  "total_pagar": "$11,186.16",
  "tabla_amortizacion": [...]
}
```

### GET /resultado
Obtiene los datos de la última simulación ejecutada.

### GET /health
Verifica que el servicio esté funcionando.

## Notas Importantes

1. **Plan Free de Render**: El servicio se "duerme" después de 15 minutos de inactividad. La primera petición después del sleep tomará ~30 segundos.

2. **Tiempos de respuesta**: Cada simulación toma ~40-60 segundos debido a:
   - Navegación al sitio web
   - Delays aleatorios para evitar detección como bot
   - Extracción de datos

3. **Anti-bot**: El servicio implementa:
   - User-agent realista
   - Delays aleatorios (5-8s inicial, 1.5-3.5s entre acciones)
   - Scripts anti-detección JavaScript
   - Cierre automático de popups de cookies

4. **Headless mode**: En producción corre en modo headless (sin ventana visible).

## Troubleshooting

Si hay errores en el despliegue:

1. Revisa los logs en el dashboard de Render
2. Verifica que Playwright se instaló correctamente: `playwright install chromium`
3. Asegúrate que las dependencias del sistema se instalaron: `playwright install-deps chromium`

## Próximas Mejoras

- Soporte para Tor (rotación de IPs)
- Cache de resultados
- Rate limiting
- Webhooks para notificaciones
