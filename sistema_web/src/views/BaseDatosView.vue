<template>
  <section class="base-view">
    <transition name="toast-fade">
      <article
        v-if="feedbackVisible"
        class="crud-toast"
        :class="feedbackType === 'success' ? 'is-success' : 'is-error'"
        role="status"
        aria-live="polite"
      >
        <div class="feedback-copy">
          <strong>{{ feedbackType === 'success' ? 'Operacion completada' : 'Operacion fallida' }}</strong>
          <span>{{ feedbackMessage }}</span>
        </div>
        <button type="button" class="feedback-close" @click="hideFeedback">Cerrar</button>
      </article>
    </transition>

    <template v-if="activeModuleKey === null">
      <header class="base-head card">
        <h2>Base de datos</h2>
      </header>

      <section class="cards-grid">
        <button
          v-for="module in modules"
          :key="module.key"
          class="module-card card"
          @click="openModule(module.key)"
        >
          <div class="module-top">
            <h3 :class="{ 'inventory-highlight': module.key === 'inventario' }">
              {{ module.key === 'inventario' ? 'INVENTARIO' : module.title }}
            </h3>
            <span>{{ module.code }}</span>
          </div>
          <p>{{ module.description }}</p>
          <small>{{ module.metrics }}</small>
          <strong class="open-link">Abrir CRUD</strong>
        </button>
      </section>
    </template>

    <template v-else-if="activeModuleKey === 'cuentas-clientes'">
      <header class="crud-head card">
        <div>
          <h2>Cuentas / Clientes</h2>
          <p>Gestiona clientes por secciones y sus cuentas en tarjetas.</p>
        </div>
        <button class="btn ghost" @click="goBack">Regresar</button>
      </header>

      <section class="crud-shell card">
        <template v-if="cuentasClientesView === 'list'">
          <article class="panel toolbar-panel clients-toolbar">
            <div class="toolbar-copy">
              <h3>Clientes y cuentas</h3>
              <p>Cada cliente contiene sus cuentas asociadas en tarjetas.</p>
            </div>
            <div class="toolbar-actions">
              <input
                v-model="clientSearch"
                class="search"
                type="search"
                placeholder="Buscar cliente, RUC, contacto o cuenta"
              />
              <button class="btn ghost" :disabled="loadingClientesCuentas" @click="loadClientesCuentasRows">
                {{ loadingClientesCuentas ? 'Actualizando...' : 'Actualizar backend' }}
              </button>
              <button class="btn primary" @click="startCreateCliente">Crear nuevo cliente</button>
            </div>
          </article>

          <article v-if="clientesCuentasLoadError" class="panel load-warning">
            {{ clientesCuentasLoadError }}
          </article>

          <section class="clientes-stack">
            <article v-for="cliente in filteredClients" :key="cliente.id" class="panel cliente-card">
              <header class="cliente-head">
                <div>
                  <h3>{{ cliente.nombre }}</h3>
                  <p>RUC: {{ cliente.ruc }}</p>
                </div>
                <span class="status-badge" :class="cliente.estado === 'Activo' ? 'active' : 'inactive'">
                  {{ cliente.estado }}
                </span>
              </header>

              <div class="cliente-meta">
                <p><strong>Contacto:</strong> {{ cliente.contacto }}</p>
                <p><strong>Cuentas:</strong> {{ getClientAccounts(cliente.id).length }}</p>
              </div>

              <div class="cliente-actions">
                <button class="btn mini" @click="startEditCliente(cliente)">Editar cliente</button>
                <button class="btn mini danger" @click="askRemoveClient(cliente)">Eliminar cliente</button>
                <button
                  class="btn primary"
                  :disabled="cliente.estado === 'Inactivo'"
                  @click="startCreateCuenta(cliente.id)"
                >
                  Crear nueva cuenta
                </button>
              </div>

              <section class="cuentas-section">
                <header class="cuentas-head">
                  <h4>Cuentas del cliente</h4>
                </header>

                <div v-if="getFilteredAccountsForClient(cliente).length === 0" class="empty-cuentas">
                  <p>No hay cuentas registradas para este cliente.</p>
                  <button class="btn mini" :disabled="cliente.estado === 'Inactivo'" @click="startCreateCuenta(cliente.id)">
                    Crear primera cuenta
                  </button>
                </div>

                <div v-else class="cuentas-grid">
                  <article
                    v-for="cuenta in getFilteredAccountsForClient(cliente)"
                    :key="`${cliente.id}-${cuenta.id}`"
                    class="cuenta-card"
                  >
                    <div class="cuenta-top">
                      <strong>{{ cuenta.nombre }}</strong>
                      <span>{{ cuenta.codigo }}</span>
                    </div>
                    <p class="cuenta-address">{{ cuenta.direccion || '-' }}</p>
                    <div class="cuenta-meta">
                      <span>Distrito: {{ cuenta.distrito || '-' }}</span>
                      <span>Coordenadas: {{ formatCuentaCoordinates(cuenta) }}</span>
                      <span>Contacto: {{ cuenta.contacto || '-' }}</span>
                      <span>Telefono: {{ cuenta.telefono || '-' }}</span>
                      <span class="state-pill" :class="cuenta.estado === 'Activa' ? 'ok' : 'warn'">{{ cuenta.estado }}</span>
                    </div>
                    <div class="cuenta-actions">
                      <button class="btn mini" @click="startEditCuenta(cliente.id, cuenta)">Editar</button>
                      <button class="btn mini danger" @click="askRemoveCuenta(cliente.id, cuenta)">Eliminar</button>
                    </div>
                  </article>
                </div>
              </section>
            </article>

            <article v-if="filteredClients.length === 0" class="panel empty-clients">
              <h3>No hay clientes para la busqueda.</h3>
              <p>Intenta con otro termino o crea un cliente nuevo.</p>
              <button class="btn primary" @click="startCreateCliente">Crear nuevo cliente</button>
            </article>
          </section>
        </template>

        <form
          v-else-if="cuentasClientesView === 'cliente-form'"
          class="editor card standalone-form"
          @submit.prevent="saveClienteForm"
        >
          <div class="form-head">
            <div>
              <h3>{{ clienteFormMode === 'create' ? 'Crear nuevo cliente' : 'Editar cliente' }}</h3>
              <p>Completa los datos del cliente y luego registra sus cuentas.</p>
            </div>
            <button type="button" class="btn ghost" @click="goToClientesList">Volver</button>
          </div>

          <div class="editor-grid">
            <label>
              <span>Nombre cliente</span>
              <input v-model.trim="clienteForm.nombre" type="text" required />
            </label>
            <label>
              <span>RUC</span>
              <input v-model.trim="clienteForm.ruc" type="text" required />
            </label>
            <label>
              <span>Contacto</span>
              <input v-model.trim="clienteForm.contacto" type="text" required />
            </label>
            <label>
              <span>Estado</span>
              <select v-model="clienteForm.estado" required>
                <option value="Activo">Activo</option>
                <option value="Inactivo">Inactivo</option>
              </select>
            </label>
          </div>

          <div class="editor-actions">
            <button type="button" class="btn ghost" @click="goToClientesList">Cancelar</button>
            <button type="submit" class="btn primary">Guardar cliente</button>
          </div>
        </form>

        <form v-else class="editor card standalone-form" @submit.prevent="saveCuentaForm">
          <div class="form-head">
            <div>
              <h3>{{ cuentaFormMode === 'create' ? 'Crear nueva cuenta' : 'Editar cuenta' }}</h3>
              <p>
                Cliente: <strong>{{ cuentaTargetClienteName || 'No definido' }}</strong>
              </p>
            </div>
            <button type="button" class="btn ghost" @click="goToClientesList">Volver</button>
          </div>

          <div class="editor-grid">
            <label>
              <span>Codigo cuenta</span>
              <input v-model.trim="cuentaForm.codigo" type="text" required />
            </label>
            <label>
              <span>Nombre cuenta</span>
              <input v-model.trim="cuentaForm.nombre" type="text" required />
            </label>
            <label>
              <span>Direccion</span>
              <input v-model.trim="cuentaForm.direccion" type="text" required />
            </label>
            <label>
              <span>Distrito</span>
              <input v-model.trim="cuentaForm.distrito" type="text" required />
            </label>
            <label>
              <span>Latitud</span>
              <input v-model.trim="cuentaForm.latitud" type="text" required />
            </label>
            <label>
              <span>Longitud</span>
              <input v-model.trim="cuentaForm.longitud" type="text" required />
            </label>
            <label>
              <span>Contacto</span>
              <input v-model.trim="cuentaForm.contacto" type="text" required />
            </label>
            <label>
              <span>Telefono</span>
              <input v-model.trim="cuentaForm.telefono" type="text" required />
            </label>
            <label>
              <span>Estado</span>
              <select v-model="cuentaForm.estado" required>
                <option value="Activa">Activa</option>
                <option value="Suspendida">Suspendida</option>
              </select>
            </label>
          </div>

          <div class="editor-actions">
            <button type="button" class="btn ghost" @click="goToClientesList">Cancelar</button>
            <button type="submit" class="btn primary">Guardar cuenta</button>
          </div>
        </form>
      </section>
    </template>

    <template v-else>
      <header class="crud-head card">
        <div>
          <h2>{{ activeModule?.title }}</h2>
          <p>{{ activeModule?.description }}</p>
        </div>
        <button class="btn ghost" @click="goBack">Regresar</button>
      </header>

      <section class="crud-shell card">
        <div class="toolbar-panel panel">
          <input
            v-model="searchQuery"
            type="search"
            class="search"
            placeholder="Buscar en la tabla"
          />
          <div class="toolbar-inline-actions">
            <button
              v-if="activeModuleSupportsRefresh"
              class="btn ghost"
              :disabled="activeModuleLoading"
              @click="loadActiveModuleRows"
            >
              {{ activeModuleLoading ? 'Actualizando...' : activeRefreshLabel }}
            </button>
            <button v-if="activeModuleKey !== 'pedidos'" class="btn primary" @click="startCreateGeneric">Nuevo registro</button>
          </div>
        </div>

        <article v-if="activeGenericLoadError" class="panel load-warning">
          {{ activeGenericLoadError }}
        </article>

        <article class="panel">
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th v-for="column in activeGenericColumns" :key="column.key">{{ column.label }}</th>
                  <th class="actions">Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in filteredGenericRows" :key="String(row.id)">
                  <td v-for="column in activeGenericColumns" :key="column.key">{{ String(row[column.key] ?? '-') }}</td>
                  <td class="action-buttons">
                    <button
                      class="btn mini"
                      :disabled="activeModuleKey === 'pedidos' && isPedidoBajaRow(row)"
                      @click="startEditGeneric(row)"
                    >
                      Editar
                    </button>
                    <button
                      class="btn mini danger"
                      :disabled="activeModuleKey === 'pedidos' && isPedidoBajaRow(row)"
                      @click="askRemoveGenericRow(row)"
                    >
                      {{ activeModuleKey === 'pedidos' ? (isPedidoBajaRow(row) ? 'Dado de baja' : 'Dar de baja') : 'Eliminar' }}
                    </button>
                  </td>
                </tr>
                <tr v-if="filteredGenericRows.length === 0">
                  <td :colspan="activeGenericColumns.length + 1" class="empty-row">
                    No se encontraron registros para la busqueda.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <form v-if="isEditing" class="editor card" @submit.prevent="saveGenericRow">
          <h3>{{ editMode === 'create' ? 'Crear registro' : 'Editar registro' }}</h3>
          <div class="editor-grid">
            <label v-for="column in activeGenericColumns" :key="column.key">
              <span>{{ column.label }}</span>
              <select
                v-if="activeModuleKey === 'pedidos' && column.key === 'estado'"
                v-model="formState[column.key]"
                required
              >
                <option v-for="estadoOption in pedidoStatusOptions" :key="estadoOption" :value="estadoOption">
                  {{ estadoOption }}
                </option>
              </select>
              <select
                v-else-if="activeModuleKey === 'pedidos' && column.key === 'fase'"
                v-model="formState[column.key]"
                required
              >
                <option v-for="faseOption in pedidoFaseOptions" :key="faseOption" :value="faseOption">
                  {{ faseOption }}
                </option>
              </select>
              <select
                v-else-if="activeModuleKey === 'pedidos' && column.key === 'prioridad'"
                v-model="formState[column.key]"
                required
              >
                <option v-for="prioridadOption in pedidoPrioridadOptions" :key="prioridadOption" :value="prioridadOption">
                  {{ prioridadOption }}
                </option>
              </select>
              <input v-else v-model="formState[column.key]" type="text" :placeholder="column.label" required />
            </label>
          </div>
          <div class="editor-actions">
            <button type="button" class="btn ghost" @click="cancelEdit">Cancelar</button>
            <button type="submit" class="btn primary">Guardar</button>
          </div>
        </form>
      </section>
    </template>

    <div v-if="deleteDialog.open" class="delete-modal-backdrop" @click.self="closeDeleteDialog()">
      <article class="delete-modal card" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title">
        <header class="delete-modal-head">
          <h3 id="delete-dialog-title">{{ deleteDialog.title }}</h3>
          <p>{{ deleteDialog.message }}</p>
        </header>
        <div class="delete-modal-actions">
          <button type="button" class="btn ghost" :disabled="deleteDialogLoading" @click="closeDeleteDialog()">
            Cancelar
          </button>
          <button type="button" class="btn danger solid" :disabled="deleteDialogLoading" @click="confirmDeleteDialog">
            {{
              deleteDialogLoading
                ? (deleteDialog.title.toLowerCase().includes('baja') ? 'Aplicando baja...' : 'Eliminando...')
                : (deleteDialog.title.toLowerCase().includes('baja') ? 'Dar de baja' : 'Eliminar')
            }}
          </button>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import {
  type ApiCliente,
  type ApiCuenta,
  type ApiInventario,
  type ApiPedido,
  type ApiTecnico,
  createCliente,
  createCuenta,
  createInventario,
  createTecnico,
  darBajaPedido,
  deleteCliente,
  deleteCuenta,
  deleteInventario,
  deleteTecnico,
  listClientes,
  listCuentas,
  listInventario,
  listPedidosWithOptions,
  listTecnicos,
  updateCliente,
  updateCuenta,
  updateInventario,
  updatePedido,
  updateTecnico,
} from '../api';

type ModuleKey =
  | 'inventario'
  | 'cuentas-clientes'
  | 'pedidos'
  | 'personal-campo'
  | 'reportes';
type GenericModuleKey =
  | 'inventario'
  | 'pedidos'
  | 'personal-campo'
  | 'reportes';
type EditMode = 'create' | 'edit';
type CuentasClientesView = 'list' | 'cliente-form' | 'cuenta-form';
type EditEntity = 'generic' | 'cliente' | 'cuenta';
type FeedbackType = 'success' | 'error';

interface ColumnDef {
  key: string;
  label: string;
}

interface DataRow {
  id: string;
  [key: string]: string | number;
}

interface ModuleConfig {
  key: ModuleKey;
  code: string;
  title: string;
  description: string;
  metrics: string;
  columns?: ColumnDef[];
}

interface ClienteItem {
  id: string;
  nombre: string;
  ruc: string;
  contacto: string;
  estado: 'Activo' | 'Inactivo';
}

interface CuentaItem {
  id: string;
  codigo: string;
  nombre: string;
  direccion: string;
  distrito: string;
  latitud: string;
  longitud: string;
  contacto: string;
  telefono: string;
  estado: 'Activa' | 'Suspendida';
}

interface DeleteDialogState {
  open: boolean;
  title: string;
  message: string;
}

const modules: ModuleConfig[] = [
  {
    key: 'inventario',
    code: 'INV',
    title: 'Inventario',
    description: 'Control de stock, almacenes y reposicion.',
    metrics: 'Sin datos cargados',
    columns: [
      { key: 'sku', label: 'SKU' },
      { key: 'descripcion', label: 'Descripcion' },
      { key: 'categoria', label: 'Categoria' },
      { key: 'stock', label: 'Stock' },
      { key: 'almacen', label: 'Almacen' },
    ],
  },
  {
    key: 'cuentas-clientes',
    code: 'CCL',
    title: 'Cuentas / Clientes',
    description: 'Clientes y sus cuentas asociadas.',
    metrics: 'Sin datos cargados',
  },
  {
    key: 'pedidos',
    code: 'PDS',
    title: 'Pedidos',
    description: 'Pedidos operativos sincronizados desde backend.',
    metrics: 'Sin datos cargados',
    columns: [
      { key: 'ot', label: 'OT' },
      { key: 'cliente', label: 'Cliente' },
      { key: 'servicio', label: 'Servicio' },
      { key: 'fase', label: 'Fase' },
      { key: 'estado', label: 'Estado' },
      { key: 'prioridad', label: 'Prioridad' },
      { key: 'fecha', label: 'Fecha' },
    ],
  },
  {
    key: 'personal-campo',
    code: 'PCF',
    title: 'Personal de campo',
    description: 'Tecnicos, especialidades y disponibilidad.',
    metrics: 'Sin datos cargados',
    columns: [
      { key: 'tecnico', label: 'Tecnico' },
      { key: 'especialidad', label: 'Especialidad' },
      { key: 'zona', label: 'Zona' },
      { key: 'turno', label: 'Turno' },
      { key: 'estado', label: 'Estado' },
    ],
  },
  {
    key: 'reportes',
    code: 'RPT',
    title: 'Reportes',
    description: 'Catalogo de reportes operativos y financieros.',
    metrics: 'Sin datos cargados',
    columns: [
      { key: 'reporte', label: 'Reporte' },
      { key: 'frecuencia', label: 'Frecuencia' },
      { key: 'propietario', label: 'Propietario' },
      { key: 'formato', label: 'Formato' },
      { key: 'estado', label: 'Estado' },
    ],
  },
];

const genericRows = reactive<Record<GenericModuleKey, DataRow[]>>({
  inventario: [],
  pedidos: [],
  'personal-campo': [],
  reportes: [],
});

const pedidoSnapshotById = reactive<Record<string, ApiPedido>>({});

const pedidoStatusLabels: Record<ApiPedido['status_operativo'], string> = {
  'por-confirmar': 'Por confirmar',
  confirmado: 'Confirmado',
  'en-labor': 'En labor',
  'cierre-tecnico': 'Cierre tecnico',
  facturacion: 'Facturacion',
  completado: 'Completado',
  'dado-de-baja': 'Dado de baja',
};

const pedidoFaseLabels: Record<ApiPedido['fase'], string> = {
  creacion: 'Creacion',
  programacion: 'Programacion',
  seguimiento: 'Seguimiento',
  cierre: 'Cierre',
};

const pedidoPrioridadLabels: Record<ApiPedido['prioridad'], string> = {
  baja: 'Baja',
  media: 'Media',
  alta: 'Alta',
  critica: 'Critica',
};

const pedidoStatusOptions = Object.values(pedidoStatusLabels);
const pedidoFaseOptions = Object.values(pedidoFaseLabels);
const pedidoPrioridadOptions = Object.values(pedidoPrioridadLabels);

const clientesRows = ref<ClienteItem[]>([]);

const cuentasByCliente = reactive<Record<string, CuentaItem[]>>({});

const activeModuleKey = ref<ModuleKey | null>(null);
const searchQuery = ref('');
const clientSearch = ref('');
const loadingPedidos = ref(false);
const pedidosLoadError = ref('');
const loadingClientesCuentas = ref(false);
const clientesCuentasLoadError = ref('');
const cuentasClientesView = ref<CuentasClientesView>('list');
const clienteFormMode = ref<EditMode>('create');
const cuentaFormMode = ref<EditMode>('create');
const clienteEditingId = ref<string | null>(null);
const cuentaEditingId = ref<string | null>(null);
const cuentaTargetClienteId = ref<string | null>(null);
const feedbackVisible = ref(false);
const feedbackType = ref<FeedbackType>('success');
const feedbackMessage = ref('');
const deleteDialogLoading = ref(false);
const deleteDialogAction = ref<(() => Promise<void>) | null>(null);
const deleteDialog = reactive<DeleteDialogState>({
  open: false,
  title: '',
  message: '',
});
let feedbackTimer: ReturnType<typeof setTimeout> | null = null;

const isEditing = ref(false);
const editMode = ref<EditMode>('create');
const editEntity = ref<EditEntity>('generic');
const editingId = ref<string | null>(null);
const formState = reactive<Record<string, string>>({});
const loadingInventario = ref(false);
const inventarioLoadError = ref('');
const loadingTecnicos = ref(false);
const tecnicosLoadError = ref('');

const clienteForm = reactive<ClienteItem>({
  id: '',
  nombre: '',
  ruc: '',
  contacto: '',
  estado: 'Activo',
});

const cuentaForm = reactive<CuentaItem>({
  id: '',
  codigo: '',
  nombre: '',
  direccion: '',
  distrito: '',
  latitud: '',
  longitud: '',
  contacto: '',
  telefono: '',
  estado: 'Activa',
});

const activeModule = computed(
  () => modules.find((module) => module.key === activeModuleKey.value) || null,
);

const activeGenericColumns = computed(() => activeModule.value?.columns || []);

const activeGenericRows = computed(() => {
  if (!activeModuleKey.value || activeModuleKey.value === 'cuentas-clientes')
    return [];
  return genericRows[activeModuleKey.value as GenericModuleKey];
});

const activeModuleSupportsRefresh = computed(
  () =>
    activeModuleKey.value === 'pedidos' ||
    activeModuleKey.value === 'inventario' ||
    activeModuleKey.value === 'personal-campo',
);

const activeModuleLoading = computed(() => {
  if (activeModuleKey.value === 'pedidos') return loadingPedidos.value;
  if (activeModuleKey.value === 'inventario') return loadingInventario.value;
  if (activeModuleKey.value === 'personal-campo') return loadingTecnicos.value;
  return false;
});

const activeRefreshLabel = computed(() => {
  if (activeModuleKey.value === 'pedidos') return 'Actualizar pedidos';
  if (activeModuleKey.value === 'inventario') return 'Actualizar inventario';
  if (activeModuleKey.value === 'personal-campo')
    return 'Actualizar personal de campo';
  return 'Actualizar';
});

const activeGenericLoadError = computed(() => {
  if (activeModuleKey.value === 'pedidos') return pedidosLoadError.value;
  if (activeModuleKey.value === 'inventario') return inventarioLoadError.value;
  if (activeModuleKey.value === 'personal-campo')
    return tecnicosLoadError.value;
  return '';
});

const filteredGenericRows = computed(() => {
  const query = searchQuery.value.trim().toLowerCase();
  if (!query) return activeGenericRows.value;

  return activeGenericRows.value.filter((row) =>
    Object.values(row).some((value) =>
      String(value).toLowerCase().includes(query),
    ),
  );
});

const filteredClients = computed(() => {
  const query = clientSearch.value.trim().toLowerCase();
  if (!query) return clientesRows.value;

  return clientesRows.value.filter((cliente) => {
    const matchesCliente = [
      cliente.nombre,
      cliente.ruc,
      cliente.contacto,
      cliente.estado,
    ]
      .join(' ')
      .toLowerCase()
      .includes(query);

    if (matchesCliente) return true;
    return getClientAccounts(cliente.id).some((cuenta) =>
      [
        cuenta.codigo,
        cuenta.nombre,
        cuenta.direccion,
        cuenta.distrito,
        cuenta.contacto,
        cuenta.telefono,
        cuenta.estado,
      ]
        .join(' ')
        .toLowerCase()
        .includes(query),
    );
  });
});

const cuentaTargetClienteName = computed(
  () =>
    clientesRows.value.find(
      (cliente) => cliente.id === cuentaTargetClienteId.value,
    )?.nombre || '',
);

function toErrorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function clearFeedbackTimer() {
  if (!feedbackTimer) return;
  clearTimeout(feedbackTimer);
  feedbackTimer = null;
}

function hideFeedback() {
  clearFeedbackTimer();
  feedbackVisible.value = false;
  feedbackMessage.value = '';
}

function showFeedback(message: string, type: FeedbackType) {
  clearFeedbackTimer();
  feedbackType.value = type;
  feedbackMessage.value = message;
  feedbackVisible.value = true;
  feedbackTimer = setTimeout(() => {
    feedbackVisible.value = false;
  }, 3000);
}

function showSuccess(message: string) {
  showFeedback(message, 'success');
}

function showError(message: string) {
  showFeedback(message, 'error');
}

function openDeleteDialog(
  title: string,
  message: string,
  action: () => Promise<void>,
) {
  deleteDialog.title = title;
  deleteDialog.message = message;
  deleteDialogAction.value = action;
  deleteDialogLoading.value = false;
  deleteDialog.open = true;
}

function closeDeleteDialog(force = false) {
  if (deleteDialogLoading.value && !force) return;
  deleteDialog.open = false;
  deleteDialog.title = '';
  deleteDialog.message = '';
  deleteDialogAction.value = null;
  deleteDialogLoading.value = false;
}

async function confirmDeleteDialog() {
  if (!deleteDialogAction.value || deleteDialogLoading.value) return;

  deleteDialogLoading.value = true;
  try {
    await deleteDialogAction.value();
    closeDeleteDialog(true);
  } catch {
    // Keep modal open so user can retry or cancel after an API failure.
  } finally {
    deleteDialogLoading.value = false;
  }
}

function parseInteger(value: string | null | undefined, fallback: number) {
  const parsed = Number.parseInt((value || '').trim(), 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function parseCoordinate(
  value: string | null | undefined,
  min: number,
  max: number,
) {
  const parsed = Number.parseFloat((value || '').trim());
  if (!Number.isFinite(parsed)) return null;
  if (parsed < min || parsed > max) return null;
  return parsed;
}

function parseEstadoActivo(
  estado: string | null | undefined,
  defaultValue: boolean,
) {
  const normalized = (estado || '').trim().toLowerCase();
  if (!normalized) return defaultValue;
  return normalized !== 'inactivo' && normalized !== 'suspendida';
}

function normalizeValue(value: string | null | undefined, fallback: string) {
  const text = (value || '').trim();
  return text || fallback;
}

function normalizePedidoToken(value: string | null | undefined) {
  return (value || '')
    .trim()
    .toLowerCase()
    .replace(/_/g, '-')
    .replace(/\s+/g, '-');
}

function formatPedidoStatus(status: ApiPedido['status_operativo']) {
  return pedidoStatusLabels[status] || 'Pendiente';
}

function formatPedidoFase(fase: ApiPedido['fase']) {
  return pedidoFaseLabels[fase] || 'Sin fase';
}

function formatPedidoPrioridad(prioridad: ApiPedido['prioridad']) {
  return pedidoPrioridadLabels[prioridad] || 'Media';
}

function parsePedidoStatus(
  value: string | null | undefined,
  fallback: ApiPedido['status_operativo'],
): ApiPedido['status_operativo'] {
  const normalized = normalizePedidoToken(value);
  if (!normalized) return fallback;
  const byCode = (
    Object.keys(pedidoStatusLabels) as Array<ApiPedido['status_operativo']>
  ).find((item) => item === normalized);
  if (byCode) return byCode;
  const byLabel = (
    Object.entries(pedidoStatusLabels) as Array<
      [ApiPedido['status_operativo'], string]
    >
  ).find(([, label]) => normalizePedidoToken(label) === normalized);
  return byLabel?.[0] || fallback;
}

function parsePedidoFase(
  value: string | null | undefined,
  fallback: ApiPedido['fase'],
): ApiPedido['fase'] {
  const normalized = normalizePedidoToken(value);
  if (!normalized) return fallback;
  const byCode = (
    Object.keys(pedidoFaseLabels) as Array<ApiPedido['fase']>
  ).find((item) => item === normalized);
  if (byCode) return byCode;
  const byLabel = (
    Object.entries(pedidoFaseLabels) as Array<[ApiPedido['fase'], string]>
  ).find(([, label]) => normalizePedidoToken(label) === normalized);
  return byLabel?.[0] || fallback;
}

function parsePedidoPrioridad(
  value: string | null | undefined,
  fallback: ApiPedido['prioridad'],
): ApiPedido['prioridad'] {
  const normalized = normalizePedidoToken(value);
  if (!normalized) return fallback;
  const byCode = (
    Object.keys(pedidoPrioridadLabels) as Array<ApiPedido['prioridad']>
  ).find((item) => item === normalized);
  if (byCode) return byCode;
  const byLabel = (
    Object.entries(pedidoPrioridadLabels) as Array<
      [ApiPedido['prioridad'], string]
    >
  ).find(([, label]) => normalizePedidoToken(label) === normalized);
  return byLabel?.[0] || fallback;
}

function isPedidoStatusDadoDeBaja(value: string | null | undefined) {
  return parsePedidoStatus(value, 'por-confirmar') === 'dado-de-baja';
}

function isPedidoBajaRow(row: DataRow) {
  if (activeModuleKey.value !== 'pedidos') return false;
  return isPedidoStatusDadoDeBaja(String(row.estado || ''));
}

function mapClienteToItem(cliente: ApiCliente): ClienteItem {
  return {
    id: String(cliente.id),
    nombre: normalizeValue(cliente.nombre, 'Sin nombre'),
    ruc: normalizeValue(cliente.documento, '-'),
    contacto: normalizeValue(cliente.telefono, '-'),
    estado: cliente.activo ? 'Activo' : 'Inactivo',
  };
}

function mapCuentaToItem(cuenta: ApiCuenta): CuentaItem {
  return {
    id: String(cuenta.id),
    codigo: normalizeValue(cuenta.numero, '-'),
    nombre: normalizeValue(cuenta.nombre, '-'),
    direccion: (cuenta.direccion || '').trim(),
    distrito: (cuenta.distrito || '').trim(),
    latitud: Number.isFinite(cuenta.latitud) ? String(cuenta.latitud) : '',
    longitud: Number.isFinite(cuenta.longitud) ? String(cuenta.longitud) : '',
    contacto: (cuenta.contacto || '').trim(),
    telefono: (cuenta.telefono || '').trim(),
    estado: cuenta.activa ? 'Activa' : 'Suspendida',
  };
}

function formatCuentaCoordinates(cuenta: CuentaItem) {
  const lat = (cuenta.latitud || '').trim();
  const lon = (cuenta.longitud || '').trim();
  if (!lat || !lon) return '-';
  return `${lat}, ${lon}`;
}

function mapInventarioToDataRow(item: ApiInventario): DataRow {
  return {
    id: String(item.id),
    sku: normalizeValue(item.sku, '-'),
    descripcion: normalizeValue(item.descripcion, '-'),
    categoria: normalizeValue(item.categoria, '-'),
    stock: item.stock,
    almacen: normalizeValue(item.almacen, '-'),
  };
}

function mapTecnicoToDataRow(tecnico: ApiTecnico): DataRow {
  return {
    id: String(tecnico.id),
    tecnico: normalizeValue(tecnico.nombre, '-'),
    especialidad: normalizeValue(tecnico.especialidad, '-'),
    zona: normalizeValue(tecnico.zona, '-'),
    turno: tecnico.capacidad_diaria,
    estado: tecnico.activo ? 'Activo' : 'Inactivo',
  };
}

function mapPedidoToDataRow(pedido: ApiPedido): DataRow {
  return {
    id: String(pedido.id),
    ot: `OT-${String(pedido.id).padStart(4, '0')}`,
    cliente: normalizeValue(pedido.cliente_nombre, 'Sin cliente'),
    servicio: normalizeValue(
      pedido.tipo_servicio || pedido.titulo,
      'Sin servicio',
    ),
    fase: formatPedidoFase(pedido.fase),
    estado: formatPedidoStatus(pedido.status_operativo),
    prioridad: formatPedidoPrioridad(pedido.prioridad),
    fecha: normalizeValue(
      (pedido.fecha_programada || pedido.created_at || '').slice(0, 10),
      'Sin fecha',
    ),
  };
}

async function loadPedidosRows() {
  loadingPedidos.value = true;
  pedidosLoadError.value = '';

  try {
    const pedidos = await listPedidosWithOptions({ includeBajas: true });
    const nextIds = new Set<string>();
    pedidos.forEach((pedido) => {
      const id = String(pedido.id);
      nextIds.add(id);
      pedidoSnapshotById[id] = pedido;
    });
    Object.keys(pedidoSnapshotById).forEach((id) => {
      if (!nextIds.has(id)) {
        delete pedidoSnapshotById[id];
      }
    });
    genericRows.pedidos = pedidos.map(mapPedidoToDataRow);
  } catch (error) {
    pedidosLoadError.value = toErrorMessage(
      error,
      'No se pudo cargar pedidos desde backend.',
    );
  } finally {
    loadingPedidos.value = false;
  }
}

async function loadInventarioRows() {
  loadingInventario.value = true;
  inventarioLoadError.value = '';

  try {
    const inventario = await listInventario();
    genericRows.inventario = inventario.map(mapInventarioToDataRow);
  } catch (error) {
    inventarioLoadError.value = toErrorMessage(
      error,
      'No se pudo cargar inventario desde backend.',
    );
  } finally {
    loadingInventario.value = false;
  }
}

async function loadTecnicosRows() {
  loadingTecnicos.value = true;
  tecnicosLoadError.value = '';

  try {
    const tecnicos = await listTecnicos();
    genericRows['personal-campo'] = tecnicos.map(mapTecnicoToDataRow);
  } catch (error) {
    tecnicosLoadError.value = toErrorMessage(
      error,
      'No se pudo cargar personal de campo desde backend.',
    );
  } finally {
    loadingTecnicos.value = false;
  }
}

async function loadClientesCuentasRows() {
  loadingClientesCuentas.value = true;
  clientesCuentasLoadError.value = '';

  try {
    const [clientes, cuentas] = await Promise.all([
      listClientes(),
      listCuentas(),
    ]);

    clientesRows.value = clientes.map(mapClienteToItem);

    const grouped: Record<string, CuentaItem[]> = {};
    cuentas.forEach((cuenta) => {
      const mapped = mapCuentaToItem(cuenta);
      const clienteId = String(cuenta.cliente);
      if (!grouped[clienteId]) grouped[clienteId] = [];
      grouped[clienteId].push(mapped);
    });

    Object.keys(cuentasByCliente).forEach((key) => {
      delete cuentasByCliente[key];
    });
    Object.assign(cuentasByCliente, grouped);
  } catch (error) {
    clientesCuentasLoadError.value = toErrorMessage(
      error,
      'No se pudo cargar clientes/cuentas desde backend.',
    );
  } finally {
    loadingClientesCuentas.value = false;
  }
}

async function loadActiveModuleRows() {
  if (activeModuleKey.value === 'pedidos') {
    await loadPedidosRows();
    return;
  }
  if (activeModuleKey.value === 'inventario') {
    await loadInventarioRows();
    return;
  }
  if (activeModuleKey.value === 'personal-campo') {
    await loadTecnicosRows();
  }
}

function openModule(key: ModuleKey) {
  activeModuleKey.value = key;
  searchQuery.value = '';
  clientSearch.value = '';
  hideFeedback();
  closeDeleteDialog(true);
  if (key === 'cuentas-clientes') {
    goToClientesList();
    void loadClientesCuentasRows();
  }
  if (key === 'pedidos' || key === 'inventario' || key === 'personal-campo') {
    void loadActiveModuleRows();
  }
  cancelEdit();
}

function goBack() {
  activeModuleKey.value = null;
  searchQuery.value = '';
  clientSearch.value = '';
  hideFeedback();
  closeDeleteDialog(true);
  goToClientesList();
  cancelEdit();
}

function resetGenericForm() {
  Object.keys(formState).forEach((key) => {
    delete formState[key];
  });

  activeGenericColumns.value.forEach((column) => {
    formState[column.key] = '';
  });
}

function startCreateGeneric() {
  if (activeModuleKey.value === 'pedidos') {
    showError('La creacion de pedidos se realiza desde el modulo de Pedidos.');
    return;
  }

  editEntity.value = 'generic';
  editMode.value = 'create';
  editingId.value = null;
  resetGenericForm();
  isEditing.value = true;
}

function startEditGeneric(row: DataRow) {
  editEntity.value = 'generic';
  editMode.value = 'edit';
  editingId.value = String(row.id);
  resetGenericForm();
  activeGenericColumns.value.forEach((column) => {
    formState[column.key] = String(row[column.key] ?? '');
  });
  isEditing.value = true;
}

async function saveGenericRow() {
  if (!activeModuleKey.value || activeModuleKey.value === 'cuentas-clientes')
    return;

  const moduleKey = activeModuleKey.value as GenericModuleKey;

  if (moduleKey === 'pedidos') {
    pedidosLoadError.value = '';
    if (editMode.value === 'create') {
      showError('La creacion de pedidos no esta disponible en esta vista.');
      return;
    }
    if (!editingId.value) {
      showError('No se pudo identificar el pedido a actualizar.');
      return;
    }

    const currentPedido = pedidoSnapshotById[editingId.value];
    if (!currentPedido) {
      pedidosLoadError.value =
        'No se encontro el pedido en cache. Recarga la tabla.';
      showError(pedidosLoadError.value);
      return;
    }

    const nextStatus = parsePedidoStatus(
      formState.estado,
      currentPedido.status_operativo,
    );
    if (
      currentPedido.status_operativo === 'dado-de-baja' &&
      nextStatus !== currentPedido.status_operativo
    ) {
      const message = 'Un pedido dado de baja es final y no puede reactivarse.';
      pedidosLoadError.value = message;
      showError(message);
      return;
    }

    const payload = {
      fase: parsePedidoFase(formState.fase, currentPedido.fase),
      prioridad: parsePedidoPrioridad(
        formState.prioridad,
        currentPedido.prioridad,
      ),
      status_operativo: nextStatus,
    };

    try {
      await updatePedido(editingId.value, payload);
      await loadPedidosRows();
      cancelEdit();
      showSuccess('Pedido actualizado correctamente.');
    } catch (error) {
      const message = toErrorMessage(
        error,
        'No se pudo actualizar el pedido en backend.',
      );
      pedidosLoadError.value = message;
      showError(message);
    }
    return;
  }

  if (moduleKey === 'inventario') {
    inventarioLoadError.value = '';
    const isCreate = editMode.value === 'create';
    try {
      const payload = {
        sku: formState.sku?.trim() || '',
        descripcion: formState.descripcion?.trim() || '',
        categoria: formState.categoria?.trim() || '',
        stock: parseInteger(formState.stock, 0),
        almacen: formState.almacen?.trim() || 'principal',
      };

      if (editMode.value === 'create') {
        await createInventario(payload);
      } else if (editingId.value) {
        await updateInventario(editingId.value, payload);
      }

      await loadInventarioRows();
      cancelEdit();
      showSuccess(
        isCreate
          ? 'Item de inventario creado correctamente.'
          : 'Item de inventario actualizado correctamente.',
      );
    } catch (error) {
      const message = toErrorMessage(
        error,
        'No se pudo guardar inventario en backend.',
      );
      inventarioLoadError.value = message;
      showError(message);
    }
    return;
  }

  if (moduleKey === 'personal-campo') {
    tecnicosLoadError.value = '';
    const isCreate = editMode.value === 'create';
    try {
      const payload = {
        nombre: formState.tecnico?.trim() || '',
        especialidad: formState.especialidad?.trim() || '',
        zona: formState.zona?.trim() || '',
        capacidad_diaria: parseInteger(formState.turno, 5),
        activo: parseEstadoActivo(formState.estado, true),
      };

      if (editMode.value === 'create') {
        await createTecnico({
          ...payload,
          latitud_base: 0,
          longitud_base: 0,
        });
      } else if (editingId.value) {
        await updateTecnico(editingId.value, payload);
      }

      await loadTecnicosRows();
      cancelEdit();
      showSuccess(
        isCreate
          ? 'Tecnico creado correctamente.'
          : 'Tecnico actualizado correctamente.',
      );
    } catch (error) {
      const message = toErrorMessage(
        error,
        'No se pudo guardar personal de campo en backend.',
      );
      tecnicosLoadError.value = message;
      showError(message);
    }
    return;
  }

  const targetRows = genericRows[moduleKey];

  if (editMode.value === 'create') {
    const newRow: DataRow = {
      id: `${Date.now()}-${Math.floor(Math.random() * 1000)}`,
    };

    activeGenericColumns.value.forEach((column) => {
      newRow[column.key] = formState[column.key]?.trim() || '-';
    });

    targetRows.unshift(newRow);
  } else {
    const rowIndex = targetRows.findIndex((row) => row.id === editingId.value);
    if (rowIndex >= 0) {
      const updatedRow: DataRow = { ...targetRows[rowIndex] };
      activeGenericColumns.value.forEach((column) => {
        updatedRow[column.key] = formState[column.key]?.trim() || '-';
      });
      targetRows[rowIndex] = updatedRow;
    }
  }

  cancelEdit();
  showSuccess(
    editMode.value === 'create'
      ? 'Registro creado en vista local.'
      : 'Registro actualizado en vista local.',
  );
}

function askRemoveGenericRow(row: DataRow) {
  if (!activeModuleKey.value || activeModuleKey.value === 'cuentas-clientes')
    return;

  const moduleKey = activeModuleKey.value as GenericModuleKey;
  const primaryColumn = activeGenericColumns.value[0]?.key;
  const rowLabel = String(
    (primaryColumn && row[primaryColumn]) || row.id || 'registro',
  );

  if (moduleKey === 'inventario') {
    openDeleteDialog(
      'Eliminar item de inventario',
      `Se eliminara ${rowLabel}. Esta accion no se puede deshacer.`,
      async () => {
        await executeRemoveGenericRow(String(row.id), rowLabel);
      },
    );
    return;
  }

  if (moduleKey === 'personal-campo') {
    openDeleteDialog(
      'Eliminar tecnico',
      `Se eliminara ${rowLabel}. Esta accion no se puede deshacer.`,
      async () => {
        await executeRemoveGenericRow(String(row.id), rowLabel);
      },
    );
    return;
  }

  if (moduleKey === 'pedidos') {
    if (isPedidoBajaRow(row)) {
      showSuccess('Este pedido ya se encuentra dado de baja.');
      return;
    }

    openDeleteDialog(
      'Dar de baja pedido',
      `Se dara de baja ${rowLabel}. Esta accion es final y no se puede deshacer.`,
      async () => {
        await executeRemoveGenericRow(String(row.id), rowLabel);
      },
    );
    return;
  }

  openDeleteDialog(
    'Eliminar registro',
    `Se eliminara ${rowLabel}. Esta accion no se puede deshacer.`,
    async () => {
      await executeRemoveGenericRow(String(row.id), rowLabel);
    },
  );
}

async function executeRemoveGenericRow(id: string, rowLabel: string) {
  if (!activeModuleKey.value || activeModuleKey.value === 'cuentas-clientes')
    return;

  const moduleKey = activeModuleKey.value as GenericModuleKey;

  if (moduleKey === 'inventario') {
    inventarioLoadError.value = '';
    try {
      await deleteInventario(id);
      await loadInventarioRows();
      showSuccess(`Item de inventario ${rowLabel} eliminado correctamente.`);
    } catch (error) {
      const message = toErrorMessage(
        error,
        'No se pudo eliminar item de inventario.',
      );
      inventarioLoadError.value = message;
      showError(message);
      throw error;
    }
    return;
  }

  if (moduleKey === 'personal-campo') {
    tecnicosLoadError.value = '';
    try {
      await deleteTecnico(id);
      await loadTecnicosRows();
      showSuccess(`Tecnico ${rowLabel} eliminado correctamente.`);
    } catch (error) {
      const message = toErrorMessage(error, 'No se pudo eliminar tecnico.');
      tecnicosLoadError.value = message;
      showError(message);
      throw error;
    }
    return;
  }

  if (moduleKey === 'pedidos') {
    pedidosLoadError.value = '';
    try {
      await darBajaPedido(id);
      await loadPedidosRows();
      showSuccess(`Pedido ${rowLabel} dado de baja correctamente.`);
    } catch (error) {
      const message = toErrorMessage(
        error,
        'No se pudo dar de baja el pedido.',
      );
      pedidosLoadError.value = message;
      showError(message);
      throw error;
    }
    return;
  }

  genericRows[moduleKey] = genericRows[moduleKey].filter(
    (row) => row.id !== id,
  );
  showSuccess(`Registro ${rowLabel} eliminado en vista local.`);
}

function resetClienteForm() {
  clienteForm.id = '';
  clienteForm.nombre = '';
  clienteForm.ruc = '';
  clienteForm.contacto = '';
  clienteForm.estado = 'Activo';
}

function resetCuentaForm() {
  cuentaForm.id = '';
  cuentaForm.codigo = '';
  cuentaForm.nombre = '';
  cuentaForm.direccion = '';
  cuentaForm.distrito = '';
  cuentaForm.latitud = '';
  cuentaForm.longitud = '';
  cuentaForm.contacto = '';
  cuentaForm.telefono = '';
  cuentaForm.estado = 'Activa';
}

function startCreateCliente() {
  clienteFormMode.value = 'create';
  clienteEditingId.value = null;
  resetClienteForm();
  cuentasClientesView.value = 'cliente-form';
}

function startEditCliente(cliente: ClienteItem) {
  clienteFormMode.value = 'edit';
  clienteEditingId.value = cliente.id;
  clienteForm.id = cliente.id;
  clienteForm.nombre = cliente.nombre;
  clienteForm.ruc = cliente.ruc;
  clienteForm.contacto = cliente.contacto;
  clienteForm.estado = cliente.estado;
  cuentasClientesView.value = 'cliente-form';
}

function askRemoveClient(cliente: ClienteItem) {
  openDeleteDialog(
    'Eliminar cliente',
    `Se eliminara ${cliente.nombre} y sus cuentas asociadas. Esta accion no se puede deshacer.`,
    async () => {
      await executeRemoveClient(cliente.id, cliente.nombre);
    },
  );
}

async function executeRemoveClient(id: string, nombre: string) {
  clientesCuentasLoadError.value = '';
  try {
    await deleteCliente(id);
    await loadClientesCuentasRows();
    showSuccess(`Cliente ${nombre} eliminado correctamente.`);

    if (cuentaTargetClienteId.value === id) {
      goToClientesList();
    }
  } catch (error) {
    const message = toErrorMessage(
      error,
      'No se pudo eliminar cliente en backend.',
    );
    clientesCuentasLoadError.value = message;
    showError(message);
    throw error;
  }
}

function startCreateCuenta(clienteId: string) {
  cuentaFormMode.value = 'create';
  cuentaEditingId.value = null;
  cuentaTargetClienteId.value = clienteId;
  resetCuentaForm();
  cuentasClientesView.value = 'cuenta-form';
}

function startEditCuenta(clienteId: string, cuenta: CuentaItem) {
  cuentaFormMode.value = 'edit';
  cuentaEditingId.value = cuenta.id;
  cuentaTargetClienteId.value = clienteId;
  cuentaForm.id = cuenta.id;
  cuentaForm.codigo = cuenta.codigo;
  cuentaForm.nombre = cuenta.nombre;
  cuentaForm.direccion = cuenta.direccion;
  cuentaForm.distrito = cuenta.distrito;
  cuentaForm.latitud = cuenta.latitud;
  cuentaForm.longitud = cuenta.longitud;
  cuentaForm.contacto = cuenta.contacto;
  cuentaForm.telefono = cuenta.telefono;
  cuentaForm.estado = cuenta.estado;
  cuentasClientesView.value = 'cuenta-form';
}

function askRemoveCuenta(clienteId: string, cuenta: CuentaItem) {
  const cuentaLabel = `${cuenta.codigo} - ${cuenta.nombre}`;
  openDeleteDialog(
    'Eliminar cuenta',
    `Se eliminara ${cuentaLabel}. Esta accion no se puede deshacer.`,
    async () => {
      await executeRemoveCuenta(clienteId, cuenta.id, cuentaLabel);
    },
  );
}

async function executeRemoveCuenta(
  clienteId: string,
  id: string,
  cuentaLabel: string,
) {
  clientesCuentasLoadError.value = '';
  try {
    await deleteCuenta(id);
    await loadClientesCuentasRows();
    showSuccess(`Cuenta ${cuentaLabel} eliminada correctamente.`);
  } catch (error) {
    const message = toErrorMessage(
      error,
      'No se pudo eliminar cuenta en backend.',
    );
    clientesCuentasLoadError.value = message;
    showError(message);
    throw error;
  }

  if (
    cuentaTargetClienteId.value === clienteId &&
    cuentaEditingId.value === id
  ) {
    goToClientesList();
  }
}

async function saveClienteForm() {
  clientesCuentasLoadError.value = '';
  const isCreate = clienteFormMode.value === 'create';

  const payload = {
    nombre: clienteForm.nombre.trim(),
    documento: clienteForm.ruc.trim(),
    telefono: clienteForm.contacto.trim(),
    activo: clienteForm.estado === 'Activo',
  };

  try {
    if (clienteFormMode.value === 'create') {
      await createCliente({
        ...payload,
        correo: '',
        direccion: '',
      });
    } else if (clienteEditingId.value) {
      await updateCliente(clienteEditingId.value, payload);
    }

    await loadClientesCuentasRows();
    goToClientesList();
    showSuccess(
      isCreate
        ? 'Cliente creado correctamente.'
        : 'Cliente actualizado correctamente.',
    );
  } catch (error) {
    const message = toErrorMessage(
      error,
      'No se pudo guardar cliente en backend.',
    );
    clientesCuentasLoadError.value = message;
    showError(message);
  }
}

async function saveCuentaForm() {
  if (!cuentaTargetClienteId.value) return;

  clientesCuentasLoadError.value = '';
  const isCreate = cuentaFormMode.value === 'create';
  const latitud = parseCoordinate(cuentaForm.latitud, -90, 90);
  const longitud = parseCoordinate(cuentaForm.longitud, -180, 180);

  if (latitud === null || longitud === null) {
    const message =
      'Coordenadas invalidas. Usa latitud [-90, 90] y longitud [-180, 180].';
    clientesCuentasLoadError.value = message;
    showError(message);
    return;
  }

  const payload = {
    cliente: cuentaTargetClienteId.value,
    numero: cuentaForm.codigo.trim(),
    nombre: cuentaForm.nombre.trim(),
    direccion: cuentaForm.direccion.trim(),
    distrito: cuentaForm.distrito.trim(),
    latitud,
    longitud,
    contacto: cuentaForm.contacto.trim(),
    telefono: cuentaForm.telefono.trim(),
    activa: parseEstadoActivo(cuentaForm.estado, true),
  };

  try {
    if (cuentaFormMode.value === 'create') {
      await createCuenta({
        ...payload,
        tipo: 'otro',
      });
    } else if (cuentaEditingId.value) {
      await updateCuenta(cuentaEditingId.value, payload);
    }

    await loadClientesCuentasRows();
    goToClientesList();
    showSuccess(
      isCreate
        ? 'Cuenta creada correctamente.'
        : 'Cuenta actualizada correctamente.',
    );
  } catch (error) {
    const message = toErrorMessage(
      error,
      'No se pudo guardar cuenta en backend.',
    );
    clientesCuentasLoadError.value = message;
    showError(message);
  }
}

function getClientAccounts(clienteId: string) {
  return cuentasByCliente[clienteId] || [];
}

function getFilteredAccountsForClient(cliente: ClienteItem) {
  const accounts = getClientAccounts(cliente.id);
  const query = clientSearch.value.trim().toLowerCase();
  if (!query) return accounts;

  const matchesCliente = [
    cliente.nombre,
    cliente.ruc,
    cliente.contacto,
    cliente.estado,
  ]
    .join(' ')
    .toLowerCase()
    .includes(query);

  if (matchesCliente) return accounts;

  return accounts.filter((cuenta) =>
    [
      cuenta.codigo,
      cuenta.nombre,
      cuenta.direccion,
      cuenta.distrito,
      cuenta.latitud,
      cuenta.longitud,
      cuenta.contacto,
      cuenta.telefono,
      cuenta.estado,
    ]
      .join(' ')
      .toLowerCase()
      .includes(query),
  );
}

function goToClientesList() {
  cuentasClientesView.value = 'list';
  clienteFormMode.value = 'create';
  cuentaFormMode.value = 'create';
  clienteEditingId.value = null;
  cuentaEditingId.value = null;
  cuentaTargetClienteId.value = null;
  resetClienteForm();
  resetCuentaForm();
}

function cancelEdit() {
  isEditing.value = false;
  editingId.value = null;
  editEntity.value = 'generic';
  resetGenericForm();
  resetClienteForm();
  resetCuentaForm();
}

onMounted(() => {
  void Promise.all([
    loadPedidosRows(),
    loadClientesCuentasRows(),
    loadInventarioRows(),
    loadTecnicosRows(),
  ]);
});

onBeforeUnmount(() => {
  clearFeedbackTimer();
});
</script>

<style scoped>
.base-view {
  --bg-main: var(--color-surface);
  --bg-soft: var(--color-surface-2);
  --bg-soft-2: var(--color-surface-alt);
  --text-main: var(--color-text);
  --text-muted: var(--color-text-muted);
  --border: var(--color-border);
  --border-strong: var(--color-primary-500);
  --radius: 4px;

  display: grid;
  gap: 10px;
  min-height: calc(100dvh - 24px);
  grid-template-rows: 54px minmax(0, 1fr);
}

.card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: linear-gradient(180deg, var(--color-surface-2) 0%, var(--bg-main) 100%);
}

.crud-toast {
  position: fixed;
  right: 14px;
  bottom: 14px;
  width: min(360px, calc(100vw - 24px));
  border-radius: var(--radius);
  border: 1px solid var(--color-border);
  padding: 10px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  z-index: 20;
  box-shadow: 0 14px 34px rgba(2, 10, 18, 0.44);
}

.crud-toast.is-success {
  background: linear-gradient(160deg, rgba(6, 78, 59, 0.88), rgba(15, 118, 110, 0.75));
  border-color: rgba(52, 211, 153, 0.8);
}

.crud-toast.is-error {
  background: linear-gradient(160deg, rgba(127, 29, 29, 0.92), rgba(153, 27, 27, 0.72));
  border-color: rgba(252, 165, 165, 0.8);
}

.feedback-copy {
  display: grid;
  gap: 2px;
}

.feedback-copy strong {
  color: var(--color-surface-2);
  font-size: 0.82rem;
}

.feedback-copy span {
  color: var(--color-text-soft);
  font-size: 0.78rem;
}

.feedback-close {
  border: 1px solid rgba(203, 213, 225, 0.4);
  border-radius: var(--radius);
  background: rgba(15, 23, 42, 0.45);
  color: var(--color-text-soft);
  font-size: 0.74rem;
  padding: 5px 8px;
  cursor: pointer;
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

.base-head,
.crud-head {
  height: 54px;
  min-height: 54px;
  max-height: 54px;
  padding: 6px 12px;
  display: flex;
  align-items: center;
}

.crud-head {
  justify-content: space-between;
  gap: 10px;
}

h2,
h3,
p {
  margin: 0;
}

h2,
h3 {
  color: var(--text-main);
}

p,
small {
  color: var(--text-muted);
}

.cards-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(260px, 300px));
  justify-content: center;
  align-content: start;
  padding-top: 10px;
}

.module-card {
  width: 100%;
  height: 204px;
  min-height: 204px;
  max-height: 204px;
  padding: 14px;
  text-align: left;
  display: grid;
  gap: 8px;
  grid-template-rows: auto auto auto 1fr;
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease;
  box-shadow: 0 10px 24px rgba(2, 10, 18, 0.28);
}

.module-card:hover {
  border-color: var(--border-strong);
  transform: translateY(-2px);
}

.module-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.module-top h3 {
  font-size: 1.06rem;
  font-weight: 700;
}

.inventory-highlight {
  font-size: 1.28rem;
  font-weight: 900;
  letter-spacing: 0.04em;
  color: var(--color-surface-2);
}

.module-top span {
  border: 1px solid var(--color-text-muted);
  border-radius: 3px;
  padding: 2px 8px;
  color: var(--color-text-muted);
  font-size: 0.74rem;
}

.open-link {
  margin-top: 2px;
  padding-top: 8px;
  border-top: 1px solid rgba(220, 232, 245, 0.2);
  color: var(--color-text-soft);
  font-size: 0.8rem;
  align-self: end;
}

.crud-shell {
  display: grid;
  gap: 10px;
  grid-template-rows: auto minmax(0, 1fr);
  padding: 10px;
  overflow: hidden;
}

.clientes-stack {
  min-height: 0;
  display: grid;
  gap: 10px;
  overflow: auto;
  align-content: start;
}

.panel {
  border: 1px solid rgba(220, 232, 245, 0.2);
  background: rgba(9, 19, 31, 0.5);
  border-radius: var(--radius);
  padding: 10px;
  display: grid;
  gap: 8px;
  min-height: 0;
}

.toolbar-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.toolbar-inline-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.load-warning {
  color: #fecaca;
  border-color: rgba(239, 68, 68, 0.55);
  background: rgba(70, 18, 18, 0.45);
}

.clients-toolbar {
  align-items: flex-start;
}

.toolbar-copy {
  display: grid;
  gap: 4px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  width: min(100%, 760px);
}

.toolbar-actions .search {
  flex: 1;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.search,
input,
select {
  background: var(--color-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--color-text);
  padding: 8px 10px;
  font: inherit;
}

.search {
  width: 100%;
}

.btn {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 7px 10px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.primary {
  background: linear-gradient(120deg, #16a34a, #059669);
  border-color: #79e3c3;
  color: #f4fff8;
}

.btn.ghost {
  background: var(--bg-soft);
  color: var(--color-text-soft);
}

.btn.mini {
  padding: 5px 8px;
  font-size: 0.74rem;
  background: var(--bg-soft-2);
  color: var(--color-text-soft);
}

.btn.danger {
  border-color: #ef4444;
  color: #fecaca;
}

.btn.danger.solid {
  background: linear-gradient(160deg, rgba(185, 28, 28, 0.9), rgba(220, 38, 38, 0.75));
  color: #fff1f2;
}

.cliente-card {
  gap: 12px;
  background: linear-gradient(160deg, rgba(15, 32, 50, 0.88), rgba(10, 22, 35, 0.95));
}

.cliente-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.cliente-head p {
  margin-top: 4px;
}

.status-badge {
  border-radius: 999px;
  border: 1px solid var(--color-border);
  padding: 4px 10px;
  font-size: 0.74rem;
  font-weight: 700;
}

.status-badge.active {
  color: #baf6dc;
  border-color: #2f8f65;
  background: rgba(16, 185, 129, 0.12);
}

.status-badge.inactive {
  color: #f6d0d0;
  border-color: #a05a5a;
  background: rgba(239, 68, 68, 0.12);
}

.cliente-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  font-size: 0.86rem;
}

.cliente-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.cuentas-section {
  border-top: 1px solid rgba(220, 232, 245, 0.2);
  padding-top: 10px;
  display: grid;
  gap: 10px;
}

.cuentas-head h4 {
  margin: 0;
  color: var(--color-text-soft);
  font-size: 0.9rem;
}

.cuentas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 8px;
}

.cuenta-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: rgba(10, 21, 33, 0.85);
  padding: 10px;
  display: grid;
  gap: 8px;
}

.cuenta-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.cuenta-top span {
  border-radius: 3px;
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: 0.72rem;
  padding: 2px 7px;
}

.cuenta-address {
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.cuenta-meta {
  display: grid;
  gap: 3px;
  color: var(--color-text-muted);
  font-size: 0.78rem;
}

.state-pill {
  width: fit-content;
  border-radius: 999px;
  padding: 3px 8px;
  border: 1px solid var(--color-border);
  font-weight: 700;
}

.state-pill.ok {
  color: #baf6dc;
  border-color: #2f8f65;
  background: rgba(16, 185, 129, 0.12);
}

.state-pill.warn {
  color: #fde8b9;
  border-color: #a27226;
  background: rgba(245, 158, 11, 0.14);
}

.cuenta-actions {
  display: flex;
  gap: 6px;
}

.empty-cuentas,
.empty-clients {
  display: grid;
  gap: 8px;
  place-items: start;
}

.standalone-form {
  max-width: 980px;
  width: 100%;
  justify-self: center;
}

.form-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.table-wrap {
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: rgba(10, 21, 34, 0.65);
  min-height: 0;
}

table {
  width: 100%;
  min-width: 680px;
  border-collapse: collapse;
}

th,
td {
  padding: 8px;
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  color: var(--color-text-soft);
}

th {
  color: var(--color-text-soft);
  font-weight: 600;
  background: rgba(19, 38, 59, 0.5);
}

.actions {
  width: 156px;
}

.action-buttons {
  display: flex;
  gap: 6px;
}

.row-clickable {
  cursor: pointer;
}

.row-clickable.selected {
  background: rgba(32, 86, 132, 0.25);
}

.empty-row {
  text-align: center;
  color: var(--color-text-muted);
}

.editor {
  padding: 10px;
  display: grid;
  gap: 10px;
}

.editor-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

label {
  display: grid;
  gap: 4px;
}

label span {
  color: var(--color-text-muted);
  font-size: 0.78rem;
}

.editor-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.delete-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(2, 6, 23, 0.66);
  display: grid;
  place-items: center;
  z-index: 12;
  padding: 12px;
}

.delete-modal {
  width: min(430px, 100%);
  padding: 14px;
  display: grid;
  gap: 12px;
}

.delete-modal-head {
  display: grid;
  gap: 6px;
}

.delete-modal-head p {
  color: var(--color-text-soft);
}

.delete-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 1200px) {
  .cards-grid {
    grid-template-columns: repeat(auto-fit, minmax(240px, 280px));
  }

  .module-card {
    height: 190px;
    min-height: 190px;
    max-height: 190px;
  }

  .editor-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 920px) {
  .cliente-meta {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 780px) {
  .cards-grid,
  .editor-grid {
    grid-template-columns: 1fr;
  }

  .module-card {
    max-width: 100%;
    height: 178px;
    min-height: 178px;
    max-height: 178px;
  }

  .crud-head,
  .toolbar-panel,
  .panel-head,
  .toolbar-actions,
  .form-head,
  .delete-modal-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .cuentas-grid {
    grid-template-columns: 1fr;
  }
}
</style>
