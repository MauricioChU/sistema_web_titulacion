<template>
  <div class="bd-view">
    <!-- Toast feedback -->
    <transition name="toast-fade">
      <div v-if="toast.show" class="bd-toast" :class="toast.type">
        <strong>{{ toast.type === 'success' ? '✓' : '✕' }}</strong>
        <span>{{ toast.msg }}</span>
        <button @click="toast.show = false">✕</button>
      </div>
    </transition>

    <!-- Módulo seleccionado -->
    <template v-if="activeModule">
      <header class="bd-header">
        <div>
          <h2>{{ activeModule.title }}</h2>
          <p>{{ activeModule.desc }}</p>
        </div>
        <div class="header-actions">
          <button v-if="activeModule.key !== 'cuentas-clientes'" class="btn-primary" @click="() => openCreate()">
            + Nuevo registro
          </button>
          <button class="btn-ghost" @click="activeModule = null">← Volver</button>
        </div>
      </header>

      <!-- ══════════ INVENTARIO ══════════ -->
      <div v-if="activeModule.key === 'inventario'" class="bd-table-card">
        <div class="table-toolbar">
          <input v-model="searchInv" type="search" placeholder="Buscar ítem..." class="bd-search" />
          <select v-model="filterCat" class="bd-select">
            <option value="">Todas las categorías</option>
            <option value="epp">EPPs</option>
            <option value="material">Materiales</option>
            <option value="herramienta">Herramientas</option>
            <option value="otro">Otro</option>
          </select>
        </div>
        <div v-if="loadingInv" class="bd-loading">Cargando...</div>
        <table v-else class="bd-table">
          <thead>
            <tr><th>SKU</th><th>Nombre</th><th>Categoría</th><th>Stock</th><th>Mín.</th><th>Precio unit.</th><th>Unidad</th><th>Estado</th><th></th></tr>
          </thead>
          <tbody>
            <tr v-if="filteredInv.length === 0"><td colspan="9" class="td-empty">Sin ítems.</td></tr>
            <tr v-for="i in filteredInv" :key="i.id" :class="{ 'row-low': i.stock_disponible <= i.stock_minimo }">
              <td><code>{{ i.sku }}</code></td>
              <td>{{ i.nombre }}</td>
              <td><span class="cat-badge" :class="`cat-${i.categoria}`">{{ i.categoria }}</span></td>
              <td><strong :class="{ 'text-danger': i.stock_disponible <= i.stock_minimo }">{{ i.stock_disponible }}</strong></td>
              <td>{{ i.stock_minimo }}</td>
              <td>S/ {{ i.precio_unitario.toFixed(2) }}</td>
              <td>{{ i.unidad }}</td>
              <td><span class="status-dot" :class="i.activo ? 'dot-green' : 'dot-gray'">{{ i.activo ? 'Activo' : 'Inactivo' }}</span></td>
              <td class="td-actions">
                <button class="btn-icon" @click="openEdit('inv', i)">✎</button>
                <button class="btn-icon danger" @click="confirmDelete('inv', i.id, i.nombre)">✕</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ══════════ CLIENTES / CUENTAS ══════════ -->
      <div v-else-if="activeModule.key === 'cuentas-clientes'" class="bd-cc">
        <div class="bd-cc-header">
          <input v-model="searchCli" type="search" placeholder="Buscar cliente..." class="bd-search" />
          <button class="btn-primary" @click="openCreate('cliente')">+ Nuevo cliente</button>
        </div>
        <div v-if="loadingCli" class="bd-loading">Cargando...</div>
        <div v-else class="clientes-list">
          <div v-if="filteredClientes.length === 0" class="bd-empty">Sin clientes.</div>
          <div v-for="cli in filteredClientes" :key="cli.id" class="cli-card">
            <div class="cli-head">
              <div>
                <strong>{{ cli.nombre }}</strong>
                <small>RUC: {{ cli.ruc }}</small>
              </div>
              <div class="cli-actions">
                <button class="btn-sm" @click="openCreate('cuenta', cli.id)">+ Cuenta</button>
                <button class="btn-icon" @click="openEdit('cliente', cli)">✎</button>
                <button class="btn-icon danger" @click="confirmDelete('cliente', cli.id, cli.nombre)">✕</button>
              </div>
            </div>
            <div class="cli-info">
              <span>{{ cli.telefono }}</span>
              <span>{{ cli.correo }}</span>
              <span>{{ cli.direccion }}</span>
            </div>
            <!-- Cuentas del cliente -->
            <div class="cuentas-list">
              <div v-if="cuentasByCliente[cli.id]?.length === 0" class="cuenta-empty">Sin cuentas.</div>
              <div v-for="cu in cuentasByCliente[cli.id] || []" :key="cu.id" class="cuenta-item">
                <div class="cuenta-info">
                  <span class="cuenta-num">{{ cu.numero }}</span>
                  <strong>{{ cu.nombre }}</strong>
                  <small>{{ cu.distrito }} — {{ cu.contacto }}</small>
                </div>
                <div class="cuenta-actions">
                  <button class="btn-icon" @click="openEdit('cuenta', cu)">✎</button>
                  <button class="btn-icon danger" @click="confirmDelete('cuenta', cu.id, cu.nombre)">✕</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ══════════ TÉCNICOS (PERSONAL DE CAMPO) ══════════ -->
      <div v-else-if="activeModule.key === 'personal-campo'" class="bd-table-card">
        <div class="table-toolbar">
          <input v-model="searchTec" type="search" placeholder="Buscar técnico..." class="bd-search" />
        </div>
        <div v-if="loadingTec" class="bd-loading">Cargando...</div>
        <table v-else class="bd-table">
          <thead>
            <tr><th>Nombre</th><th>Especialidad</th><th>Zona</th><th>Teléfono</th><th>Pedidos activos</th><th>Estado</th><th></th></tr>
          </thead>
          <tbody>
            <tr v-if="filteredTecnicos.length === 0"><td colspan="7" class="td-empty">Sin técnicos.</td></tr>
            <tr v-for="t in filteredTecnicos" :key="t.id">
              <td><strong>{{ t.nombre }}</strong></td>
              <td>{{ t.especialidad }}</td>
              <td>{{ t.zona }}</td>
              <td>{{ t.telefono }}</td>
              <td><span class="num-pill">{{ t.pedidos_activos }}</span></td>
              <td><span class="status-dot" :class="t.activo ? 'dot-green' : 'dot-gray'">{{ t.activo ? 'Activo' : 'Inactivo' }}</span></td>
              <td class="td-actions">
                <button class="btn-icon" @click="openEdit('tec', t)">✎</button>
                <button class="btn-icon danger" @click="confirmDelete('tec', t.id, t.nombre)">✕</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ══════════ USUARIOS ══════════ -->
      <div v-else-if="activeModule.key === 'usuarios'" class="bd-table-card">
        <div class="table-toolbar">
          <input v-model="searchUsr" type="search" placeholder="Buscar usuario..." class="bd-search" />
          <select v-model="filterRol" class="bd-select">
            <option value="">Todos los roles</option>
            <option value="admin">Admin</option>
            <option value="coordinador">Coordinador</option>
            <option value="tecnico">Técnico</option>
          </select>
        </div>
        <div v-if="loadingUsr" class="bd-loading">Cargando...</div>
        <table v-else class="bd-table">
          <thead>
            <tr><th>Usuario</th><th>Nombre</th><th>Email</th><th>Rol</th><th>Privilegio</th><th>Estado</th><th></th></tr>
          </thead>
          <tbody>
            <tr v-if="filteredUsuarios.length === 0"><td colspan="7" class="td-empty">Sin usuarios.</td></tr>
            <tr v-for="u in filteredUsuarios" :key="u.id">
              <td><code>{{ u.username }}</code></td>
              <td>{{ u.nombre_completo }}</td>
              <td>{{ u.email }}</td>
              <td><span class="rol-badge" :class="`rol-${u.rol}`">{{ u.rol }}</span></td>
              <td>{{ u.privilegio || '—' }}</td>
              <td><span class="status-dot" :class="u.activo ? 'dot-green' : 'dot-gray'">{{ u.activo ? 'Activo' : 'Inactivo' }}</span></td>
              <td class="td-actions">
                <button class="btn-icon" @click="openEdit('usr', u)">✎</button>
                <button class="btn-icon danger" @click="confirmDelete('usr', u.id, u.username)">✕</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- ══════════ GRID DE MÓDULOS ══════════ -->
    <template v-else>
      <header class="bd-header">
        <div>
          <h2>Base de datos</h2>
          <p>Administración de entidades del sistema</p>
        </div>
      </header>
      <div class="modules-grid">
        <button v-for="m in visibleModules" :key="m.key" class="module-card" @click="openModule(m)">
          <div class="module-icon">{{ m.icon }}</div>
          <div class="module-info">
            <strong>{{ m.title }}</strong>
            <p>{{ m.desc }}</p>
          </div>
          <span class="module-arrow">→</span>
        </button>
      </div>
    </template>

    <!-- ══════════ MODAL CREAR / EDITAR ══════════ -->
    <div v-if="modal.open" class="modal-overlay" @click.self="modal.open = false">
      <div class="modal">
        <div class="modal-head">
          <h3>{{ modal.mode === 'create' ? 'Nuevo' : 'Editar' }} {{ modal.entityLabel }}</h3>
          <button class="modal-close" @click="modal.open = false">✕</button>
        </div>

        <!-- Inventario form -->
        <form v-if="modal.entity === 'inv'" @submit.prevent="saveInv" class="modal-form">
          <div class="form-row">
            <label>SKU * <input v-model="invForm.sku" required /></label>
            <label>Nombre * <input v-model="invForm.nombre" required /></label>
          </div>
          <div class="form-row">
            <label>Categoría *
              <select v-model="invForm.categoria" required>
                <option value="epp">EPP</option>
                <option value="material">Material</option>
                <option value="herramienta">Herramienta</option>
                <option value="otro">Otro</option>
              </select>
            </label>
            <label>Unidad * <input v-model="invForm.unidad" required placeholder="unidad, rollo, caja..." /></label>
          </div>
          <label>Descripción <textarea v-model="invForm.descripcion" rows="2"></textarea></label>
          <div class="form-row">
            <label>Stock disponible * <input v-model.number="invForm.stock_disponible" type="number" min="0" required /></label>
            <label>Stock mínimo * <input v-model.number="invForm.stock_minimo" type="number" min="0" required /></label>
          </div>
          <div class="form-row">
            <label>Precio unitario (S/) * <input v-model.number="invForm.precio_unitario" type="number" min="0" step="0.01" required /></label>
            <label>
              Activo
              <select v-model="invForm.activo">
                <option :value="true">Sí</option>
                <option :value="false">No</option>
              </select>
            </label>
          </div>
          <p v-if="modal.error" class="form-error">{{ modal.error }}</p>
          <div class="modal-actions">
            <button type="button" class="btn-ghost" @click="modal.open = false">Cancelar</button>
            <button type="submit" class="btn-primary" :disabled="modal.saving">{{ modal.saving ? 'Guardando...' : 'Guardar' }}</button>
          </div>
        </form>

        <!-- Cliente form -->
        <form v-else-if="modal.entity === 'cliente'" @submit.prevent="saveCli" class="modal-form">
          <label>Nombre * <input v-model="cliForm.nombre" required /></label>
          <div class="form-row">
            <label>RUC * <input v-model="cliForm.ruc" required /></label>
            <label>Teléfono <input v-model="cliForm.telefono" /></label>
          </div>
          <label>Correo <input v-model="cliForm.correo" type="email" /></label>
          <label>Dirección <input v-model="cliForm.direccion" /></label>
          <p v-if="modal.error" class="form-error">{{ modal.error }}</p>
          <div class="modal-actions">
            <button type="button" class="btn-ghost" @click="modal.open = false">Cancelar</button>
            <button type="submit" class="btn-primary" :disabled="modal.saving">{{ modal.saving ? 'Guardando...' : 'Guardar' }}</button>
          </div>
        </form>

        <!-- Cuenta form -->
        <form v-else-if="modal.entity === 'cuenta'" @submit.prevent="saveCuenta" class="modal-form">
          <div class="form-row">
            <label>Número/Código * <input v-model="cuentaForm.numero" required /></label>
            <label>Nombre * <input v-model="cuentaForm.nombre" required /></label>
          </div>
          <label>Dirección <input v-model="cuentaForm.direccion" /></label>
          <div class="form-row">
            <label>Distrito <input v-model="cuentaForm.distrito" /></label>
            <label>Tipo
              <select v-model="cuentaForm.tipo">
                <option value="empresa">Empresa</option>
                <option value="hogar">Hogar</option>
                <option value="gobierno">Gobierno</option>
                <option value="otro">Otro</option>
              </select>
            </label>
          </div>
          <div class="form-row">
            <label>Contacto <input v-model="cuentaForm.contacto" /></label>
            <label>Teléfono <input v-model="cuentaForm.telefono" /></label>
          </div>
          <div class="form-row">
            <label>Latitud * <input v-model.number="cuentaForm.latitud" type="number" step="any" required /></label>
            <label>Longitud * <input v-model.number="cuentaForm.longitud" type="number" step="any" required /></label>
          </div>
          <p v-if="modal.error" class="form-error">{{ modal.error }}</p>
          <div class="modal-actions">
            <button type="button" class="btn-ghost" @click="modal.open = false">Cancelar</button>
            <button type="submit" class="btn-primary" :disabled="modal.saving">{{ modal.saving ? 'Guardando...' : 'Guardar' }}</button>
          </div>
        </form>

        <!-- Técnico form -->
        <form v-else-if="modal.entity === 'tec'" @submit.prevent="saveTec" class="modal-form">
          <label>Nombre completo * <input v-model="tecForm.nombre" required /></label>
          <div class="form-row">
            <label>Especialidad * <input v-model="tecForm.especialidad" required /></label>
            <label>Zona * <input v-model="tecForm.zona" required /></label>
          </div>
          <label>Teléfono <input v-model="tecForm.telefono" /></label>
          <div class="form-row">
            <label>Latitud base * <input v-model.number="tecForm.latitud_base" type="number" step="any" required /></label>
            <label>Longitud base * <input v-model.number="tecForm.longitud_base" type="number" step="any" required /></label>
          </div>
          <label>
            Activo
            <select v-model="tecForm.activo">
              <option :value="true">Sí</option>
              <option :value="false">No</option>
            </select>
          </label>
          <p v-if="modal.error" class="form-error">{{ modal.error }}</p>
          <div class="modal-actions">
            <button type="button" class="btn-ghost" @click="modal.open = false">Cancelar</button>
            <button type="submit" class="btn-primary" :disabled="modal.saving">{{ modal.saving ? 'Guardando...' : 'Guardar' }}</button>
          </div>
        </form>

        <!-- Usuario form -->
        <form v-else-if="modal.entity === 'usr'" @submit.prevent="saveUsr" class="modal-form">
          <div class="form-row">
            <label>Username * <input v-model="usrForm.username" required :disabled="modal.mode === 'edit'" /></label>
            <label>Nombre completo * <input v-model="usrForm.nombre_completo" required /></label>
          </div>
          <label>Email * <input v-model="usrForm.email" type="email" required /></label>
          <div class="form-row">
            <label>Rol *
              <select v-model="usrForm.rol" required>
                <option value="admin">Admin</option>
                <option value="coordinador">Coordinador</option>
                <option value="tecnico">Técnico</option>
              </select>
            </label>
            <label>Privilegio
              <select v-model="usrForm.privilegio">
                <option value="">Ninguno</option>
                <option value="supervisor">Supervisor</option>
              </select>
            </label>
          </div>
          <label>
            {{ modal.mode === 'create' ? 'Contraseña *' : 'Nueva contraseña (vacío = sin cambio)' }}
            <input v-model="usrForm.password" type="password" :required="modal.mode === 'create'" autocomplete="new-password" />
          </label>
          <label>
            Activo
            <select v-model="usrForm.activo">
              <option :value="true">Sí</option>
              <option :value="false">No</option>
            </select>
          </label>
          <p v-if="modal.error" class="form-error">{{ modal.error }}</p>
          <div class="modal-actions">
            <button type="button" class="btn-ghost" @click="modal.open = false">Cancelar</button>
            <button type="submit" class="btn-primary" :disabled="modal.saving">{{ modal.saving ? 'Guardando...' : 'Guardar' }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal eliminar -->
    <div v-if="delModal.open" class="modal-overlay" @click.self="delModal.open = false">
      <div class="modal modal-sm">
        <h3>Eliminar registro</h3>
        <p>¿Eliminar <strong>{{ delModal.name }}</strong>? Esta acción no se puede deshacer.</p>
        <p v-if="delModal.error" class="form-error">{{ delModal.error }}</p>
        <div class="modal-actions">
          <button class="btn-ghost" @click="delModal.open = false">Cancelar</button>
          <button class="btn-danger" :disabled="delModal.loading" @click="doDelete">
            {{ delModal.loading ? 'Eliminando...' : 'Eliminar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { getSessionUser, esAdmin, esSupervisor } from '../stores/sessionStore';
import { listClientes, createCliente, updateCliente, deleteCliente, type ApiCliente } from '../api/clientes';
import { listCuentas, createCuenta, updateCuenta, deleteCuenta, type ApiCuenta } from '../api/cuentas';
import { listInventario, createInventario, updateInventario, deleteInventario, type ApiInventario } from '../api/inventario';
import { listTecnicos, createTecnico, updateTecnico, deleteTecnico, type ApiTecnico } from '../api/tecnicos';
import { listUsuarios, createUsuario, updateUsuario, deleteUsuario, type ApiUsuario } from '../api/usuarios';

const currentUser = getSessionUser();

interface Module { key: string; title: string; desc: string; icon: string; adminOnly?: boolean; }

const ALL_MODULES: Module[] = [
  { key: 'inventario', title: 'Inventario', desc: 'Items, precios y stock disponible', icon: '📦' },
  { key: 'cuentas-clientes', title: 'Clientes y Cuentas', desc: 'Clientes y sus sedes asociadas', icon: '🏢' },
  { key: 'personal-campo', title: 'Personal de campo', desc: 'Técnicos, zonas y especialidades', icon: '🔧' },
  { key: 'usuarios', title: 'Usuarios', desc: 'Gestión de acceso y roles del sistema', icon: '👤', adminOnly: true },
];

const visibleModules = computed(() =>
  ALL_MODULES.filter(m => !m.adminOnly || esAdmin(currentUser) || esSupervisor(currentUser))
);

const activeModule = ref<Module | null>(null);

// ── Datos ──────────────────────────────────────────────────────────────────
const inventario = ref<ApiInventario[]>([]);
const clientes = ref<ApiCliente[]>([]);
const cuentas = ref<ApiCuenta[]>([]);
const tecnicos = ref<ApiTecnico[]>([]);
const usuarios = ref<ApiUsuario[]>([]);

const loadingInv = ref(false);
const loadingCli = ref(false);
const loadingTec = ref(false);
const loadingUsr = ref(false);

// ── Filtros ────────────────────────────────────────────────────────────────
const searchInv = ref('');
const filterCat = ref('');
const searchCli = ref('');
const searchTec = ref('');
const searchUsr = ref('');
const filterRol = ref('');

// ── Computed filtrados ─────────────────────────────────────────────────────
const filteredInv = computed(() => {
  let list = inventario.value;
  if (filterCat.value) list = list.filter(i => i.categoria === filterCat.value);
  if (searchInv.value) {
    const q = searchInv.value.toLowerCase();
    list = list.filter(i => i.nombre.toLowerCase().includes(q) || i.sku.toLowerCase().includes(q));
  }
  return list;
});

const filteredClientes = computed(() => {
  if (!searchCli.value) return clientes.value;
  const q = searchCli.value.toLowerCase();
  return clientes.value.filter(c => c.nombre.toLowerCase().includes(q) || c.ruc.toLowerCase().includes(q));
});

const cuentasByCliente = computed(() => {
  const map: Record<string, ApiCuenta[]> = {};
  for (const cu of cuentas.value) {
    if (!map[cu.cliente_id]) map[cu.cliente_id] = [];
    map[cu.cliente_id].push(cu);
  }
  return map;
});

const filteredTecnicos = computed(() => {
  if (!searchTec.value) return tecnicos.value;
  const q = searchTec.value.toLowerCase();
  return tecnicos.value.filter(t => t.nombre.toLowerCase().includes(q) || t.zona.toLowerCase().includes(q));
});

const filteredUsuarios = computed(() => {
  let list = usuarios.value;
  if (filterRol.value) list = list.filter(u => u.rol === filterRol.value);
  if (searchUsr.value) {
    const q = searchUsr.value.toLowerCase();
    list = list.filter(u => u.username.toLowerCase().includes(q) || u.nombre_completo.toLowerCase().includes(q));
  }
  return list;
});

// ── Toast ──────────────────────────────────────────────────────────────────
const toast = reactive({ show: false, type: 'success', msg: '' });
function showToast(type: 'success' | 'error', msg: string) {
  toast.type = type;
  toast.msg = msg;
  toast.show = true;
  setTimeout(() => { toast.show = false; }, 4000);
}

// ── Modal crear/editar ─────────────────────────────────────────────────────
const modal = reactive({
  open: false,
  mode: 'create' as 'create' | 'edit',
  entity: '' as string,
  entityLabel: '',
  editId: '',
  saving: false,
  error: '',
});

// Form states
const invForm = reactive<{ sku: string; nombre: string; descripcion: string; categoria: 'epp' | 'material' | 'herramienta' | 'otro'; stock_disponible: number; stock_minimo: number; precio_unitario: number; unidad: string; activo: boolean }>({ sku: '', nombre: '', descripcion: '', categoria: 'material', stock_disponible: 0, stock_minimo: 0, precio_unitario: 0, unidad: 'unidad', activo: true });
const cliForm = reactive({ nombre: '', ruc: '', telefono: '', correo: '', direccion: '' });
const cuentaForm = reactive({ numero: '', nombre: '', direccion: '', distrito: '', contacto: '', telefono: '', tipo: 'empresa', latitud: -12.0464, longitud: -77.0428, cliente_id: '' });
const tecForm = reactive({ nombre: '', especialidad: '', zona: '', telefono: '', latitud_base: -12.0464, longitud_base: -77.0428, activo: true });
const usrForm = reactive({ username: '', nombre_completo: '', email: '', rol: 'tecnico', privilegio: '', password: '', activo: true });

// ── Modal eliminar ─────────────────────────────────────────────────────────
const delModal = reactive({ open: false, entity: '', id: '', name: '', loading: false, error: '' });

// ── Cargar datos ───────────────────────────────────────────────────────────
async function openModule(m: Module) {
  activeModule.value = m;
  switch (m.key) {
    case 'inventario':
      loadingInv.value = true;
      inventario.value = await listInventario().finally(() => { loadingInv.value = false; });
      break;
    case 'cuentas-clientes':
      loadingCli.value = true;
      await Promise.all([
        listClientes().then(v => { clientes.value = v; }),
        listCuentas().then(v => { cuentas.value = v; }),
      ]).finally(() => { loadingCli.value = false; });
      break;
    case 'personal-campo':
      loadingTec.value = true;
      tecnicos.value = await listTecnicos().finally(() => { loadingTec.value = false; });
      break;
    case 'usuarios':
      loadingUsr.value = true;
      usuarios.value = await listUsuarios().finally(() => { loadingUsr.value = false; });
      break;
  }
}

// ── Abrir modal ────────────────────────────────────────────────────────────
function openCreate(entity?: string, clienteId?: string) {
  modal.mode = 'create';
  if (entity) {
    modal.entity = entity;
  } else {
    const key = activeModule.value!.key;
    modal.entity = key === 'inventario' ? 'inv'
      : key === 'personal-campo' ? 'tec'
      : key === 'usuarios' ? 'usr'
      : 'inv';
  }
  modal.editId = '';
  modal.error = '';
  modal.entityLabel = { inv: 'ítem de inventario', cliente: 'cliente', cuenta: 'cuenta', tec: 'técnico', usr: 'usuario' }[modal.entity] || 'registro';

  if (modal.entity === 'inv') Object.assign(invForm, { sku: '', nombre: '', descripcion: '', categoria: 'material', stock_disponible: 0, stock_minimo: 0, precio_unitario: 0, unidad: 'unidad', activo: true });
  if (modal.entity === 'cliente') Object.assign(cliForm, { nombre: '', ruc: '', telefono: '', correo: '', direccion: '' });
  if (modal.entity === 'cuenta') Object.assign(cuentaForm, { numero: '', nombre: '', direccion: '', distrito: '', contacto: '', telefono: '', tipo: 'empresa', latitud: -12.0464, longitud: -77.0428, cliente_id: clienteId || '' });
  if (modal.entity === 'tec') Object.assign(tecForm, { nombre: '', especialidad: '', zona: '', telefono: '', latitud_base: -12.0464, longitud_base: -77.0428, activo: true });
  if (modal.entity === 'usr') Object.assign(usrForm, { username: '', nombre_completo: '', email: '', rol: 'tecnico', privilegio: '', password: '', activo: true });

  modal.open = true;
}

function openEdit(entity: string, item: unknown) {
  modal.mode = 'edit';
  modal.entity = entity;
  modal.editId = (item as Record<string, unknown>).id as string;
  modal.error = '';
  modal.entityLabel = { inv: 'ítem de inventario', cliente: 'cliente', cuenta: 'cuenta', tec: 'técnico', usr: 'usuario' }[entity] || 'registro';

  if (entity === 'inv') {
    const i = item as unknown as ApiInventario;
    Object.assign(invForm, { sku: i.sku, nombre: i.nombre, descripcion: i.descripcion, categoria: i.categoria, stock_disponible: i.stock_disponible, stock_minimo: i.stock_minimo, precio_unitario: i.precio_unitario, unidad: i.unidad, activo: i.activo });
  } else if (entity === 'cliente') {
    const c = item as unknown as ApiCliente;
    Object.assign(cliForm, { nombre: c.nombre, ruc: c.ruc, telefono: c.telefono, correo: c.correo, direccion: c.direccion });
  } else if (entity === 'cuenta') {
    const c = item as unknown as ApiCuenta;
    Object.assign(cuentaForm, { numero: c.numero, nombre: c.nombre, direccion: c.direccion, distrito: c.distrito, contacto: c.contacto, telefono: c.telefono, tipo: c.tipo, latitud: c.latitud, longitud: c.longitud, cliente_id: c.cliente_id });
  } else if (entity === 'tec') {
    const t = item as unknown as ApiTecnico;
    Object.assign(tecForm, { nombre: t.nombre, especialidad: t.especialidad, zona: t.zona, telefono: t.telefono, latitud_base: t.latitud_base, longitud_base: t.longitud_base, activo: t.activo });
  } else if (entity === 'usr') {
    const u = item as unknown as ApiUsuario;
    Object.assign(usrForm, { username: u.username, nombre_completo: u.nombre_completo, email: u.email, rol: u.rol, privilegio: u.privilegio || '', password: '', activo: u.activo });
  }
  modal.open = true;
}

// ── Guardar ────────────────────────────────────────────────────────────────
async function saveInv() {
  modal.saving = true;
  modal.error = '';
  try {
    if (modal.mode === 'create') {
      const item = await createInventario({ ...invForm });
      inventario.value.unshift(item);
    } else {
      const item = await updateInventario(modal.editId, { ...invForm });
      const idx = inventario.value.findIndex(i => i.id === modal.editId);
      if (idx >= 0) inventario.value[idx] = item;
    }
    modal.open = false;
    showToast('success', 'Ítem guardado correctamente.');
  } catch (e: unknown) {
    modal.error = e instanceof Error ? e.message : 'Error al guardar';
  } finally {
    modal.saving = false;
  }
}

async function saveCli() {
  modal.saving = true;
  modal.error = '';
  try {
    if (modal.mode === 'create') {
      const c = await createCliente({ ...cliForm });
      clientes.value.unshift(c);
    } else {
      const c = await updateCliente(modal.editId, { ...cliForm });
      const idx = clientes.value.findIndex(x => x.id === modal.editId);
      if (idx >= 0) clientes.value[idx] = c;
    }
    modal.open = false;
    showToast('success', 'Cliente guardado.');
  } catch (e: unknown) {
    modal.error = e instanceof Error ? e.message : 'Error al guardar';
  } finally {
    modal.saving = false;
  }
}

async function saveCuenta() {
  modal.saving = true;
  modal.error = '';
  try {
    if (modal.mode === 'create') {
      const c = await createCuenta({ ...cuentaForm });
      cuentas.value.push(c);
    } else {
      const c = await updateCuenta(modal.editId, { ...cuentaForm });
      const idx = cuentas.value.findIndex(x => x.id === modal.editId);
      if (idx >= 0) cuentas.value[idx] = c;
    }
    modal.open = false;
    showToast('success', 'Cuenta guardada.');
  } catch (e: unknown) {
    modal.error = e instanceof Error ? e.message : 'Error al guardar';
  } finally {
    modal.saving = false;
  }
}

async function saveTec() {
  modal.saving = true;
  modal.error = '';
  try {
    if (modal.mode === 'create') {
      const t = await createTecnico({ ...tecForm });
      tecnicos.value.unshift(t);
    } else {
      const t = await updateTecnico(modal.editId, { ...tecForm });
      const idx = tecnicos.value.findIndex(x => x.id === modal.editId);
      if (idx >= 0) tecnicos.value[idx] = t;
    }
    modal.open = false;
    showToast('success', 'Técnico guardado.');
  } catch (e: unknown) {
    modal.error = e instanceof Error ? e.message : 'Error al guardar';
  } finally {
    modal.saving = false;
  }
}

async function saveUsr() {
  modal.saving = true;
  modal.error = '';
  try {
    const payload: Record<string, unknown> = {
      username: usrForm.username,
      nombre_completo: usrForm.nombre_completo,
      email: usrForm.email,
      rol: usrForm.rol,
      privilegio: usrForm.privilegio || null,
      activo: usrForm.activo,
    };
    if (usrForm.password) payload.password = usrForm.password;

    if (modal.mode === 'create') {
      if (!usrForm.password) { modal.error = 'La contraseña es obligatoria.'; modal.saving = false; return; }
      const u = await createUsuario(payload as Parameters<typeof createUsuario>[0]);
      usuarios.value.unshift(u);
    } else {
      const u = await updateUsuario(modal.editId, payload as Partial<ApiUsuario & { password?: string }>);
      const idx = usuarios.value.findIndex(x => x.id === modal.editId);
      if (idx >= 0) usuarios.value[idx] = u;
    }
    modal.open = false;
    showToast('success', 'Usuario guardado.');
  } catch (e: unknown) {
    modal.error = e instanceof Error ? e.message : 'Error al guardar';
  } finally {
    modal.saving = false;
  }
}

// ── Eliminar ───────────────────────────────────────────────────────────────
function confirmDelete(entity: string, id: string, name: string) {
  Object.assign(delModal, { open: true, entity, id, name, loading: false, error: '' });
}

async function doDelete() {
  delModal.loading = true;
  delModal.error = '';
  try {
    switch (delModal.entity) {
      case 'inv': await deleteInventario(delModal.id); inventario.value = inventario.value.filter(i => i.id !== delModal.id); break;
      case 'cliente': await deleteCliente(delModal.id); clientes.value = clientes.value.filter(c => c.id !== delModal.id); break;
      case 'cuenta': await deleteCuenta(delModal.id); cuentas.value = cuentas.value.filter(c => c.id !== delModal.id); break;
      case 'tec': await deleteTecnico(delModal.id); tecnicos.value = tecnicos.value.filter(t => t.id !== delModal.id); break;
      case 'usr': await deleteUsuario(delModal.id); usuarios.value = usuarios.value.filter(u => u.id !== delModal.id); break;
    }
    delModal.open = false;
    showToast('success', 'Registro eliminado.');
  } catch (e: unknown) {
    delModal.error = e instanceof Error ? e.message : 'Error al eliminar';
  } finally {
    delModal.loading = false;
  }
}
</script>

<style scoped>
.bd-view { display: flex; flex-direction: column; gap: 1rem; height: 100%; }

/* Toast */
.bd-toast { position: fixed; top: 1rem; right: 1rem; z-index: 2000; display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem; border-radius: 0.5rem; font-size: 0.85rem; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
.bd-toast.success { background: #15803d; color: #dcfce7; }
.bd-toast.error { background: #991b1b; color: #fee2e2; }
.bd-toast button { background: none; border: none; color: inherit; cursor: pointer; opacity: 0.7; font-size: 1rem; }
.toast-fade-enter-active, .toast-fade-leave-active { transition: all 0.3s; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateY(-1rem); }

/* Header */
.bd-header { display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.5rem; background: var(--surface, #1e293b); border-radius: 0.75rem; flex-wrap: wrap; gap: 0.5rem; }
.bd-header h2 { margin: 0; font-size: 1.25rem; color: var(--text-primary, #f1f5f9); }
.bd-header p { margin: 0; font-size: 0.8rem; color: var(--text-muted, #94a3b8); }
.header-actions { display: flex; gap: 0.5rem; }

/* Modules grid */
.modules-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 1rem; }
.module-card { background: var(--surface, #1e293b); border: 1px solid var(--border, #334155); border-radius: 0.75rem; padding: 1.25rem; display: flex; align-items: center; gap: 1rem; cursor: pointer; text-align: left; transition: all 0.15s; }
.module-card:hover { border-color: #6366f1; transform: translateY(-2px); }
.module-icon { font-size: 2rem; flex-shrink: 0; }
.module-info { flex: 1; }
.module-info strong { display: block; font-size: 0.95rem; color: var(--text-primary, #f1f5f9); margin-bottom: 0.2rem; }
.module-info p { margin: 0; font-size: 0.78rem; color: var(--text-muted, #94a3b8); }
.module-arrow { color: var(--text-muted, #94a3b8); font-size: 1.2rem; }

/* Table card */
.bd-table-card { background: var(--surface, #1e293b); border-radius: 0.75rem; padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem; flex: 1; overflow: hidden; }
.table-toolbar { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.bd-search { padding: 0.45rem 0.75rem; border: 1px solid var(--border, #334155); border-radius: 0.4rem; background: var(--bg, #0f172a); color: var(--text-primary, #f1f5f9); font-size: 0.8rem; flex: 1; min-width: 160px; }
.bd-select { padding: 0.45rem 0.5rem; border: 1px solid var(--border, #334155); border-radius: 0.4rem; background: var(--bg, #0f172a); color: var(--text-primary, #f1f5f9); font-size: 0.8rem; }
.bd-loading { color: var(--text-muted, #94a3b8); font-size: 0.85rem; padding: 1rem; }
.bd-empty { color: var(--text-muted, #94a3b8); font-size: 0.85rem; padding: 1rem; text-align: center; }

.bd-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
.bd-table th { padding: 0.5rem 0.75rem; text-align: left; color: var(--text-muted, #94a3b8); font-weight: 600; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; border-bottom: 1px solid var(--border, #334155); }
.bd-table td { padding: 0.55rem 0.75rem; color: var(--text-secondary, #cbd5e1); border-bottom: 1px solid rgba(51,65,85,0.5); }
.bd-table tr:hover td { background: rgba(255,255,255,0.02); }
.bd-table tr.row-low td:first-child { border-left: 2px solid #ef4444; }
.td-empty { text-align: center; color: var(--text-muted, #94a3b8); padding: 2rem !important; }
.td-actions { display: flex; gap: 0.3rem; justify-content: flex-end; }
.text-danger { color: #f87171; }

/* Badges */
.cat-badge { font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 999px; font-weight: 600; }
.cat-epp { background: rgba(168,85,247,0.2); color: #d8b4fe; }
.cat-material { background: rgba(59,130,246,0.2); color: #93c5fd; }
.cat-herramienta { background: rgba(234,179,8,0.2); color: #fbbf24; }
.cat-otro { background: rgba(100,116,139,0.2); color: #94a3b8; }

.rol-badge { font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 999px; font-weight: 600; }
.rol-admin { background: rgba(239,68,68,0.2); color: #fca5a5; }
.rol-coordinador { background: rgba(99,102,241,0.2); color: #a5b4fc; }
.rol-tecnico { background: rgba(34,197,94,0.2); color: #86efac; }

.status-dot { font-size: 0.75rem; display: flex; align-items: center; gap: 0.3rem; }
.status-dot::before { content: ''; width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.dot-green::before { background: #4ade80; }
.dot-gray::before { background: #94a3b8; }

.num-pill { background: rgba(99,102,241,0.2); color: #a5b4fc; padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.75rem; font-weight: 700; }

/* Clientes / Cuentas */
.bd-cc { background: var(--surface, #1e293b); border-radius: 0.75rem; padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem; flex: 1; overflow-y: auto; }
.bd-cc-header { display: flex; gap: 0.5rem; align-items: center; }
.clientes-list { display: flex; flex-direction: column; gap: 0.75rem; }
.cli-card { background: var(--bg, #0f172a); border-radius: 0.5rem; border: 1px solid var(--border, #334155); overflow: hidden; }
.cli-head { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 1rem; flex-wrap: wrap; gap: 0.5rem; }
.cli-head strong { display: block; font-size: 0.9rem; color: var(--text-primary, #f1f5f9); }
.cli-head small { font-size: 0.75rem; color: var(--text-muted, #94a3b8); }
.cli-actions { display: flex; gap: 0.3rem; }
.cli-info { display: flex; gap: 1rem; padding: 0 1rem 0.5rem; font-size: 0.75rem; color: var(--text-muted, #94a3b8); flex-wrap: wrap; }
.cuentas-list { border-top: 1px solid var(--border, #334155); }
.cuenta-empty { padding: 0.5rem 1rem; font-size: 0.75rem; color: var(--text-muted, #94a3b8); }
.cuenta-item { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 1rem; border-bottom: 1px solid rgba(51,65,85,0.5); }
.cuenta-info { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.cuenta-num { font-size: 0.72rem; background: rgba(99,102,241,0.15); color: #a5b4fc; padding: 0.1rem 0.4rem; border-radius: 0.25rem; font-weight: 600; }
.cuenta-info strong { font-size: 0.82rem; color: var(--text-primary, #f1f5f9); }
.cuenta-info small { font-size: 0.72rem; color: var(--text-muted, #94a3b8); }
.cuenta-actions { display: flex; gap: 0.3rem; }

/* Buttons */
.btn-primary { padding: 0.5rem 1rem; background: #6366f1; color: #fff; border: none; border-radius: 0.4rem; cursor: pointer; font-size: 0.85rem; font-weight: 600; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-ghost { padding: 0.5rem 1rem; background: transparent; color: var(--text-secondary, #cbd5e1); border: 1px solid var(--border, #334155); border-radius: 0.4rem; cursor: pointer; font-size: 0.85rem; }
.btn-danger { padding: 0.5rem 1rem; background: #dc2626; color: #fff; border: none; border-radius: 0.4rem; cursor: pointer; font-size: 0.85rem; font-weight: 600; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-icon { width: 28px; height: 28px; border: 1px solid var(--border, #334155); border-radius: 0.35rem; background: transparent; color: var(--text-secondary, #cbd5e1); cursor: pointer; font-size: 0.85rem; display: inline-flex; align-items: center; justify-content: center; }
.btn-icon:hover { border-color: #6366f1; color: #a5b4fc; }
.btn-icon.danger:hover { border-color: #ef4444; color: #f87171; }
.btn-sm { padding: 0.25rem 0.6rem; background: rgba(99,102,241,0.15); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.3); border-radius: 0.35rem; cursor: pointer; font-size: 0.75rem; white-space: nowrap; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.55); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 1rem; }
.modal { background: var(--surface, #1e293b); border-radius: 0.75rem; padding: 1.5rem; width: 520px; max-width: 100%; max-height: 90vh; overflow-y: auto; display: flex; flex-direction: column; gap: 0.75rem; }
.modal-sm { width: 380px; }
.modal-head { display: flex; justify-content: space-between; align-items: center; }
.modal-head h3 { margin: 0; font-size: 1rem; color: var(--text-primary, #f1f5f9); }
.modal-close { background: none; border: none; color: var(--text-muted, #94a3b8); cursor: pointer; font-size: 1.1rem; }
.modal h3 { margin: 0; color: var(--text-primary, #f1f5f9); }
.modal p { margin: 0; font-size: 0.85rem; color: var(--text-secondary, #cbd5e1); }

.modal-form { display: flex; flex-direction: column; gap: 0.65rem; }
.modal-form label { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.8rem; color: var(--text-muted, #94a3b8); }
.modal-form input, .modal-form select, .modal-form textarea { padding: 0.5rem 0.65rem; border: 1px solid var(--border, #334155); border-radius: 0.4rem; background: var(--bg, #0f172a); color: var(--text-primary, #f1f5f9); font-size: 0.85rem; font-family: inherit; }
.modal-form textarea { resize: vertical; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.65rem; }
.form-error { color: #f87171; font-size: 0.8rem; margin: 0; }
.modal-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 0.25rem; }
</style>
