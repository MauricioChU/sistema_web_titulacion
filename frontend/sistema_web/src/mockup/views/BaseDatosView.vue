<template>
  <section class="base-view">
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
              <button class="btn primary" @click="startCreateCliente">Crear nuevo cliente</button>
            </div>
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
                <button class="btn mini danger" @click="removeClient(cliente.id)">Eliminar cliente</button>
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
                    <p class="cuenta-address">{{ cuenta.direccion }}</p>
                    <div class="cuenta-meta">
                      <span>Contacto: {{ cuenta.contacto }}</span>
                      <span>Telefono: {{ cuenta.telefono }}</span>
                      <span class="state-pill" :class="cuenta.estado === 'Activa' ? 'ok' : 'warn'">{{ cuenta.estado }}</span>
                    </div>
                    <div class="cuenta-actions">
                      <button class="btn mini" @click="startEditCuenta(cliente.id, cuenta)">Editar</button>
                      <button class="btn mini danger" @click="removeCuenta(cliente.id, cuenta.id)">Eliminar</button>
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
          <button class="btn primary" @click="startCreateGeneric">Nuevo registro</button>
        </div>

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
                    <button class="btn mini" @click="startEditGeneric(row)">Editar</button>
                    <button class="btn mini danger" @click="removeGenericRow(Number(row.id))">Eliminar</button>
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
              <input v-model="formState[column.key]" type="text" :placeholder="column.label" required />
            </label>
          </div>
          <div class="editor-actions">
            <button type="button" class="btn ghost" @click="cancelEdit">Cancelar</button>
            <button type="submit" class="btn primary">Guardar</button>
          </div>
        </form>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';

type ModuleKey = 'inventario' | 'cuentas-clientes' | 'personal-campo' | 'reportes';
type GenericModuleKey = 'inventario' | 'personal-campo' | 'reportes';
type EditMode = 'create' | 'edit';
type CuentasClientesView = 'list' | 'cliente-form' | 'cuenta-form';
type EditEntity = 'generic' | 'cliente' | 'cuenta';

interface ColumnDef {
  key: string;
  label: string;
}

interface DataRow {
  id: number;
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
  id: number;
  nombre: string;
  ruc: string;
  contacto: string;
  estado: 'Activo' | 'Inactivo';
}

interface CuentaItem {
  id: number;
  codigo: string;
  nombre: string;
  direccion: string;
  contacto: string;
  telefono: string;
  estado: 'Activa' | 'Suspendida';
}

const modules: ModuleConfig[] = [
  {
    key: 'inventario',
    code: 'INV',
    title: 'Inventario',
    description: 'Control de stock, almacenes y reposicion.',
    metrics: '1248 items activos',
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
    metrics: '312 cuentas registradas',
  },
  {
    key: 'personal-campo',
    code: 'PCF',
    title: 'Personal de campo',
    description: 'Tecnicos, especialidades y disponibilidad.',
    metrics: '76 tecnicos habilitados',
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
    metrics: '24 reportes disponibles',
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
  inventario: [
    { id: 1, sku: 'INV-1001', descripcion: 'Cable UTP Cat6', categoria: 'Material', stock: 245, almacen: 'Lima Centro' },
    { id: 2, sku: 'INV-1002', descripcion: 'Patch panel 48', categoria: 'Equipo', stock: 32, almacen: 'San Isidro' },
    { id: 3, sku: 'INV-1003', descripcion: 'Guante dielectrico', categoria: 'EPP', stock: 88, almacen: 'Surco' },
  ],
  'personal-campo': [
    { id: 1, tecnico: 'Luis Rojas', especialidad: 'Electrico', zona: 'Lima Norte', turno: 'Manana', estado: 'Disponible' },
    { id: 2, tecnico: 'Carlos Palacios', especialidad: 'UPS', zona: 'Lima Este', turno: 'Tarde', estado: 'En ruta' },
    { id: 3, tecnico: 'Martha Pino', especialidad: 'Cableado', zona: 'Lima Centro', turno: 'Noche', estado: 'Disponible' },
  ],
  reportes: [
    { id: 1, reporte: 'SLA por cliente', frecuencia: 'Semanal', propietario: 'Operacion', formato: 'Dashboard', estado: 'Activo' },
    { id: 2, reporte: 'Costos por OT', frecuencia: 'Diario', propietario: 'Finanzas', formato: 'Excel', estado: 'Activo' },
    { id: 3, reporte: 'Productividad tecnico', frecuencia: 'Mensual', propietario: 'Jefatura campo', formato: 'PDF', estado: 'Activo' },
  ],
});

const clientesRows = ref<ClienteItem[]>([
  { id: 1, nombre: 'Clinica Miraflores', ruc: '20548796321', contacto: 'Laura Medina', estado: 'Activo' },
  { id: 2, nombre: 'Condominio Brisas', ruc: '20600154789', contacto: 'Marta Solis', estado: 'Activo' },
  { id: 3, nombre: 'Retail Norte SAC', ruc: '20114589632', contacto: 'Rosa Calderon', estado: 'Inactivo' },
]);

const cuentasByCliente = reactive<Record<number, CuentaItem[]>>({
  1: [
    { id: 1, codigo: 'CUE-1001', nombre: 'Sede Principal', direccion: 'Av. Arequipa 1001', contacto: 'Laura Medina', telefono: '987123111', estado: 'Activa' },
    { id: 2, codigo: 'CUE-1002', nombre: 'Sede Emergencias', direccion: 'Jr. Las Flores 221', contacto: 'Pedro Chavez', telefono: '987123222', estado: 'Activa' },
  ],
  2: [
    { id: 1, codigo: 'CUE-2001', nombre: 'Torre A', direccion: 'Calle Parque Norte 450', contacto: 'Marta Solis', telefono: '965774100', estado: 'Activa' },
  ],
  3: [
    { id: 1, codigo: 'CUE-3001', nombre: 'Local San Isidro', direccion: 'Av. Rivera Navarrete 3201', contacto: 'Rosa Calderon', telefono: '955441990', estado: 'Suspendida' },
  ],
});

const activeModuleKey = ref<ModuleKey | null>(null);
const searchQuery = ref('');
const clientSearch = ref('');
const cuentasClientesView = ref<CuentasClientesView>('list');
const clienteFormMode = ref<EditMode>('create');
const cuentaFormMode = ref<EditMode>('create');
const clienteEditingId = ref<number | null>(null);
const cuentaEditingId = ref<number | null>(null);
const cuentaTargetClienteId = ref<number | null>(null);

const isEditing = ref(false);
const editMode = ref<EditMode>('create');
const editEntity = ref<EditEntity>('generic');
const editingId = ref<number | null>(null);
const formState = reactive<Record<string, string>>({});

const clienteForm = reactive<ClienteItem>({
  id: 0,
  nombre: '',
  ruc: '',
  contacto: '',
  estado: 'Activo',
});

const cuentaForm = reactive<CuentaItem>({
  id: 0,
  codigo: '',
  nombre: '',
  direccion: '',
  contacto: '',
  telefono: '',
  estado: 'Activa',
});

const activeModule = computed(() => modules.find((module) => module.key === activeModuleKey.value) || null);

const activeGenericColumns = computed(() => activeModule.value?.columns || []);

const activeGenericRows = computed(() => {
  if (!activeModuleKey.value || activeModuleKey.value === 'cuentas-clientes') return [];
  return genericRows[activeModuleKey.value as GenericModuleKey];
});

const filteredGenericRows = computed(() => {
  const query = searchQuery.value.trim().toLowerCase();
  if (!query) return activeGenericRows.value;

  return activeGenericRows.value.filter((row) =>
    Object.values(row).some((value) => String(value).toLowerCase().includes(query))
  );
});

const filteredClients = computed(() => {
  const query = clientSearch.value.trim().toLowerCase();
  if (!query) return clientesRows.value;

  return clientesRows.value.filter((cliente) => {
    const matchesCliente = [cliente.nombre, cliente.ruc, cliente.contacto, cliente.estado]
      .join(' ')
      .toLowerCase()
      .includes(query);

    if (matchesCliente) return true;
    return getClientAccounts(cliente.id).some((cuenta) =>
      [cuenta.codigo, cuenta.nombre, cuenta.direccion, cuenta.contacto, cuenta.telefono, cuenta.estado]
        .join(' ')
        .toLowerCase()
        .includes(query)
    );
  });
});

const cuentaTargetClienteName = computed(() =>
  clientesRows.value.find((cliente) => cliente.id === cuentaTargetClienteId.value)?.nombre || ''
);

function openModule(key: ModuleKey) {
  activeModuleKey.value = key;
  searchQuery.value = '';
  clientSearch.value = '';
  if (key === 'cuentas-clientes') {
    goToClientesList();
  }
  cancelEdit();
}

function goBack() {
  activeModuleKey.value = null;
  searchQuery.value = '';
  clientSearch.value = '';
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
  editEntity.value = 'generic';
  editMode.value = 'create';
  editingId.value = null;
  resetGenericForm();
  isEditing.value = true;
}

function startEditGeneric(row: DataRow) {
  editEntity.value = 'generic';
  editMode.value = 'edit';
  editingId.value = Number(row.id);
  resetGenericForm();
  activeGenericColumns.value.forEach((column) => {
    formState[column.key] = String(row[column.key] ?? '');
  });
  isEditing.value = true;
}

function saveGenericRow() {
  if (!activeModuleKey.value || activeModuleKey.value === 'cuentas-clientes') return;

  const targetRows = genericRows[activeModuleKey.value as GenericModuleKey];

  if (editMode.value === 'create') {
    const nextId = targetRows.length ? Math.max(...targetRows.map((row) => Number(row.id))) + 1 : 1;
    const newRow: DataRow = { id: nextId };

    activeGenericColumns.value.forEach((column) => {
      newRow[column.key] = formState[column.key]?.trim() || '-';
    });

    targetRows.unshift(newRow);
  } else {
    const rowIndex = targetRows.findIndex((row) => Number(row.id) === editingId.value);
    if (rowIndex >= 0) {
      const updatedRow: DataRow = { ...targetRows[rowIndex] };
      activeGenericColumns.value.forEach((column) => {
        updatedRow[column.key] = formState[column.key]?.trim() || '-';
      });
      targetRows[rowIndex] = updatedRow;
    }
  }

  cancelEdit();
}

function removeGenericRow(id: number) {
  if (!activeModuleKey.value || activeModuleKey.value === 'cuentas-clientes') return;
  genericRows[activeModuleKey.value as GenericModuleKey] = genericRows[activeModuleKey.value as GenericModuleKey]
    .filter((row) => Number(row.id) !== id);
}

function resetClienteForm() {
  clienteForm.id = 0;
  clienteForm.nombre = '';
  clienteForm.ruc = '';
  clienteForm.contacto = '';
  clienteForm.estado = 'Activo';
}

function resetCuentaForm() {
  cuentaForm.id = 0;
  cuentaForm.codigo = '';
  cuentaForm.nombre = '';
  cuentaForm.direccion = '';
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

function removeClient(id: number) {
  clientesRows.value = clientesRows.value.filter((cliente) => cliente.id !== id);
  delete cuentasByCliente[id];

  if (cuentaTargetClienteId.value === id) {
    goToClientesList();
  }
}

function startCreateCuenta(clienteId: number) {
  cuentaFormMode.value = 'create';
  cuentaEditingId.value = null;
  cuentaTargetClienteId.value = clienteId;
  resetCuentaForm();
  cuentasClientesView.value = 'cuenta-form';
}

function startEditCuenta(clienteId: number, cuenta: CuentaItem) {
  cuentaFormMode.value = 'edit';
  cuentaEditingId.value = cuenta.id;
  cuentaTargetClienteId.value = clienteId;
  cuentaForm.id = cuenta.id;
  cuentaForm.codigo = cuenta.codigo;
  cuentaForm.nombre = cuenta.nombre;
  cuentaForm.direccion = cuenta.direccion;
  cuentaForm.contacto = cuenta.contacto;
  cuentaForm.telefono = cuenta.telefono;
  cuentaForm.estado = cuenta.estado;
  cuentasClientesView.value = 'cuenta-form';
}

function removeCuenta(clienteId: number, id: number) {
  cuentasByCliente[clienteId] = (cuentasByCliente[clienteId] || [])
    .filter((cuenta) => cuenta.id !== id);
}

function saveClienteForm() {
  if (clienteFormMode.value === 'create') {
    const nextId = clientesRows.value.length ? Math.max(...clientesRows.value.map((cliente) => cliente.id)) + 1 : 1;
    const newCliente: ClienteItem = {
      id: nextId,
      nombre: clienteForm.nombre.trim(),
      ruc: clienteForm.ruc.trim(),
      contacto: clienteForm.contacto.trim(),
      estado: clienteForm.estado,
    };
    clientesRows.value.unshift(newCliente);
    cuentasByCliente[nextId] = cuentasByCliente[nextId] || [];
  } else {
    const index = clientesRows.value.findIndex((cliente) => cliente.id === clienteEditingId.value);
    if (index >= 0) {
      clientesRows.value[index] = {
        id: clientesRows.value[index].id,
        nombre: clienteForm.nombre.trim(),
        ruc: clienteForm.ruc.trim(),
        contacto: clienteForm.contacto.trim(),
        estado: clienteForm.estado,
      };
    }
  }

  goToClientesList();
}

function saveCuentaForm() {
  if (!cuentaTargetClienteId.value) return;

  const target = cuentasByCliente[cuentaTargetClienteId.value] || [];

  if (cuentaFormMode.value === 'create') {
    const nextId = target.length ? Math.max(...target.map((cuenta) => cuenta.id)) + 1 : 1;
    const newCuenta: CuentaItem = {
      id: nextId,
      codigo: cuentaForm.codigo.trim(),
      nombre: cuentaForm.nombre.trim(),
      direccion: cuentaForm.direccion.trim(),
      contacto: cuentaForm.contacto.trim(),
      telefono: cuentaForm.telefono.trim(),
      estado: cuentaForm.estado,
    };
    target.unshift(newCuenta);
  } else {
    const index = target.findIndex((cuenta) => cuenta.id === cuentaEditingId.value);
    if (index >= 0) {
      target[index] = {
        id: target[index].id,
        codigo: cuentaForm.codigo.trim(),
        nombre: cuentaForm.nombre.trim(),
        direccion: cuentaForm.direccion.trim(),
        contacto: cuentaForm.contacto.trim(),
        telefono: cuentaForm.telefono.trim(),
        estado: cuentaForm.estado,
      };
    }
  }

  cuentasByCliente[cuentaTargetClienteId.value] = target;
  goToClientesList();
}

function getClientAccounts(clienteId: number) {
  return cuentasByCliente[clienteId] || [];
}

function getFilteredAccountsForClient(cliente: ClienteItem) {
  const accounts = getClientAccounts(cliente.id);
  const query = clientSearch.value.trim().toLowerCase();
  if (!query) return accounts;

  const matchesCliente = [cliente.nombre, cliente.ruc, cliente.contacto, cliente.estado]
    .join(' ')
    .toLowerCase()
    .includes(query);

  if (matchesCliente) return accounts;

  return accounts.filter((cuenta) =>
    [cuenta.codigo, cuenta.nombre, cuenta.direccion, cuenta.contacto, cuenta.telefono, cuenta.estado]
      .join(' ')
      .toLowerCase()
      .includes(query)
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
</script>

<style scoped>
.base-view {
  --bg-main: #0f1c2b;
  --bg-soft: #13263b;
  --bg-soft-2: #102235;
  --text-main: #e9f1fb;
  --text-muted: #9db3cb;
  --border: #4a6078;
  --border-strong: #dce8f5;
  --radius: 4px;

  display: grid;
  gap: 10px;
  min-height: calc(100dvh - 24px);
  grid-template-rows: 54px minmax(0, 1fr);
}

.card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: linear-gradient(180deg, #122235 0%, var(--bg-main) 100%);
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
  color: #f5fbff;
}

.module-top span {
  border: 1px solid #6f88a6;
  border-radius: 3px;
  padding: 2px 8px;
  color: #bbd2ea;
  font-size: 0.74rem;
}

.open-link {
  margin-top: 2px;
  padding-top: 8px;
  border-top: 1px solid rgba(220, 232, 245, 0.2);
  color: #d9e8f8;
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
  background: #0b1827;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: #e5eef8;
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
  color: #d8e7f7;
}

.btn.mini {
  padding: 5px 8px;
  font-size: 0.74rem;
  background: var(--bg-soft-2);
  color: #d8e7f7;
}

.btn.danger {
  border-color: #ef4444;
  color: #fecaca;
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
  border: 1px solid #3f5873;
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
  color: #c9daed;
  font-size: 0.9rem;
}

.cuentas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 8px;
}

.cuenta-card {
  border: 1px solid #39506a;
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
  border: 1px solid #445f7d;
  color: #b7d0ea;
  font-size: 0.72rem;
  padding: 2px 7px;
}

.cuenta-address {
  color: #bed1e3;
  font-size: 0.85rem;
}

.cuenta-meta {
  display: grid;
  gap: 3px;
  color: #aac3db;
  font-size: 0.78rem;
}

.state-pill {
  width: fit-content;
  border-radius: 999px;
  padding: 3px 8px;
  border: 1px solid #3f5873;
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
  border-bottom: 1px solid #384c62;
  text-align: left;
  color: #d5e4f3;
}

th {
  color: #c0d2e6;
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
  color: #abc3db;
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
  color: #b8cee6;
  font-size: 0.78rem;
}

.editor-actions {
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
  .form-head {
    flex-direction: column;
    align-items: stretch;
  }

  .cuentas-grid {
    grid-template-columns: 1fr;
  }
}
</style>
