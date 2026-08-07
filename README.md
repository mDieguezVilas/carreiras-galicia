# carreiras-galicia

Caso de estudio del TFG **"Framework para recopilación e integración de
datos de distintas fuentes y gestión de eventos"**.

Este proyecto implementa un portal de recopilación de **carreras populares y
trails en Galicia**, integrando tres fuentes de datos reales y heterogéneas
(scraping HTML, API REST y CSV manual) bajo una interfaz común.

Usa el [events-framework](https://github.com/mDieguezVilas/events-framework)
como librería externa para recopilar, normalizar, deduplicar, almacenar,
notificar y exponer los eventos a través de una API REST.

---

## Índice

- [Fuentes implementadas](#fuentes-implementadas)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
  - [Opción A: instalación local](#opción-a-instalación-local)
  - [Opción B: Docker Compose](#opción-b-docker-compose)
- [Configuración](#configuración)
  - [config.yaml](#configyaml)
  - [.env](#env)
- [Uso del framework (CLI)](#uso-del-framework-cli)
  - [`framework list-sources`](#framework-list-sources)
  - [`framework update`](#framework-update)
  - [`framework serve-api`](#framework-serve-api)
  - [`framework promote-field`](#framework-promote-field)
- [API REST](#api-rest)
  - [GET /events/](#get-events)
  - [GET /events/{id}](#get-eventsid)
  - [GET /events/schema/{type}](#get-eventsschematype)
  - [GET /docs](#get-docs)
- [Tipo de evento: `race`](#tipo-de-evento-race)
- [Fuentes de datos en detalle](#fuentes-de-datos-en-detalle)
  - [fga (scraping)](#fga-scraping)
  - [carreiras_galegas (API REST)](#carreiras_galegas-api-rest)
  - [manual (CSV)](#manual-csv)
- [Añadir una nueva fuente de datos](#añadir-una-nueva-fuente-de-datos)
- [Deduplicación](#deduplicación)
- [Almacenamiento en PostgreSQL](#almacenamiento-en-postgresql)
- [Notificaciones](#notificaciones)
- [Despliegue con Docker Compose](#despliegue-con-docker-compose)
- [Licencia](#licencia)

---

## Fuentes implementadas

| Fuente                | Tipo          | Descripción                                             |
|-----------------------|---------------|---------------------------------------------------------|
| `fga`                 | Scraping HTML | Federación Galega de Atletismo (atletismo.gal)          |
| `carreiras_galegas`   | API REST      | Portal carreirasgalegas.com                             |
| `manual`              | CSV           | Carreras introducidas manualmente en un fichero local   |

Todas las fuentes producen eventos del tipo `race`, definido en
[`event_types/race.json`](event_types/race.json).

## Estructura del proyecto

```
carreiras-galicia/
├── pyproject.toml              # Dependencias, incluyendo events-framework
├── config.yaml                 # Configuración de fuentes, storage y notificaciones
├── dockerfile                  # Imagen Docker del proyecto
├── docker-compose.yml          # Orquestación de db + api + updater
├── .env                        # Credenciales (no versionado)
├── sources/
│   ├── __init__.py
│   ├── fga_source.py                    # Federación Galega de Atletismo
│   ├── carreriras_galegas_source.py     # carreirasgalegas.com
│   └── manual_csv_source.py             # CSV manual
├── event_types/
│   └── race.json               # JSON Schema del tipo de evento "race"
└── data/
    └── carreiras_manual.csv    # Carreras introducidas manualmente
```

## Requisitos

- **Python** 3.11 o superior
- **Git** (para instalar `events-framework` como dependencia)
- **PostgreSQL** 14 o superior, si se usa el backend `sql` (recomendado)
- **Docker** y **Docker Compose**, si se opta por el despliegue en contenedores

## Instalación

### Opción A: instalación local

```bash
git clone https://github.com/mDieguezVilas/carreiras-galicia.git
cd carreiras-galicia

python -m venv .venv

# Activar el entorno virtual
.venv\Scripts\Activate.ps1     # Windows (PowerShell)
source .venv/bin/activate      # Linux / macOS

pip install -e .
```

Este comando instala `events-framework` automáticamente como dependencia
externa (declarada en `pyproject.toml`), junto con `beautifulsoup4` y
`lxml`, necesarias para el scraping de la fuente `fga`.

Crea la base de datos en PostgreSQL:

```bash
createdb -U postgres carreiras_galicia_db
```

Crea el fichero `.env` en la raíz del proyecto (ver [sección .env](#env)).

### Opción B: Docker Compose

Si no quieres instalar Python ni PostgreSQL localmente, puedes arrancar
todo el sistema con un único comando. Ver [Despliegue con Docker
Compose](#despliegue-con-docker-compose).

## Configuración

### config.yaml

Controla el comportamiento general del sistema: backend de almacenamiento,
fuentes activas y canales de notificación.

```yaml
storage:
  type: sql
  data_dir: data

sources:
  fga:
    enabled: true
    schedule: "0 9 * * *"
  carreiras_galegas:
    enabled: true
    schedule: "0 10 * * *"
  manual:
    enabled: true
    schedule: "0 11 * * *"

notifications:
  telegram:
    enabled: false
    token_env: TELEGRAM_TOKEN
    chat_id_env: TELEGRAM_CHAT_ID
  smtp:
    enabled: false
    summary: false

sources_package: sources
```

Notas:

- `storage.type: sql` usa PostgreSQL. Para pruebas rápidas sin base de
  datos se puede cambiar a `type: csv`, y los eventos se guardarán en
  `data/events.csv`.
- Cada fuente puede activarse/desactivarse cambiando `enabled: true/false`,
  sin tocar código.
- El campo `schedule` documenta la periodicidad prevista de cada fuente en
  formato cron (la ejecución automatizada es responsabilidad del sistema
  externo que invoque `framework update`, por ejemplo una tarea cron o un
  contenedor `updater`).

### .env

Fichero con credenciales sensibles, **no se sube al repositorio**.

```env
DATABASE_URL=postgresql+psycopg://postgres:PASSWORD@localhost/carreiras_galicia_db
TELEGRAM_TOKEN=tu_token
TELEGRAM_CHAT_ID=tu_chat_id
```

| Variable            | Obligatoria                                    | Descripción                               |
|---------------------|------------------------------------------------|-------------------------------------------|
| `DATABASE_URL`      | Solo si `storage.type: sql`                    | Cadena de conexión a PostgreSQL           |
| `TELEGRAM_TOKEN`    | Solo si `notifications.telegram.enabled: true` | Token del bot de Telegram                 |
| `TELEGRAM_CHAT_ID`  | Solo si `notifications.telegram.enabled: true` | ID del chat/canal de destino              |

## Uso del framework (CLI)

Todos los comandos se ejecutan desde la raíz del proyecto, con el entorno
virtual activado (o dentro del contenedor Docker).

### `framework list-sources`

Muestra las fuentes registradas y activas según `config.yaml`.

```bash
framework list-sources
```

Salida de ejemplo:

```
- fga
- carreiras_galegas
- manual
```

### `framework update`

Ejecuta el ciclo completo: descubre las fuentes activas, extrae los
eventos, los valida contra el JSON Schema, calcula su huella SHA-256,
descarta los duplicados, guarda los nuevos y notifica si hay canales de
notificación activos.

```bash
framework update
```

Salida de ejemplo:

```
INFO - fga: HTML obtenido (48213 chars)
INFO - fga: 12 competiciones parseadas
INFO - carreiras_galegas: 4 meses obtenidos
INFO - carreiras_galegas: 27 carreras parseadas
INFO - manual: 3 filas parseadas
INFO - Guardado: IX Carreirado Apóstolo - A Laracha (carreiras_galegas)
INFO - Guardado: XI Carreira Pedestre Concello de Cee Nocturna (carreiras_galegas)
...
Total: 42 | Guardados: 37 | Omitidos: 5
```

Se recomienda automatizar este comando con una tarea cron o un servicio
programado, ya que el framework por sí solo no planifica ejecuciones.

### `framework serve-api`

Arranca el servidor de la API REST en el puerto 8000 por defecto.

```bash
framework serve-api
```

```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Para cambiar host/puerto:

```bash
framework serve-api --host 0.0.0.0 --port 8080
```

### `framework promote-field`

Convierte un campo del JSONB `data` en una columna física indexada, para
mejorar el rendimiento de las consultas más frecuentes. Requiere el
backend `sql`.

```bash
framework promote-field race location
```

El comando solicita confirmación antes de ejecutar la operación. Una vez
confirmado:

```
¿Confirmas la promoción del campo 'location' para el tipo 'race'? [y/N]: y
INFO - Columna 'location' añadida
INFO - Backfill: 37 filas actualizadas
INFO - Índice 'idx_events_location' creado
```

Tras la promoción, las consultas filtradas por `location` usan la columna
física indexada en lugar de examinar el contenido completo del JSONB.

## API REST

Con `framework serve-api` arrancado, la API queda disponible en
`http://localhost:8000`.

| Endpoint                     | Descripción                                    |
|-------------------------------|---------------------------------------------------|
| `GET /events/`                | Lista de eventos con filtros y paginación         |
| `GET /events/{id}`            | Detalle de un evento concreto                     |
| `GET /events/schema/{type}`   | JSON Schema del tipo de evento                    |
| `GET /docs`                   | Documentación interactiva (Swagger UI)            |

### GET /events/

Lista los eventos almacenados, con soporte de filtros por fuente, tipo y
rango de fechas, y paginación.

```bash
# Todos los eventos
curl http://localhost:8000/events/

# Filtrar por fuente
curl "http://localhost:8000/events/?source=fga"

# Filtrar por fuente y limitar resultados
curl "http://localhost:8000/events/?source=carreiras_galegas&limit=5"

# Filtrar por tipo de evento
curl "http://localhost:8000/events/?type=race"

# Combinar filtro con paginación
curl "http://localhost:8000/events/?source=manual&limit=10&offset=0"
```

Respuesta de ejemplo:

```json
[
  {
    "id": 1,
    "type_": "race",
    "name": "IX CARREIRADO APÓSTOLO - A LARACHA",
    "url": "https://www.carreirasgalegas.com/competicion/ix-carreirado-apstolo-a-laracha",
    "source": "carreiras_galegas",
    "event_date": "2026-07-16T19:49:28.251887",
    "data": {
      "location": "A Laracha",
      "date_text": "2026-07-18"
    }
  },
  {
    "id": 2,
    "type_": "race",
    "name": "Trail Illas Cíes",
    "url": "https://cies.gal/trail",
    "source": "manual",
    "event_date": "2026-07-16T19:50:01.882341",
    "data": {
      "location": "Vigo",
      "distance": "15K",
      "date_text": "2025-08-23"
    }
  }
]
```

### GET /events/{id}

Devuelve el detalle de un único evento por su identificador.

```bash
curl http://localhost:8000/events/1
```

```json
{
  "id": 1,
  "type_": "race",
  "name": "IX CARREIRADO APÓSTOLO - A LARACHA",
  "url": "https://www.carreirasgalegas.com/competicion/ix-carreirado-apstolo-a-laracha",
  "source": "carreiras_galegas",
  "event_date": "2026-07-16T19:49:28.251887",
  "data": {
    "location": "A Laracha",
    "date_text": "2026-07-18"
  }
}
```

Si el identificador no existe, se devuelve un error `404`:

```bash
curl -i http://localhost:8000/events/99999
```

```
HTTP/1.1 404 Not Found
{"detail": "Event not found"}
```

### GET /events/schema/{type}

Devuelve el JSON Schema empleado para validar un tipo de evento concreto.

```bash
curl http://localhost:8000/events/schema/race
```

```json
{
  "type": "object",
  "properties": {
    "location": {"type": "string"},
    "distance": {"type": "string"},
    "registration_url": {"type": "string"}
  },
  "required": ["location"]
}
```

### GET /docs

Abre en el navegador `http://localhost:8000/docs` para acceder a la
documentación interactiva generada automáticamente por FastAPI (Swagger
UI), desde donde se pueden probar todos los endpoints sin necesidad de
`curl` ni Postman.

## Tipo de evento: `race`

Definido en [`event_types/race.json`](event_types/race.json):

```json
{
  "type_id": "race",
  "description": "Carreira popular ou trail en Galicia",
  "json_schema": {
    "type": "object",
    "properties": {
      "location": {"type": "string"},
      "distance": {"type": "string"},
      "registration_url": {"type": "string"}
    },
    "required": ["location"]
  }
}
```

Cualquier evento producido por las fuentes con `type_="race"` debe cumplir
este esquema en su campo `data`; en caso contrario, el evento se descarta
durante `framework update` y se registra un aviso en el log.

## Fuentes de datos en detalle

### fga (scraping)

Fichero: [`sources/fga_source.py`](sources/fga_source.py)

Descarga el HTML de `https://atletismo.gal/competicions/` con `httpx` y
extrae cada competición mediante `BeautifulSoup` (parser `lxml`), leyendo
el nombre, la URL, la fecha en texto, el tipo de prueba y la localización
de cada artículo `article.competition`.

```python
@event_source(source_id="fga", enabled=True)
class FGASource(EventSource):
    def fetch(self):
        ...  # descarga el HTML
    def parse(self, raw):
        ...  # devuelve una lista de EventPayload
```

Ejemplo de evento generado por esta fuente:

```json
{
  "type_": "race",
  "name": "Campionato Galego de Cross",
  "url": "https://atletismo.gal/competicion/campionato-galego-de-cross/",
  "source": "fga",
  "data": {
    "location": "Ourense",
    "event_type": "Cross",
    "date_text": "18/01/2026"
  }
}
```

### carreiras_galegas (API REST)

Fichero: [`sources/carreriras_galegas_source.py`](sources/carreriras_galegas_source.py)

Consulta la API interna de `carreirasgalegas.com`
(`https://api.web.carreirasgalegas.com/competitions-by-month`), que
devuelve un listado de meses, cada uno con una lista de competiciones. Se
filtran solo las competiciones con el estado `"published"` y se genera la
URL final normalizando el nombre del evento (minúsculas, sin acentos,
espacios sustituidos por guiones).

```python
@event_source(source_id="carreiras_galegas", enabled=True)
class CarreirasGalegasSource(EventSource):
    def fetch(self):
        ...  # GET a la API de carreirasgalegas.com
    def parse(self, raw):
        ...  # filtra publicadas y genera EventPayload
```

Ejemplo de evento generado por esta fuente:

```json
{
  "type_": "race",
  "name": "V CARREIRA SOLIDARIA MÓVETE POLA DIABETES",
  "url": "https://www.carreirasgalegas.com/competicion/v-carreira-solidaria-mvete-pola-diabetes",
  "source": "carreiras_galegas",
  "data": {
    "location": "A Pobra do Caramiñal",
    "date_text": "2026-07-24"
  }
}
```

### manual (CSV)

Fichero: [`sources/manual_csv_source.py`](sources/manual_csv_source.py)
Datos: [`data/carreiras_manual.csv`](data/carreiras_manual.csv)

Lee un fichero CSV local con carreras introducidas manualmente, útil para
añadir eventos que no estén disponibles en las otras dos fuentes.

```csv
name,url,location,distance,event_date
Carreira Popular Cangas,https://cangas.gal/carreira,Cangas do Morrazo,5K,2025-07-12
Trail Illas Cíes,https://cies.gal/trail,Vigo,15K,2025-08-23
10K Ponteareas,https://ponteareas.gal/10k,Ponteareas,10K,2025-10-05
```

Para añadir una nueva carrera manualmente, basta con añadir una fila a
este fichero y volver a ejecutar `framework update`; el nuevo evento se
detectará y almacenará en el siguiente ciclo.

## Añadir una nueva fuente de datos

1. Crea un fichero nuevo en `sources/`, por ejemplo `sources/nueva_fuente.py`.
2. Implementa una clase que herede de `EventSource` con `fetch()` y
   `parse()`, decorada con `@event_source`:

   ```python
   from framework.models import EventPayload
   from framework.sources.base import EventSource, event_source

   @event_source(source_id="nueva_fuente", enabled=True)
   class NuevaFuenteSource(EventSource):
       def fetch(self):
           # devuelve los datos crudos (HTTP, HTML, fichero...)
           return [...]

       def parse(self, raw):
           return [
               EventPayload(
                   type_="race",
                   name=item["name"],
                   url=item["url"],
                   source=self.source_id,
                   data={"location": item["location"]},
               )
               for item in raw
           ]
   ```

3. Añade la fuente en `config.yaml`, bajo `sources`, con el mismo
   identificador indicado en `source_id`:

   ```yaml
   sources:
     nueva_fuente:
       enabled: true
       schedule: "0 12 * * *"
   ```

4. Verifica que se detecta correctamente:

   ```bash
   framework list-sources
   ```

5. Ejecuta el ciclo de actualización para probarla:

   ```bash
   framework update
   ```

No es necesario modificar ningún otro fichero del proyecto ni del
framework para añadir una nueva fuente.

## Deduplicación

El framework evita almacenar eventos repetidos calculando una huella
digital **SHA-256** para cada evento a partir de `name`, `source` y
`location`. Si la huella ya existe en el almacenamiento, el evento se
descarta y se contabiliza como *omitido* en el resumen de `framework
update`, sin llegar a guardarse de nuevo.

Esto permite ejecutar `framework update` repetidas veces (por ejemplo,
cada día) sin riesgo de duplicar eventos ya conocidos entre ejecuciones.

## Almacenamiento en PostgreSQL

Con la configuración `storage.type: sql`, los eventos se guardan en la
tabla `events`, creada automáticamente al arrancar el framework si no
existe:

| Columna      | Tipo      | Descripción                              |
|--------------|-----------|------------------------------------------|
| `id`         | Integer   | Identificador único, autoincremental     |
| `type_`      | String    | Tipo de evento (`race`)                  |
| `name`       | String    | Nombre del evento                        |
| `url`        | String    | URL de referencia                        |
| `source`     | String    | Fuente de origen                         |
| `event_date` | Timestamp | Fecha de extracción                      |
| `data`       | JSONB     | Campos específicos (location, distance, etc.) |

Las huellas de deduplicación se almacenan en una tabla separada
`fingerprints`, con una restricción de unicidad a nivel de base de datos.

Consulta directa de ejemplo en `psql`:

```sql
SELECT name, source, data->>'location' AS location
FROM events
WHERE type_ = 'race'
ORDER BY event_date DESC
LIMIT 10;
```

## Notificaciones

Se activan en `config.yaml` (bloque `notifications`) y se configuran las
credenciales en `.env`. Por defecto vienen desactivadas en este proyecto.

Para activar Telegram:

```yaml
notifications:
  telegram:
    enabled: true
    token_env: TELEGRAM_TOKEN
    chat_id_env: TELEGRAM_CHAT_ID
```

```env
TELEGRAM_TOKEN=123456789:AAEjemplo_DelTokenDelBotDeTelegram
TELEGRAM_CHAT_ID=-1001234567890
```

Al ejecutar `framework update`, si se detectan eventos nuevos, se enviará
un mensaje por Telegram por cada uno de ellos, con nombre, fecha,
localización (si está disponible) y la URL de referencia.

## Despliegue con Docker Compose

El proyecto incluye un `docker-compose.yml` con tres servicios:

- `db`: instancia de PostgreSQL 16.
- `api`: arranca `framework serve-api` en el puerto 8000.
- `updater`: ejecuta `framework update` bajo demanda (perfil `tools`, no
  se arranca por defecto).

Arrancar la base de datos y la API:

```bash
docker compose up -d db api
```

La API quedará disponible en `http://localhost:8000`.

Ejecutar manualmente un ciclo de actualización dentro del contenedor:

```bash
docker compose --profile tools run --rm updater
```

Ver los logs de la API en tiempo real:

```bash
docker compose logs -f api
```

Parar y eliminar los contenedores (manteniendo los datos en `pgdata`):

```bash
docker compose down
```

Parar y eliminar también el volumen de datos de la base de datos:

```bash
docker compose down -v
```

Si se usa Telegram, exporta las variables antes de arrancar los
contenedores (o defínelas en un fichero `.env` en la raíz, que Docker
Compose lee automáticamente):

```env
TELEGRAM_TOKEN=tu_token
TELEGRAM_CHAT_ID=tu_chat_id
```


## Licencia

Proyecto desarrollado como caso de estudio del Trabajo de Fin de Grado
*"Framework para recopilación e integración de datos de distintas fuentes
y gestión de eventos"*, Escola Superior de Enxeñaría Informática,
Universidade de Vigo.