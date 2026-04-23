# PROINTEL - Panel Web

Frontend operativo de PROINTEL. Vue 3 + TypeScript + Rsbuild + Tailwind v4,
con cliente HTTP propio hacia el backend Django REST.

## Stack

- **Vue 3** (Composition API, `<script setup>`)
- **TypeScript** estricto
- **Rsbuild** (dev server + build)
- **Tailwind CSS v4** + tokens de diseno en `src/styles/tokens.css`
- **Biome** (lint + format)
- **Rstest** (tests)
- **Chart.js** / **vue-chartjs** (Dashboard)
- **Leaflet** (mapas operativos del tecnico)

## Scripts

```bash
npm install          # instalar dependencias
npm run dev          # dev server en http://localhost:3000
npm run build        # build produccion
npm run preview      # servir el build local
npm run lint         # Biome lint + fix
npm run format       # Biome format
npm run test         # Rstest
```

## Configuracion del backend

La URL base del backend se lee de `VITE_API_BASE_URL`.

```bash
cp .env.example .env
# edita .env con la URL real del backend
npm run dev
```

En ausencia de esa variable se usa `http://127.0.0.1:8000/api`.

El cliente HTTP (`src/api/http.ts`) incluye:

- Token JWT en `Authorization: Bearer <access>`.
- Refresh automatico con `POST /auth/refresh/` cuando el backend responde 401.
- Persistencia de tokens/usuario en `localStorage` (`src/stores/sessionStore.ts`).

## Estructura del proyecto

```
src/
  api/                 cliente HTTP + un modulo por recurso
    http.ts            fetch + refresh + helpers (withQuery, unwrapList)
    auth.ts            login, fetchMe, restoreSession, logout
    pedidos.ts         CRUD pedidos + checklist, evidencias, informe tecnico
    clientes.ts        CRUD clientes
    cuentas.ts         CRUD cuentas
    tecnicos.ts        CRUD tecnicos + recomendacion
    inventario.ts      CRUD inventario
    index.ts           barrel re-export
  components/
    layout/
      SidebarNav.vue   menu principal lateral
  stores/              estado compartido (singletons basados en composables)
    sessionStore.ts    tokens + usuario autenticado
    pedidosStore.ts    pedidos + checklists + evidencias + informes
  styles/
    tokens.css         variables CSS (paleta verde corporativa)
  types/
    navigation.ts      tipado del menu y vistas
  views/               vistas de primer nivel
    LoginView.vue
    DashboardView.vue
    PedidosView.vue
    PedidosTecnicoView.vue
    BaseDatosView.vue
  App.vue              shell + routing manual por rol
  index.ts             bootstrap Vue
  index.css            imports globales (tailwind, leaflet, tokens)
```

### Reglas de organizacion

- **`api/` nunca importa de `views/` ni de `components/`.** Flujo: view → store → api.
- **`stores/`** expone funciones `useXxxStore()` que retornan refs/computed reactivas.
- **`components/layout/`** contiene piezas del shell (sidebar, futuros headers/footers).
  Componentes especificos de una vista viven junto a esa vista cuando se extraigan.
- **Los tipos del dominio vienen desde `api/`** (tipos `ApiXxx`). No duplicar en views.
- **No usar rutas relativas profundas** (`../../services/...`). Importar desde `./api`
  o `./stores/...` siempre desde la raiz de `src/`.

## Paleta de diseno

Definida en `src/styles/tokens.css`. Se consume via variables CSS:

- `--color-primary-500` verde corporativo (#10b981)
- `--color-primary-{50..900}` escala completa
- `--color-bg`, `--color-surface`, `--color-surface-2`, `--color-surface-alt`
- `--color-text`, `--color-text-soft`, `--color-text-muted`
- `--color-border`, `--color-border-strong`, `--color-border-focus`
- `--color-success`, `--color-warning`, `--color-danger`, `--color-info`
- `--shadow-sm`, `--shadow-md`, `--shadow-lg`
- `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-xl`, `--radius-pill`

Las clases utilitarias de Tailwind v4 disponen ademas del scale `brand-{50..900}`
gracias al bloque `@theme` en `src/index.css`.

## Roles y vistas

| Rol           | Vistas disponibles                                   |
| ------------- | ---------------------------------------------------- |
| admin         | Dashboard, Pedidos, Pedidos Tecnico, Base de Datos   |
| coordinador   | Dashboard, Pedidos, Pedidos Tecnico, Base de Datos   |
| tecnico       | Dashboard, Pedidos, Pedidos Tecnico                  |

El shell escoge la vista por defecto segun el rol tras login.

## Proximos pasos sugeridos

- Extraer sub-componentes de las views grandes (PedidosView, BaseDatosView,
  PedidosTecnicoView) en `components/pedidos/`, `components/base-datos/`, etc.
- Anadir `vue-router` cuando haya deep-links / historia del navegador.
- Introducir `pinia` si el estado compartido crece (por ahora los composables
  singleton son suficientes).
- Cubrir las vistas con tests unitarios (Rstest + @testing-library/vue).
