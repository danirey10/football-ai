# ⚽ Football AI - Scouting Dashboard & RAE Engine

> **Plataforma Integral de Inteligencia Deportiva, Scouting Avanzado y Detección del Efecto de la Edad Relativa (RAE)**  
> *Diseñada bajo arquitectura de microservicios full-stack con FastAPI (Python 3.11), Angular 17+ reactivo, MongoDB 7.0 y contenedores Docker.*

---

## 📋 Tabla de Contenidos
- [1. Descripción y Visión del Proyecto](#1-descripción-y-visión-del-proyecto)
- [2. Fundamento Analítico: El Efecto de la Edad Relativa (RAE)](#2-fundamento-analítico-el-efecto-de-la-edad-relativa-rae)
- [3. Arquitectura del Sistema y Stack Tecnológico](#3-arquitectura-del-sistema-y-stack-tecnológico)
  - [Diagrama de Arquitectura](#diagrama-de-arquitectura)
  - [Backend: FastAPI & Motor Asíncrono](#backend-fastapi--motor-asíncrono)
  - [Frontend: Angular 17+ Moderno (Signals & Standalone)](#frontend-angular-17-moderno-signals--standalone)
  - [Persistencia: MongoDB 7.0 & Agregaciones](#persistencia-mongodb-70--agregaciones)
  - [Pipeline ETL de Ingesta Masiva de Datos](#pipeline-etl-de-ingesta-masiva-de-datos)
- [4. Estructura del Repositorio](#4-estructura-del-repositorio)
- [5. Guía de Inicio Rápido (Despliegue con Docker)](#5-guía-de-inicio-rápido-despliegue-con-docker)
  - [Requisitos Previos](#requisitos-previos)
  - [Paso a Paso: Del Clon de GitHub a la Producción Local](#paso-a-paso-del-clon-de-github-a-la-producción-local)
- [6. Guía de Desarrollo Local (Sin Docker)](#6-guía-de-desarrollo-local-sin-docker)
  - [Arranque del Backend](#arranque-del-backend)
  - [Arranque del Frontend](#arranque-del-frontend)
- [7. Catálogo de la API REST](#7-catálogo-de-la-api-rest)
- [8. Batería de Pruebas y Control de Calidad](#8-batería-de-pruebas-y-control-de-calidad)
- [9. Matriz de Variables de Entorno](#9-matriz-de-variables-de-entorno)
- [10. Preguntas Frecuentes y Solución de Problemas (Troubleshooting)](#10-preguntas-frecuentes-y-solución-de-problemas-troubleshooting)
- [11. Licencia](#11-licencia)

---

## 1. Descripción y Visión del Proyecto

**Football AI** es una solución tecnológica avanzada de inteligencia deportiva concebida para directores de cantera, secretarías técnicas, analistas de rendimiento y ojeadores (*scouts*). 

La plataforma aborda dos grandes desafíos del fútbol moderno:
1. **Detección y Corrección del Sesgo Biológico (RAE)**: Identificación cuantitativa de anomalías cronológicas en la captación de talento mediante el análisis estadístico de fechas de nacimiento agrupadas por trimestres (Q1 a Q4).
2. **Scouting Multidimensional Normalizado (0-99)**: Motor de búsqueda y evaluación de futbolistas con atributos técnicos y físicos basados en los estándares de simulación deportiva internacional (*Pace, Shooting, Passing, Dribbling, Defending, Physicality* y valoración global *Overall*), representados en gráficos interactivos de radar frente a la media de su demarcación táctica.

El sistema opera sobre un censo real de **más de 28.000 futbolistas profesionales en activo** de las principales competiciones mundiales (LaLiga, Premier League, Serie A, Bundesliga, Ligue 1, Liga Portugal, etc.).

---

## 2. Fundamento Analítico: El Efecto de la Edad Relativa (RAE)

El **Efecto de la Edad Relativa (*Relative Age Effect* - RAE)** es un sesgo sistemático ampliamente documentado en el fútbol formativo. Debido al criterio de corte por año natural (del 1 de enero al 31 de diciembre), los futbolistas nacidos en los primeros meses del año disponen de una ventaja de desarrollo biológico, muscular y cognitivo de hasta 11 meses respecto a los nacidos a final de año.

```
                    AÑO DE NACIMIENTO COMPETITIVO
┌───────────────────────┬───────────────────────┬───────────────────────┬───────────────────────┐
│     Q1 (Ene - Mar)    │     Q2 (Abr - Jun)    │     Q3 (Jul - Sep)    │     Q4 (Oct - Dic)    │
│  Desarrollo avanzado  │  Desarrollo medio-alto│  Desarrollo medio-bajo│   Maduración tardía   │
└───────────────────────┴───────────────────────┴───────────────────────┴───────────────────────┘
  ▲ Sobrerrepresentación (>30-40%)                       Subestimación de talento (<15-20%) ▼
```

### Impacto en la Detección de Talento:
- **Sobrerrepresentación de Q1 (típicamente >30-40%)**: Mayor probabilidad de ser seleccionados por su ventaja física y envergadura temporal.
- **Abandono o Descarte en Q4 (típicamente <15-20%)**: Pérdida de talento técnico diferencial debido a una menor madurez física temporal.

### Motor Matemático:
El motor calcula tanto en servidor con **agregaciones nativas de MongoDB** como en memoria mediante **Pandas**:

$$\% Q_i = \left( \frac{\text{Recuento}(Q_i)}{\text{Total de Muestra}} \right) \times 100$$

frente a la línea teórica de distribución uniforme ($25\%$ por cuartil), evidenciando desviaciones estructurales en tiempo real.

---

## 3. Arquitectura del Sistema y Stack Tecnológico

### Diagrama de Arquitectura

```
                        ┌────────────────────────────────────────┐
                        │          CLIENTE WEB (Navegador)       │
                        └───────────────────┬────────────────────┘
                                            │ HTTP / JSON (Port 4200)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ FRONTEND: Angular 17.3+ (Standalone Components, Signals & RxJS)                        │
│  ├── Core Services: PlayerService, StatsService (Cache reactiva shareReplay)           │
│  ├── Features: Dashboard, Scouting Spotlight Search, Player Profile Radar View        │
│  └── Visualización: Chart.js 4.4 + ng2-charts 6.0 (Gráficos Radar y Distribución RAE) │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ REST API Calls (Port 8000)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ BACKEND: FastAPI & Uvicorn (Python 3.11)                                               │
│  ├── Core Config: Pydantic Settings tipado (12-Factor App & .env)                      │
│  ├── Rutas REST: /health, /api/players/search, /api/players/{id}, /api/stats/rae       │
│  ├── Inyección de Dependencias: Depends(get_database)                                  │
│  ├── Motor RAE Dual:                                                                   │
│  │    ├── Primario: Agregaciones Nativas MongoDB ($project, $month, $cond, $group)    │
│  │    └── Respaldo: Motor Estadístico Pandas / NumPy                                   │
│  └── Seguridad: Middleware CORS estricto y saneamiento de logs (CWE-532)               │
└─────────────────────┬────────────────────────────────────────────┬─────────────────────┘
                      │ Driver Asíncrono Motor                     │ BulkWrite Pipeline
                      ▼                                            ▼
┌────────────────────────────────────────┐       ┌───────────────────────────────────────┐
│ BASE DE DATOS: MongoDB 7.0             │       │ PIPELINE ETL: Ingesta Masiva          │
│  ├── Base de datos: scouting_db        │       │  ├── Fuente: Transfermarkt / HF Hub   │
│  ├── Colección: players (>28k docs)    │◄──────┤  ├── Filtro: Solo jugadores en activo │
│  └── Índices: ID único, Texto completo,│       │  ├── Calibración: Atributos 0-99      │
│      Demarcación, Nacimiento y Liga    │       │  └── Carga: ReplaceOne upsert x lotes │
└────────────────────────────────────────┘       └───────────────────────────────────────┘
```

### Backend: FastAPI & Motor Asíncrono
- **Python 3.11** sobre imagen base `python:3.11-slim` ejecutada con usuario no privilegiado (`appuser`, UID 1000).
- **FastAPI 0.111+ & Uvicorn**: Framework ASGI asíncrono de alto rendimiento con generación automática de especificaciones OpenAPI 3.0.
- **Motor (AsyncIOMotorClient)**: Driver asíncrono no bloqueante para MongoDB con pool de conexiones gestionado en el ciclo de vida de la aplicación (`lifespan`).
- **Pydantic v2 & Pydantic-Settings**: Validación rigurosa de tipos en esquemas de entrada y respuesta, con carga jerárquica de variables de entorno.
- **Índices Autoverificados**: Al arrancar, el backend comprueba y genera automáticamente los índices necesarios si no existen.

### Frontend: Angular 17+ Moderno (Signals & Standalone)
- **Arquitectura Standalone**: Libre de `NgModule`s heredados, con inicialización limpia basada en `provideRouter` y `provideHttpClient`.
- **Reactividad con Signals & Computed**: Los rankings de jugadores (*Top Valued*, *Top Shooting*, *Top Passing*, etc.) se calculan y memoizan mediante `computed()`, eliminando operaciones costosas de ordenación en cada ciclo de detección de cambios (`ChangeDetectionStrategy.OnPush`).
- **Flujos RxJS Controlados**:
  - `debounceTime(300)` y `distinctUntilChanged()`: Optimización de peticiones en la barra de búsqueda *Spotlight*.
  - `switchMap()`: Cancelación automática de peticiones HTTP en vuelo cuando el usuario continúa escribiendo.
  - `shareReplay(1)`: Cacheo reactivo de la distribución demográfica RAE.
- **Visualización Gráfica**: `ng2-charts` y `Chart.js` para renderizar el hexágono de radar técnico-físico y las barras de cuartiles.
- **Lazy Loading**: Enrutamiento asíncrono con code-splitting que reduce el tamaño del bundle inicial en más de un 50%.

### Persistencia: MongoDB 7.0 & Agregaciones
- **Base de datos**: `scouting_db`
- **Colección**: `players`
- **Índices de Alto Rendimiento**:
  - `idx_players_id`: Índice único sobre `id` ($O(1)$).
  - `idx_players_text_search`: Índice `TEXT` compuesto sobre `nombre` y `club`.
  - `idx_players_nombre`: Búsqueda textual y ordenación.
  - `idx_players_fecha_nacimiento`: Filtro y agregación temporal del RAE.
  - `idx_players_posicion`: Filtrado posicional táctico.
  - `idx_players_liga`: Segmentación por competición.

### Pipeline ETL de Ingesta Masiva de Datos
Ubicado en `api-backend/scripts/ingest_real_players.py` (con wrapper en `scripts/ingest_real_players.py`):
1. **Extracción**: Descarga el dataset oficial de jugadores de Transfermarkt (>30.000 registros).
2. **Filtrado Estricto de Actividad**: Descarta exfutbolistas retirados (ej. Berbatov, Ziegler) evaluando la última temporada en activo (`last_season >= 2024`).
3. **Normalización Posicional y de Competiciones**: Mapea demarcaciones tácticas anglosajonas al estándar en español (*Delantero Centro, Extremo Derecho, Mediapunta, Pivote, Defensa Central, etc.*).
4. **Calibración Algorítmica de Atributos (0-99)**: Modela métricas de rendimiento deportivo correlacionando demarcación táctica, valor de mercado actual y pico histórico de tasación.
5. **Carga Masiva Eficiente**: Realiza inserciones en lotes de 2.500 registros con `bulk_write` y operaciones `ReplaceOne(..., upsert=True)`.

---

## 4. Estructura del Repositorio

```
football-ai/
├── .github/
│   └── workflows/
│       └── ci.yml               # Pipeline CI: Tests Backend + Frontend + SonarCloud
├── api-backend/                 # Microservicio API REST (FastAPI)
│   ├── core/                    # Configuración centralizada y dependencias
│   │   ├── config.py            # Settings tipados con Pydantic-Settings
│   │   └── dependencies.py      # Inyección de dependencias (MongoDB)
│   ├── models/                  # Modelos y esquemas Pydantic v2
│   │   └── player.py            # Modelos Player, PlayerStats, RaeReport
│   ├── routes/                  # Endpoints modulares de la API
│   │   ├── players.py           # Rutas /api/players (búsqueda, perfil, stats)
│   │   └── stats.py             # Rutas /api/stats (motor RAE)
│   ├── services/                # Lógica de negocio y motor analítico
│   │   ├── player_service.py    # Búsqueda, paginación y benchmarks
│   │   └── rae_calculator.py    # Agregaciones MongoDB y análisis Pandas
│   ├── scripts/
│   │   └── ingest_real_players.py # Pipeline ETL de ingesta masiva
│   ├── tests/                   # Batería de pruebas unitarias y de integración
│   │   ├── test_player_service.py
│   │   ├── test_players_routes.py
│   │   ├── test_rae_calculator.py
│   │   └── test_real_players_mongo.py
│   ├── Dockerfile               # Imagen Docker de producción multi-stage
│   ├── main.py                  # Punto de entrada ASGI, lifespan y CORS
│   ├── pytest.ini               # Configuración de pruebas Pytest
│   └── requirements.txt         # Dependencias Python
├── web-frontend/                # Dashboard SPA (Angular 17+)
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/            # Modelos y servicios HTTP centrales
│   │   │   │   ├── models/      # Interfaces TypeScript (Player, RaeStats)
│   │   │   │   └── services/    # PlayerService, StatsService
│   │   │   ├── features/        # Módulos funcionales de la UI
│   │   │   │   ├── dashboard/   # Vista principal con KPIs y rankings
│   │   │   │   └── scouting/    # Buscador Spotlight, fichas y radar
│   │   │   ├── app.component.ts # Componente raíz
│   │   │   ├── app.config.ts    # Configuración Standalone (Router, HttpClient)
│   │   │   └── app.routes.ts    # Definición de rutas con Lazy Loading
│   │   └── environments/        # Configuración por entorno (dev / prod)
│   ├── angular.json             # Configuración del CLI de Angular
│   ├── Dockerfile               # Contenedor Node.js para desarrollo frontend
│   ├── karma.conf.js            # Configuración de pruebas Karma/Jasmine
│   └── package.json             # Dependencias npm y scripts
├── scripts/
│   └── ingest_real_players.py   # Wrapper raíz para ejecución rápida del ETL
├── .env.example                 # Plantilla de variables de entorno (OBLIGATORIA)
├── .gitignore                   # Exclusiones de Git (seguridad y temporales)
├── docker-compose.yml           # Orquestación de servicios (db, api, web)
└── README.md                    # Documentación técnica y de arquitectura
```

---

## 5. Guía de Inicio Rápido (Despliegue con Docker)

Esta es la vía oficial y recomendada para ejecutar todo el ecosistema (Frontend, Backend, Base de Datos y Redes) de forma idempotente y reproducible.

### Requisitos Previos
- **[Docker Engine](https://docs.docker.com/engine/install/)** (versión 24.0 o superior)
- **[Docker Compose](https://docs.docker.com/compose/install/)** (versión 2.20 o superior, integrado en Docker Desktop)
- **Git** instalado en tu sistema

---

### Paso a Paso: Del Clon de GitHub a la Producción Local

#### 1. Clonar el Repositorio
Abre tu terminal y clona el proyecto:

```bash
git clone https://github.com/danirey10/football-ai.git
cd football-ai
```

#### 2. Configurar las Variables de Entorno (`.env`)
> [!IMPORTANT]
> El archivo `docker-compose.yml` valida estrictamente la existencia de las contraseñas en el archivo `.env`. Si intentas levantar Docker sin este archivo, la ejecución se detendrá con un mensaje de error.

Copia la plantilla `.env.example` para generar tu archivo `.env`:

**En Linux / macOS:**
```bash
cp .env.example .env
```

**En Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**En Windows (CMD):**
```cmd
copy .env.example .env
```

*(Opcional)*: Puedes abrir `.env` con un editor de texto y personalizar la contraseña de `MONGO_INITDB_ROOT_PASSWORD` si lo deseas.

#### 3. Construir y Levantar los Contenedores
Ejecuta el siguiente comando para compilar las imágenes e inicializar los tres servicios en segundo plano (`-d`):

```bash
docker compose up --build -d
```

> **¿Qué ocurre internamente?**
> 1. Se crea la red interna `scouting_network` y el volumen persistente `mongo_data`.
> 2. Se levanta **MongoDB 7.0** y se ejecuta su healthcheck interno (`mongosh ping`).
> 3. Al confirmarse la salud de la base de datos, se construye y arranca el microservicio **FastAPI**, verificando los índices automáticamente.
> 4. Al responder positivamente el healthcheck de la API (`/health`), se inicializa el servidor de **Angular** en el puerto 4200.

#### 4. Verificar el Estado de los Servicios
Comprueba que los tres contenedores estén en estado saludable (`healthy` o `Up`):

```bash
docker compose ps
```

Deberías ver una salida similar a:
```
NAME                        IMAGE             STATUS                    PORTS
scouting_angular_frontend   football-ai-web   Up                        0.0.0.0:4200->4200/tcp
scouting_fastapi_backend    football-ai-api   Up (healthy)              0.0.0.0:8000->8000/tcp
scouting_mongo_db           mongo:7.0         Up (healthy)              0.0.0.0:27017->27017/tcp
```

#### 5. Ingestar los Datos Reales de Futbolistas (ETL Masivo)
> [!NOTE]
> Al arrancar por primera vez, MongoDB se inicializa con el esquema e índices pero sin registros. La API cuenta con una plantilla en memoria de respaldo, pero para disponer de la experiencia completa con **más de 28.000 futbolistas reales en activo** y análisis RAE poblacional, debes ejecutar el pipeline ETL:

Ejecuta el script de ingesta directamente dentro del contenedor de la API:

```bash
docker compose exec api python scripts/ingest_real_players.py
```

*Salida esperada:*
```
[ETL] Descargando dataset desde Hugging Face...
[ETL] 28,351 futbolistas en activo normalizados listos para ingesta.
[ETL] Lote 1/12 cargado (acumulado: 2,500)
...
[ETL] Pipeline completado con éxito! Censo activo en scouting_db.players: 28,351 futbolistas.
```

#### 6. Acceder a las Aplicaciones
Una vez completada la ingesta, abre tu navegador:

| Servicio | URL | Descripción |
| :--- | :--- | :--- |
| 🌐 **Frontend Dashboard** | [http://localhost:4200](http://localhost:4200) | Panel interactivo de scouting y análisis RAE |
| ⚡ **Backend API** | [http://localhost:8000](http://localhost:8000) | Raíz del microservicio FastAPI |
| 📚 **Swagger OpenAPI Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Documentación interactiva y consola de pruebas |
| 📖 **ReDoc Documentation** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Documentación técnica alternativa |
| 🩺 **Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | Diagnóstico del microservicio y MongoDB |

#### 7. Detener los Servicios
- **Detener los contenedores preservando los datos**:
  ```bash
  docker compose down
  ```
- **Detener los contenedores y resetear la base de datos** (eliminando volúmenes persistentes):
  ```bash
  docker compose down -v
  ```

---

## 6. Guía de Desarrollo Local (Sin Docker)

Si deseas desarrollar o depurar código directamente en tu máquina anfitriona sin contenedores:

### Requisitos
- **Python 3.11+**
- **Node.js 20+** y **npm 10+**
- Instancia local de **MongoDB 7.0** escuchando en `localhost:27017`

### Arranque del Backend

1. **Crear y activar un entorno virtual**:
   ```bash
   cd api-backend
   python -m venv venv
   
   # En Linux / macOS:
   source venv/bin/activate
   
   # En Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables locales**:
   Asegúrate de tener un archivo `.env` en la raíz del proyecto con:
   ```env
   MONGO_URI=mongodb://localhost:27017/scouting_db
   MONGO_DB_NAME=scouting_db
   CORS_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
   ```

4. **Poblar la base de datos (ETL)**:
   ```bash
   python scripts/ingest_real_players.py
   ```

5. **Iniciar el servidor de desarrollo**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Arranque del Frontend

1. **Navegar e instalar paquetes**:
   ```bash
   cd web-frontend
   npm install
   ```

2. **Iniciar servidor de desarrollo de Angular**:
   ```bash
   npm start
   ```
   El frontend estará accesible en `http://localhost:4200`.

---

## 7. Catálogo de la API REST

### Endpoints Principales

| Método | Endpoint | Descripción | Parámetros de Consulta |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Diagnóstico del microservicio y estado de conexión a MongoDB | Ninguno |
| `GET` | `/api/players/search` | Búsqueda textual y filtrado posicional con paginación | `query` / `q`, `position` / `posicion`, `max_results` / `limit`, `skip` / `offset` |
| `GET` | `/api/players/{player_id}` | Obtención del perfil biográfico y deportivo de un jugador | Ruta: `player_id` (entero o cadena) |
| `GET` | `/api/players/{player_id}/stats` | Atributos técnicos y físicos normalizados en escala 0-99 | Ruta: `player_id` |
| `GET` | `/api/stats/rae` | Informe analítico del Efecto de la Edad Relativa (Q1 a Q4) | `sample_size`, `categoria` |

### Ejemplos de Peticiones cURL

#### 1. Diagnóstico de Salud
```bash
curl -X GET "http://localhost:8000/health"
```
*Respuesta:*
```json
{
  "status": "online",
  "environment": "development",
  "database": "connected",
  "service": "scouting-dashboard-api"
}
```

#### 2. Búsqueda de Futbolistas
```bash
curl -X GET "http://localhost:8000/api/players/search?query=Pedri&limit=1"
```
*Respuesta:*
```json
[
  {
    "id": 683840,
    "nombre": "Pedri",
    "fecha_nacimiento": "2002-11-25",
    "posicion": "Centrocampista",
    "liga": "LaLiga EA Sports",
    "club": "FC Barcelona",
    "pace": 80,
    "shooting": 84,
    "passing": 97,
    "dribbling": 99,
    "defending": 72,
    "physicality": 88,
    "overall": 87
  }
]
```

#### 3. Métricas de Radar Posicional
```bash
curl -X GET "http://localhost:8000/api/players/683840/stats"
```
*Respuesta:*
```json
{
  "player_id": 683840,
  "nombre": "Pedri",
  "posicion": "Centrocampista",
  "pace": 80,
  "shooting": 84,
  "passing": 97,
  "dribbling": 99,
  "defending": 72,
  "physicality": 88,
  "overall": 87
}
```

#### 4. Distribución RAE (Efecto de la Edad Relativa)
```bash
curl -X GET "http://localhost:8000/api/stats/rae"
```
*Respuesta:*
```json
{
  "totalPlayers": 28351,
  "category": "Censo Global / Transfermarkt",
  "season": "2025/2026",
  "quarters": [
    { "id": "Q1", "name": "Primer Trimestre", "months": "Ene - Mar", "count": 9024, "percentage": 31.83 },
    { "id": "Q2", "name": "Segundo Trimestre", "months": "Abr - Jun", "count": 7529, "percentage": 26.56 },
    { "id": "Q3", "name": "Tercer Trimestre", "months": "Jul - Sep", "count": 6588, "percentage": 23.24 },
    { "id": "Q4", "name": "Cuarto Trimestre", "months": "Oct - Dic", "count": 5210, "percentage": 18.38 }
  ],
  "distribution": {
    "Q1": { "count": 9024, "percentage": 31.83 },
    "Q2": { "count": 7529, "percentage": 26.56 },
    "Q3": { "count": 6588, "percentage": 23.24 },
    "Q4": { "count": 5210, "percentage": 18.38 }
  }
}
```

---

## 8. Batería de Pruebas y Control de Calidad

El proyecto dispone de un conjunto integral de **37 pruebas automatizadas** en el backend y pruebas unitarias en el frontend con cobertura de código.

### 1. Pruebas del Backend (Pytest)
Para ejecutar la suite completa en el entorno Docker:

```bash
docker compose exec api pytest -v
```

*O con informe detallado de cobertura:*
```bash
docker compose exec api pytest --cov=. --cov-report=term-missing
```

Las pruebas verifican:
- Búsqueda textual exacta y aproximada con fallback.
- Paginación e inmutabilidad de esquemas Pydantic.
- Exclusión estricta de exfutbolistas retirados (ej. Berbatov, Marc Ziegler).
- Existencia y validación de futbolistas emblemáticos (ej. Iago Aspas, Pedri).
- Agregación nativa del RAE en MongoDB frente a cálculos en Pandas.
- Creación y consistencia de los índices de MongoDB.

### 2. Pruebas del Frontend (Karma & Jasmine)
Para ejecutar las pruebas en modo headless:

```bash
cd web-frontend
npm test -- --no-watch --browsers=ChromeHeadless
```

### 3. Pipeline de Integración Continua (CI/CD)
El repositorio incorpora un flujo de GitHub Actions configurado en `.github/workflows/ci.yml` que en cada *Push* y *Pull Request* ejecuta:
- Verificación de formato y sintaxis en Python 3.11.
- Ejecución de Pytest con exportación de reporte XML de cobertura.
- Verificación y compilación estricta de Angular (`ng build --configuration production`).
- Pruebas unitarias de Angular en navegador virtual ChromeHeadless.
- Análisis estático de vulnerabilidades y deuda técnica con **SonarCloud**.

---

## 9. Matriz de Variables de Entorno

Todas las variables se definen en el archivo `.env` en la raíz del proyecto:

| Variable | Tipo | Valor por Defecto | Ámbito | Descripción |
| :--- | :--- | :--- | :--- | :--- |
| `MONGO_INITDB_ROOT_USERNAME` | `string` | `scoutadmin` | MongoDB / Docker | Usuario administrador raíz para MongoDB |
| `MONGO_INITDB_ROOT_PASSWORD` | `string` | *Requerido* | MongoDB / Docker | Contraseña del usuario administrador de MongoDB |
| `MONGO_INITDB_DATABASE` | `string` | `scouting_db` | MongoDB / Docker | Base de datos creada en la inicialización |
| `MONGO_URI` | `string` | `mongodb://scoutadmin:...@db:27017/?authSource=admin` | Backend / Docker | Cadena de conexión asíncrona a MongoDB |
| `MONGO_DB_NAME` | `string` | `scouting_db` | Backend | Nombre de la base de datos de trabajo |
| `CORS_ORIGINS` | `string` | `http://localhost:4200` | Backend | Orígenes permitidos separados por comas para CORS |
| `API_PORT` | `integer` | `8000` | Backend / Docker | Puerto de publicación del microservicio FastAPI |
| `WEB_PORT` | `integer` | `4200` | Frontend / Docker | Puerto de publicación del dashboard de Angular |
| `LOG_LEVEL` | `string` | `INFO` | Backend | Nivel de logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `ENVIRONMENT` | `string` | `development` | Backend | Entorno de ejecución (`development`, `test`, `production`) |

---

## 10. Preguntas Frecuentes y Solución de Problemas (Troubleshooting)

### P: Al ejecutar `docker compose up` obtengo el error: `Defina MONGO_INITDB_ROOT_PASSWORD en .env`.
**R:** Olvidaste crear el archivo `.env`. Docker Compose requiere obligatoriamente que este archivo exista para evitar levantar bases de datos sin credenciales.  
Ejecuta:
- Windows (PowerShell): `Copy-Item .env.example .env`
- Linux / macOS: `cp .env.example .env`

### P: El frontend carga pero la búsqueda no devuelve futbolistas o muestra solo los de prueba.
**R:** Cuando MongoDB arranca por primera vez, la colección está vacía. Debes ejecutar el pipeline de ingesta masiva:
```bash
docker compose exec api python scripts/ingest_real_players.py
```

### P: Error `address already in use` en los puertos 4200, 8000 o 27017.
**R:** Hay otro servicio en tu equipo ocupando alguno de esos puertos.
- Para verificar qué proceso ocupa el puerto en Windows:
  ```powershell
  Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess
  ```
- Para verificar en Linux / macOS:
  ```bash
  lsof -i :8000
  ```
Puedes modificar los puertos mapeados en `.env` (`API_PORT=8001`, `WEB_PORT=4201`).

### P: ¿Los cambios que hago en el código se reflejan automáticamente?
**R:** **Sí.** El entorno Docker Compose está configurado con volúmenes montados y recarga en caliente:
- En el **Backend**: Uvicorn detecta modificaciones en `./api-backend` gracias al flag `--reload`.
- En el **Frontend**: Angular CLI detecta cambios en `./web-frontend` gracias a `--poll 2000` y `CHOKIDAR_USEPOLLING=true`.

---

## 11. Licencia

Este proyecto está bajo la licencia **MIT**. Consulta el código fuente y las cabeceras de los archivos para más detalles.
