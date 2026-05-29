# carreiras-galicia

Caso de estudo do TFG: portal de carreiras populares e trails en Galicia.

Usa o [events-framework](https://github.com/mDieguezVilas/events-framework)
como librería externa para recompilar, normalizar e centralizar eventos
deportivos procedentes de múltiples fontes.

## Fontes implementadas

| Fonte      | Tipo     | Descripción                                |
|------------|----------|--------------------------------------------|
| fga        | Scraping | Federación Galega de Atletismo             |
| kronotime  | API REST | Plataforma de inscricións Kronotime        |
| manual     | CSV      | Carreiras introducidas manualmente         |

## Instalación

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
pip install -e .
```

Crea a base de datos en Postgres:

```bash
createdb -U postgres carreiras_galicia_db
```

Crea o ficheiro `.env`:

```.env
DATABASE_URL=postgresql+psycopg://postgres:PASSWORD@localhost/carreiras_galicia_db
TELEGRAM_TOKEN=tu_token
TELEGRAM_CHAT_ID=tu_chat_id
```
## Uso

```bash
# Ver as fontes dispoñibles
framework list-sources

# Executar a recompilación
framework update

# Arrancar a API REST
framework serve-api
```

## API REST

Con `framework serve-api` arrancado, os endpoints dispoñibles son:

| Endpoint                     | Descripción                        |
|------------------------------|------------------------------------|
| GET /events/                 | Lista con filtros e paginación     |
| GET /events/{id}             | Detalle dun evento                 |
| GET /events/schema/{type}    | JSON Schema do tipo de evento      |
| GET /docs                    | Documentación interactiva          |

Exemplos de filtros:

http://localhost:8000/events/?source=fga
http://localhost:8000/events/?source=kronotime&limit=5
http://localhost:8000/events/1


## Estrutura

carreiras-galicia/
├── pyproject.toml
├── config.yaml
├── .env.example
├── sources/
│   ├── fga_source.py          # Federación Galega de Atletismo
│   ├── kronotime_source.py    # Kronotime
│   └── manual_csv_source.py   # CSV manual
├── event_types/
│   └── race.json              # JSON Schema de carreiras
└── data/
└── carreiras_manual.csv       # Carreiras introducidas manualmente

## Deduplicación

O framework evita duplicados dentro da mesma fonte mediante un
fingerprint SHA-256 calculado a partir de `name`, `source` e `location`.