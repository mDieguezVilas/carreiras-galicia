# CarreirasGalicia

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