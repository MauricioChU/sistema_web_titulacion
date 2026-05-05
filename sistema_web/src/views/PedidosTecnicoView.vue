<template>
  <div class="tecnico-view">
    <header class="tv-header">
      <div>
        <h2>Mis Pedidos</h2>
        <p>Gestiona el trabajo de campo asignado a tu usuario</p>
      </div>
      <div class="header-stats">
        <div class="stat-pill"><span>{{ pedidosPorConfirmar.length }}</span> por confirmar</div>
        <div class="stat-pill active"><span>{{ pedidosEnCurso.length }}</span> en curso</div>
      </div>
    </header>

    <div class="tv-layout">
      <!-- Lista de pedidos -->
      <aside class="tv-sidebar">
        <div class="tv-filters">
          <input v-model="search" type="search" placeholder="Buscar OT o cliente..." class="tv-search" />
          <select v-model="filterEstado" class="tv-select">
            <option value="">Todos los estados</option>
            <option value="por-confirmar">Por confirmar</option>
            <option value="confirmado">Confirmado</option>
            <option value="en-labor">En labor</option>
            <option value="cierre-tecnico">Cierre técnico</option>
            <option value="completado">Completado</option>
            <option value="dado-de-baja">Dado de baja</option>
          </select>
        </div>

        <div class="tv-list">
          <div v-if="loading" class="tv-empty">Cargando...</div>
          <div v-else-if="filteredPedidos.length === 0" class="tv-empty">No hay pedidos asignados.</div>
          <button
            v-for="p in filteredPedidos"
            :key="p.id"
            class="tv-item"
            :class="{
              active: selectedId === p.id,
              urgent: p.prioridad === 'critica' || p.prioridad === 'alta',
              pending: p.estado === 'por-confirmar'
            }"
            @click="selectPedido(p.id)"
          >
            <div class="tv-item-top">
              <strong>{{ p.codigo }}</strong>
              <span class="tv-badge" :class="`pr-${p.prioridad}`">{{ p.prioridad }}</span>
            </div>
            <div class="tv-item-cliente">{{ p.cliente_nombre }}</div>
            <p class="tv-item-titulo">{{ p.titulo }}</p>
            <div class="tv-item-bottom">
              <span class="tv-estado" :class="`es-${p.estado}`">{{ estadoLabel(p.estado) }}</span>
              <span class="tv-fecha">{{ fmtDate(p.created_at) }}</span>
            </div>
            <div v-if="p.estado === 'por-confirmar'" class="pending-indicator">⚡ Requiere confirmación</div>
          </button>
        </div>
      </aside>

      <!-- Panel principal -->
      <main class="tv-main">
        <div v-if="!selected" class="tv-empty-detail">
          <div class="empty-icon">🔧</div>
          <p>Selecciona un pedido para ver las acciones disponibles.</p>
        </div>

        <div v-else class="tv-card">
          <!-- Encabezado -->
          <div class="tv-card-head">
            <div>
              <h3>{{ selected.codigo }} — {{ selected.titulo }}</h3>
              <p>{{ selected.cliente_nombre }} · {{ selected.cuenta_nombre }}</p>
              <p class="tv-desc">{{ selected.descripcion }}</p>
            </div>
            <div class="head-badges">
              <span class="tv-badge" :class="`pr-${selected.prioridad}`">{{ selected.prioridad }}</span>
              <span class="tv-estado" :class="`es-${selected.estado}`">{{ estadoLabel(selected.estado) }}</span>
            </div>
          </div>

          <!-- Acción rápida: confirmar / rechazar -->
          <div v-if="selected.estado === 'por-confirmar'" class="action-card urgent-action">
            <h4>⚡ Acción requerida</h4>
            <p>Este pedido necesita tu confirmación antes de iniciar el trabajo de campo.</p>
            <div class="action-btns">
              <button class="btn-confirm" :disabled="actionLoading" @click="confirmar">
                {{ actionLoading ? 'Procesando...' : '✓ Confirmar pedido' }}
              </button>
              <button class="btn-reject" @click="showRechazar = true">✕ Rechazar pedido</button>
            </div>
          </div>

          <!-- EPPs asignados -->
          <div v-if="selected.epps_asignados?.length" class="tv-section">
            <h4>EPPs asignados para este pedido</h4>
            <div class="items-table">
              <div class="item-row header-row"><span>EPP</span><span>SKU</span><span>Cant.</span><span>Precio unit.</span></div>
              <div v-for="e in selected.epps_asignados" :key="e.item_id" class="item-row">
                <span>{{ e.nombre }}</span>
                <span>{{ e.sku }}</span>
                <span>{{ e.cantidad }}</span>
                <span>S/ {{ e.precio_unitario.toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <!-- Tabs (disponibles cuando confirmado o más avanzado) -->
          <nav class="tv-tabs" v-if="['confirmado','en-labor','cierre-tecnico','completado'].includes(selected.estado)">
            <button
              v-for="t in tabs"
              :key="t.key"
              class="tab-btn"
              :class="{ active: tab === t.key }"
              @click="tab = t.key"
            >
              {{ t.label }}
            </button>
          </nav>

          <!-- Tab: Checklist -->
          <div v-if="tab === 'checklist' && selected.estado !== 'por-confirmar'" class="tab-content">
            <div class="checklist-grid">
              <div
                v-for="step in selected.checklist"
                :key="step.step_id"
                class="check-card"
                :class="{ done: step.completado }"
              >
                <div class="check-header">
                  <span class="check-icon">{{ step.completado ? '✓' : '○' }}</span>
                  <strong>{{ step.label }}</strong>
                  <small v-if="step.completado_en">{{ fmtDate(step.completado_en!) }}</small>
                </div>
                <div v-if="step.nota" class="check-nota">{{ step.nota }}</div>
                <div v-if="!step.completado" class="check-actions">
                  <input
                    v-model="checkNota[step.step_id]"
                    type="text"
                    placeholder="Nota opcional..."
                    class="check-input"
                  />
                  <button
                    class="btn-complete"
                    :disabled="actionLoading"
                    @click="marcarChecklist(step.step_id)"
                  >
                    Marcar completado
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Tab: Evidencias -->
          <div v-else-if="tab === 'evidencias'" class="tab-content">
            <div class="ev-upload">
              <h4>Subir evidencia</h4>
              <div class="upload-form">
                <select v-model="evForm.stage" class="ev-select">
                  <option value="antes">Antes del trabajo</option>
                  <option value="despues">Después del trabajo</option>
                </select>
                <input v-model="evForm.descripcion" type="text" placeholder="Descripción..." class="ev-input" />
                <label class="file-label">
                  <span>{{ evForm.file ? evForm.file.name : 'Seleccionar imagen' }}</span>
                  <input type="file" accept="image/*" @change="onFileChange" hidden />
                </label>
                <button class="btn-upload" :disabled="!evForm.file || uploadingEv" @click="uploadEv">
                  {{ uploadingEv ? 'Subiendo...' : '↑ Subir' }}
                </button>
              </div>
              <p v-if="evError" class="form-error">{{ evError }}</p>
            </div>

            <div class="ev-gallery" v-if="selected.evidencias?.length">
              <div v-for="e in selected.evidencias" :key="e.id" class="ev-card">
                <img :src="evidenciaUrl(e.archivo)" :alt="e.nombre" />
                <div class="ev-info">
                  <span class="ev-stage" :class="`stage-${e.stage}`">{{ e.stage }}</span>
                  <small>{{ e.descripcion }}</small>
                  <small>{{ fmtDate(e.uploaded_at) }}</small>
                </div>
              </div>
            </div>
            <p v-else class="tv-empty">Sin evidencias cargadas aún.</p>
          </div>

          <!-- Tab: Diagnóstico -->
          <div v-else-if="tab === 'diagnostico'" class="tab-content">
            <h4>Diagnóstico técnico</h4>
            <textarea
              v-model="diagText"
              rows="5"
              class="tv-textarea"
              placeholder="Describe los hallazgos técnicos encontrados en el campo..."
            ></textarea>
            <div class="form-actions">
              <button class="btn-primary" :disabled="savingDiag" @click="saveDiag">
                {{ savingDiag ? 'Guardando...' : 'Guardar diagnóstico' }}
              </button>
            </div>
            <p v-if="diagError" class="form-error">{{ diagError }}</p>
          </div>

          <!-- Tab: Materiales usados -->
          <div v-else-if="tab === 'materiales'" class="tab-content">
            <h4>Registrar materiales usados</h4>
            <p class="tv-hint">Los materiales se descuentan automáticamente del inventario al registrarlos.</p>

            <div class="item-adder">
              <select v-model="matSel.item_id" @change="onMatChange" style="flex:2" class="ev-select">
                <option value="">Seleccionar material del inventario...</option>
                <option v-for="i in inventario" :key="i.id" :value="i.id">
                  {{ i.nombre }} — stock: {{ i.stock_disponible }} {{ i.unidad }}
                </option>
              </select>
              <input v-model.number="matSel.cantidad" type="number" min="1" placeholder="Cant." class="qty-input" />
              <button class="btn-add" @click="addMat">+ Agregar</button>
            </div>

            <div class="items-table" v-if="matUsados.length">
              <div class="item-row header-row">
                <span>Material</span><span>SKU</span><span>Cant.</span><span>P.Unit.</span><span>Subtotal</span><span></span>
              </div>
              <div v-for="(m, idx) in matUsados" :key="idx" class="item-row">
                <span>{{ m.nombre }}</span>
                <span>{{ m.sku }}</span>
                <span>{{ m.cantidad }}</span>
                <span>S/ {{ m.precio_unitario.toFixed(2) }}</span>
                <span>S/ {{ (m.cantidad * m.precio_unitario).toFixed(2) }}</span>
                <button class="btn-remove" @click="matUsados.splice(idx, 1)">✕</button>
              </div>
            </div>

            <p v-if="matError" class="form-error">{{ matError }}</p>
            <div class="form-actions">
              <button class="btn-primary" :disabled="!matUsados.length || savingMat" @click="saveMateriales">
                {{ savingMat ? 'Registrando...' : 'Registrar materiales' }}
              </button>
            </div>

            <div v-if="selected.materiales_usados?.length" class="mt-4">
              <h5>Materiales ya registrados</h5>
              <div class="items-table">
                <div class="item-row header-row">
                  <span>Material</span><span>SKU</span><span>Cant.</span><span>P.Unit.</span><span>Subtotal</span><span></span>
                </div>
                <div v-for="m in selected.materiales_usados" :key="m.item_id" class="item-row">
                  <span>{{ m.nombre }}</span>
                  <span>{{ m.sku }}</span>
                  <span>{{ m.cantidad }}</span>
                  <span>S/ {{ m.precio_unitario.toFixed(2) }}</span>
                  <span>S/ {{ (m.cantidad * m.precio_unitario).toFixed(2) }}</span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>

          <!-- Tab: Informe final -->
          <div v-else-if="tab === 'informe'" class="tab-content">
            <div v-if="selected.informe" class="informe-done">
              <h4>✓ Informe enviado</h4>
              <div class="info-grid">
                <ul class="info-list">
                  <li><span>Diagnóstico final</span><strong>{{ selected.informe.diagnostico_final }}</strong></li>
                  <li><span>Responsable local</span><strong>{{ selected.informe.responsable_local }}</strong></li>
                  <li><span>Pedido solicitado</span><strong>{{ selected.informe.pedido_solicitado }}</strong></li>
                </ul>
                <ul class="info-list">
                  <li><span>Observaciones</span><strong>{{ selected.informe.observaciones }}</strong></li>
                  <li><span>Recomendaciones</span><strong>{{ selected.informe.recomendaciones }}</strong></li>
                </ul>
              </div>
            </div>

            <form v-else @submit.prevent="submitInforme" class="informe-form">
              <h4>Enviar informe de cierre técnico</h4>
              <label>
                Diagnóstico final *
                <textarea v-model="informeForm.diagnostico_final" rows="3" required placeholder="Hallazgos y diagnóstico final..."></textarea>
              </label>
              <div class="form-row">
                <label>
                  Responsable local *
                  <input v-model="informeForm.responsable_local" required placeholder="Nombre del responsable en sitio" />
                </label>
                <label>
                  Pedido solicitado
                  <input v-model="informeForm.pedido_solicitado" placeholder="Descripción del pedido solicitado" />
                </label>
              </div>
              <label>
                Observaciones *
                <textarea v-model="informeForm.observaciones" rows="2" required placeholder="Observaciones adicionales..."></textarea>
              </label>
              <label>
                Recomendaciones *
                <textarea v-model="informeForm.recomendaciones" rows="2" required placeholder="Recomendaciones para el cliente..."></textarea>
              </label>
              <label>
                Firma del cliente (imagen)
                <label class="file-label" style="cursor:pointer">
                  <span>{{ informeForm.firma ? informeForm.firma.name : 'Seleccionar imagen de firma...' }}</span>
                  <input type="file" accept="image/*" @change="onFirmaChange" hidden />
                </label>
              </label>
              <p v-if="informeError" class="form-error">{{ informeError }}</p>
              <div class="form-actions">
                <button type="submit" class="btn-primary" :disabled="savingInforme">
                  {{ savingInforme ? 'Enviando...' : 'Enviar informe' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>

    <!-- Modal rechazo -->
    <div v-if="showRechazar" class="modal-overlay" @click.self="showRechazar = false">
      <div class="modal">
        <h3>Rechazar pedido</h3>
        <p>Indica el motivo por el que rechazas el pedido <strong>{{ selected?.codigo }}</strong>. El coordinador recibirá una notificación.</p>
        <label>
          Motivo *
          <textarea v-model="rechazarMotivo" rows="3" required placeholder="Describe el motivo del rechazo..."></textarea>
        </label>
        <p v-if="rechazarError" class="form-error">{{ rechazarError }}</p>
        <div class="modal-actions">
          <button class="btn-ghost" @click="showRechazar = false">Cancelar</button>
          <button class="btn-reject" :disabled="actionLoading" @click="rechazar">
            {{ actionLoading ? 'Procesando...' : 'Confirmar rechazo' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import {
  listPedidos, getPedido, confirmarPedido, rechazarPedido,
  updateChecklist, uploadEvidencia, updateDiagnostico,
  registrarMateriales, submitInforme as apiSubmitInforme,
  evidenciaUrl,
  type ApiPedido, type ApiItemPedido,
} from '../api/pedidos';
import { listInventario, type ApiInventario } from '../api/inventario';

const pedidos = ref<ApiPedido[]>([]);
const loading = ref(false);
const selectedId = ref<string | null>(null);
const selected = ref<ApiPedido | null>(null);
const tab = ref('checklist');

const search = ref('');
const filterEstado = ref('');
const inventario = ref<ApiInventario[]>([]);

const actionLoading = ref(false);
const showRechazar = ref(false);
const rechazarMotivo = ref('');
const rechazarError = ref('');

const checkNota = ref<Record<string, string>>({});

const evForm = ref<{ stage: 'antes' | 'despues'; descripcion: string; file: File | null }>({
  stage: 'antes', descripcion: '', file: null,
});
const uploadingEv = ref(false);
const evError = ref('');

const diagText = ref('');
const savingDiag = ref(false);
const diagError = ref('');

const matSel = ref({ item_id: '', nombre: '', sku: '', precio_unitario: 0, cantidad: 1 });
const matUsados = ref<ApiItemPedido[]>([]);
const savingMat = ref(false);
const matError = ref('');

const informeForm = ref({
  diagnostico_final: '', responsable_local: '', pedido_solicitado: '',
  observaciones: '', recomendaciones: '', firma: null as File | null,
});
const savingInforme = ref(false);
const informeError = ref('');

const tabs = [
  { key: 'checklist', label: 'Checklist' },
  { key: 'evidencias', label: 'Evidencias' },
  { key: 'diagnostico', label: 'Diagnóstico' },
  { key: 'materiales', label: 'Materiales' },
  { key: 'informe', label: 'Informe final' },
];

const filteredPedidos = computed(() => {
  let list = pedidos.value;
  if (search.value) {
    const q = search.value.toLowerCase();
    list = list.filter(p =>
      p.codigo.toLowerCase().includes(q) ||
      p.cliente_nombre.toLowerCase().includes(q) ||
      p.titulo.toLowerCase().includes(q)
    );
  }
  if (filterEstado.value) list = list.filter(p => p.estado === filterEstado.value);
  return list;
});

const pedidosPorConfirmar = computed(() => pedidos.value.filter(p => p.estado === 'por-confirmar'));
const pedidosEnCurso = computed(() => pedidos.value.filter(p => ['confirmado', 'en-labor'].includes(p.estado)));

function estadoLabel(e: string) {
  const map: Record<string, string> = {
    'por-confirmar': 'Por confirmar', confirmado: 'Confirmado', rechazado: 'Rechazado',
    'en-labor': 'En labor', 'cierre-tecnico': 'Cierre técnico',
    completado: 'Completado', 'dado-de-baja': 'Dado de baja',
  };
  return map[e] || e;
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' });
}

function updateList(p: ApiPedido) {
  const idx = pedidos.value.findIndex(x => x.id === p.id);
  if (idx >= 0) pedidos.value[idx] = p;
}

async function loadPedidos() {
  loading.value = true;
  try {
    pedidos.value = await listPedidos();
  } finally {
    loading.value = false;
  }
}

async function selectPedido(id: string) {
  selectedId.value = id;
  tab.value = 'checklist';
  selected.value = await getPedido(id);
  diagText.value = selected.value.diagnostico_tecnico || '';
  matUsados.value = [];
  checkNota.value = {};
  informeForm.value = {
    diagnostico_final: selected.value.informe?.diagnostico_final || '',
    responsable_local: selected.value.informe?.responsable_local || '',
    pedido_solicitado: selected.value.informe?.pedido_solicitado || '',
    observaciones: selected.value.informe?.observaciones || '',
    recomendaciones: selected.value.informe?.recomendaciones || '',
    firma: null,
  };
}

async function confirmar() {
  if (!selected.value) return;
  actionLoading.value = true;
  try {
    const p = await confirmarPedido(selected.value.id);
    selected.value = p;
    updateList(p);
  } finally {
    actionLoading.value = false;
  }
}

async function rechazar() {
  if (!selected.value || !rechazarMotivo.value.trim()) {
    rechazarError.value = 'El motivo es obligatorio.';
    return;
  }
  actionLoading.value = true;
  rechazarError.value = '';
  try {
    const p = await rechazarPedido(selected.value.id, rechazarMotivo.value);
    selected.value = p;
    updateList(p);
    showRechazar.value = false;
    rechazarMotivo.value = '';
  } catch (e: unknown) {
    rechazarError.value = e instanceof Error ? e.message : 'Error al rechazar';
  } finally {
    actionLoading.value = false;
  }
}

async function marcarChecklist(step_id: string) {
  if (!selected.value) return;
  actionLoading.value = true;
  try {
    const nota = checkNota.value[step_id] || '';
    const p = await updateChecklist(selected.value.id, step_id, true, nota);
    selected.value = p;
    updateList(p);
    delete checkNota.value[step_id];
  } finally {
    actionLoading.value = false;
  }
}

function onFileChange(e: Event) {
  evForm.value.file = (e.target as HTMLInputElement).files?.[0] ?? null;
}

async function uploadEv() {
  if (!selected.value || !evForm.value.file) return;
  uploadingEv.value = true;
  evError.value = '';
  try {
    const p = await uploadEvidencia(
      selected.value.id,
      evForm.value.file,
      evForm.value.descripcion,
      evForm.value.stage,
    );
    selected.value = p;
    updateList(p);
    evForm.value = { stage: 'despues', descripcion: '', file: null };
  } catch (e: unknown) {
    evError.value = e instanceof Error ? e.message : 'Error al subir evidencia';
  } finally {
    uploadingEv.value = false;
  }
}

async function saveDiag() {
  if (!selected.value) return;
  savingDiag.value = true;
  diagError.value = '';
  try {
    const p = await updateDiagnostico(selected.value.id, diagText.value);
    selected.value = p;
    updateList(p);
  } catch (e: unknown) {
    diagError.value = e instanceof Error ? e.message : 'Error';
  } finally {
    savingDiag.value = false;
  }
}

function onMatChange() {
  const item = inventario.value.find(i => i.id === matSel.value.item_id);
  if (item) {
    matSel.value.nombre = item.nombre;
    matSel.value.sku = item.sku;
    matSel.value.precio_unitario = item.precio_unitario;
  }
}

function addMat() {
  if (!matSel.value.item_id || matSel.value.cantidad < 1) return;
  matUsados.value.push({
    item_id: matSel.value.item_id,
    nombre: matSel.value.nombre,
    sku: matSel.value.sku,
    precio_unitario: matSel.value.precio_unitario,
    cantidad: matSel.value.cantidad,
  });
  matSel.value = { item_id: '', nombre: '', sku: '', precio_unitario: 0, cantidad: 1 };
}

async function saveMateriales() {
  if (!selected.value || !matUsados.value.length) return;
  savingMat.value = true;
  matError.value = '';
  try {
    const p = await registrarMateriales(selected.value.id, matUsados.value);
    selected.value = p;
    updateList(p);
    matUsados.value = [];
  } catch (e: unknown) {
    matError.value = e instanceof Error ? e.message : 'Error al registrar materiales';
  } finally {
    savingMat.value = false;
  }
}

function onFirmaChange(e: Event) {
  informeForm.value.firma = (e.target as HTMLInputElement).files?.[0] ?? null;
}

async function submitInforme() {
  if (!selected.value) return;
  savingInforme.value = true;
  informeError.value = '';
  try {
    const p = await apiSubmitInforme(selected.value.id, {
      diagnostico_final: informeForm.value.diagnostico_final,
      responsable_local: informeForm.value.responsable_local,
      pedido_solicitado: informeForm.value.pedido_solicitado,
      observaciones: informeForm.value.observaciones,
      recomendaciones: informeForm.value.recomendaciones,
      firma_cliente: informeForm.value.firma,
    });
    selected.value = p;
    updateList(p);
  } catch (e: unknown) {
    informeError.value = e instanceof Error ? e.message : 'Error al enviar informe';
  } finally {
    savingInforme.value = false;
  }
}

onMounted(async () => {
  await Promise.all([
    loadPedidos(),
    listInventario({ activo: true }).then(v => { inventario.value = v; }),
  ]);
});
</script>

<style scoped>
.tecnico-view { display: flex; flex-direction: column; gap: 1rem; height: 100%; }

.tv-header { display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.5rem; background: var(--surface, #1e293b); border-radius: 0.75rem; }
.tv-header h2 { margin: 0; font-size: 1.25rem; color: var(--text-primary, #f1f5f9); }
.tv-header p { margin: 0; font-size: 0.8rem; color: var(--text-muted, #94a3b8); }
.header-stats { display: flex; gap: 0.5rem; }
.stat-pill { background: var(--bg, #0f172a); border-radius: 999px; padding: 0.3rem 0.75rem; font-size: 0.8rem; color: var(--text-muted, #94a3b8); display: flex; gap: 0.35rem; align-items: center; }
.stat-pill span { font-weight: 700; color: var(--text-primary, #f1f5f9); }
.stat-pill.active span { color: #4ade80; }

.tv-layout { display: grid; grid-template-columns: 300px 1fr; gap: 1rem; flex: 1; min-height: 0; }

.tv-sidebar { background: var(--surface, #1e293b); border-radius: 0.75rem; display: flex; flex-direction: column; overflow: hidden; }
.tv-filters { padding: 0.75rem; display: flex; flex-direction: column; gap: 0.5rem; border-bottom: 1px solid var(--border, #334155); }
.tv-search { width: 100%; padding: 0.5rem 0.75rem; border: 1px solid var(--border, #334155); border-radius: 0.5rem; background: var(--bg, #0f172a); color: var(--text-primary, #f1f5f9); font-size: 0.8rem; }
.tv-select { padding: 0.4rem 0.5rem; border: 1px solid var(--border, #334155); border-radius: 0.5rem; background: var(--bg, #0f172a); color: var(--text-primary, #f1f5f9); font-size: 0.75rem; width: 100%; }
.tv-list { flex: 1; overflow-y: auto; padding: 0.5rem; display: flex; flex-direction: column; gap: 0.35rem; }
.tv-empty { color: var(--text-muted, #94a3b8); font-size: 0.85rem; padding: 1rem; text-align: center; }

.tv-item { background: var(--bg, #0f172a); border: 1px solid var(--border, #334155); border-radius: 0.5rem; padding: 0.75rem; text-align: left; cursor: pointer; transition: all 0.15s; width: 100%; }
.tv-item:hover { border-color: #6366f1; }
.tv-item.active { border-color: #6366f1; background: rgba(99,102,241,0.1); }
.tv-item.urgent { border-left: 3px solid #fb923c; }
.tv-item.pending { border-left: 3px solid #fbbf24; }
.tv-item-top { display: flex; justify-content: space-between; margin-bottom: 0.2rem; }
.tv-item-top strong { font-size: 0.85rem; color: var(--text-primary, #f1f5f9); }
.tv-item-cliente { font-size: 0.8rem; color: var(--text-secondary, #cbd5e1); }
.tv-item-titulo { font-size: 0.75rem; color: var(--text-muted, #94a3b8); margin: 0.1rem 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tv-item-bottom { display: flex; justify-content: space-between; margin-top: 0.3rem; }
.tv-fecha { font-size: 0.7rem; color: var(--text-muted, #94a3b8); }
.pending-indicator { font-size: 0.7rem; color: #fbbf24; font-weight: 600; margin-top: 0.25rem; }

.tv-badge { font-size: 0.65rem; padding: 0.15rem 0.5rem; border-radius: 999px; font-weight: 600; text-transform: uppercase; }
.pr-baja { background: #1e293b; color: #94a3b8; }
.pr-media { background: rgba(234,179,8,0.2); color: #fbbf24; }
.pr-alta { background: rgba(249,115,22,0.2); color: #fb923c; }
.pr-critica { background: rgba(239,68,68,0.2); color: #f87171; }

.tv-estado { font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 999px; }
.es-por-confirmar { background: rgba(251,191,36,0.2); color: #fbbf24; }
.es-confirmado { background: rgba(34,197,94,0.2); color: #86efac; }
.es-en-labor { background: rgba(59,130,246,0.2); color: #93c5fd; }
.es-cierre-tecnico { background: rgba(168,85,247,0.2); color: #d8b4fe; }
.es-completado { background: rgba(34,197,94,0.3); color: #4ade80; }
.es-dado-de-baja { background: rgba(100,116,139,0.2); color: #94a3b8; }

.tv-main { overflow-y: auto; }
.tv-empty-detail { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; background: var(--surface, #1e293b); border-radius: 0.75rem; color: var(--text-muted, #94a3b8); }
.empty-icon { font-size: 3rem; margin-bottom: 0.5rem; }

.tv-card { background: var(--surface, #1e293b); border-radius: 0.75rem; padding: 1.25rem; display: flex; flex-direction: column; gap: 1rem; }
.tv-card-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem; flex-wrap: wrap; }
.tv-card-head h3 { margin: 0; font-size: 1rem; color: var(--text-primary, #f1f5f9); }
.tv-card-head p { margin: 0; font-size: 0.8rem; color: var(--text-muted, #94a3b8); }
.tv-desc { font-size: 0.8rem !important; color: var(--text-secondary, #cbd5e1) !important; margin-top: 0.25rem !important; }
.head-badges { display: flex; gap: 0.4rem; align-items: center; flex-wrap: wrap; flex-shrink: 0; }

.action-card { background: rgba(251,191,36,0.08); border: 1px solid rgba(251,191,36,0.3); border-radius: 0.5rem; padding: 1rem; }
.action-card h4 { margin: 0 0 0.4rem; color: #fbbf24; font-size: 0.9rem; }
.action-card p { margin: 0 0 0.75rem; font-size: 0.85rem; color: var(--text-secondary, #cbd5e1); }
.action-btns { display: flex; gap: 0.5rem; flex-wrap: wrap; }

.tv-section h4 { margin: 0 0 0.5rem; font-size: 0.85rem; color: var(--text-secondary, #cbd5e1); }

.tv-tabs { display: flex; gap: 0.25rem; border-bottom: 1px solid var(--border, #334155); padding-bottom: 0.5rem; flex-wrap: wrap; }
.tab-btn { padding: 0.4rem 0.75rem; border: none; border-radius: 0.4rem; background: none; color: var(--text-muted, #94a3b8); cursor: pointer; font-size: 0.8rem; transition: all 0.15s; }
.tab-btn:hover { color: var(--text-primary, #f1f5f9); }
.tab-btn.active { background: rgba(99,102,241,0.15); color: #a5b4fc; font-weight: 600; }
.tab-content { min-height: 200px; }

.checklist-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 0.75rem; }
.check-card { background: var(--bg, #0f172a); border-radius: 0.5rem; padding: 0.75rem; border: 1px solid var(--border, #334155); }
.check-card.done { border-color: rgba(74,222,128,0.4); background: rgba(34,197,94,0.05); }
.check-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.4rem; }
.check-icon { font-size: 1.1rem; color: var(--text-muted, #94a3b8); }
.check-card.done .check-icon { color: #4ade80; }
.check-header strong { font-size: 0.85rem; color: var(--text-primary, #f1f5f9); flex: 1; }
.check-header small { font-size: 0.7rem; color: var(--text-muted, #94a3b8); }
.check-nota { font-size: 0.75rem; color: var(--text-muted, #94a3b8); font-style: italic; margin-bottom: 0.4rem; }
.check-actions { display: flex; flex-direction: column; gap: 0.4rem; }
.check-input { padding: 0.35rem 0.5rem; border: 1px solid var(--border, #334155); border-radius: 0.4rem; background: var(--surface, #1e293b); color: var(--text-primary, #f1f5f9); font-size: 0.8rem; width: 100%; }

.ev-upload { background: var(--bg, #0f172a); border-radius: 0.5rem; padding: 0.75rem; }
.ev-upload h4 { margin: 0 0 0.5rem; font-size: 0.85rem; color: var(--text-secondary, #cbd5e1); }
.upload-form { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
.ev-select { padding: 0.4rem 0.5rem; border: 1px solid var(--border, #334155); border-radius: 0.4rem; background: var(--surface, #1e293b); color: var(--text-primary, #f1f5f9); font-size: 0.8rem; }
.ev-input { padding: 0.4rem 0.5rem; border: 1px solid var(--border, #334155); border-radius: 0.4rem; background: var(--surface, #1e293b); color: var(--text-primary, #f1f5f9); font-size: 0.8rem; flex: 1; min-width: 150px; }
.file-label { padding: 0.4rem 0.75rem; background: var(--surface, #1e293b); border: 1px solid var(--border, #334155); border-radius: 0.4rem; cursor: pointer; font-size: 0.8rem; color: var(--text-secondary, #cbd5e1); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 200px; }
.ev-gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 0.75rem; margin-top: 0.75rem; }
.ev-card { background: var(--bg, #0f172a); border-radius: 0.5rem; overflow: hidden; }
.ev-card img { width: 100%; height: 100px; object-fit: cover; }
.ev-info { padding: 0.4rem; display: flex; flex-direction: column; gap: 0.15rem; }
.ev-stage { font-size: 0.65rem; padding: 0.1rem 0.35rem; border-radius: 999px; width: fit-content; }
.stage-antes { background: rgba(234,179,8,0.2); color: #fbbf24; }
.stage-despues { background: rgba(34,197,94,0.2); color: #4ade80; }
.ev-info small { font-size: 0.7rem; color: var(--text-muted, #94a3b8); }

.tv-textarea { width: 100%; padding: 0.6rem 0.75rem; border: 1px solid var(--border, #334155); border-radius: 0.5rem; background: var(--bg, #0f172a); color: var(--text-primary, #f1f5f9); font-size: 0.85rem; resize: vertical; font-family: inherit; box-sizing: border-box; }
.tv-hint { font-size: 0.8rem; color: var(--text-muted, #94a3b8); margin: 0 0 0.5rem; }

.item-adder { display: flex; gap: 0.5rem; margin-bottom: 0.5rem; align-items: center; flex-wrap: wrap; }
.qty-input { padding: 0.4rem 0.5rem; border: 1px solid var(--border, #334155); border-radius: 0.4rem; background: var(--bg, #0f172a); color: var(--text-primary, #f1f5f9); font-size: 0.8rem; width: 80px; }
.items-table { background: var(--bg, #0f172a); border-radius: 0.4rem; overflow: hidden; }
.item-row { display: grid; grid-template-columns: 2fr 1fr 0.5fr 1fr 1fr 30px; padding: 0.4rem 0.5rem; font-size: 0.75rem; gap: 0.25rem; align-items: center; }
.item-row.header-row { color: var(--text-muted, #94a3b8); background: rgba(255,255,255,0.03); font-weight: 600; font-size: 0.7rem; }
.item-row:not(.header-row) { color: var(--text-secondary, #cbd5e1); border-top: 1px solid var(--border, #334155); }
.mt-4 { margin-top: 1rem; }
.mt-4 h5 { margin: 0 0 0.5rem; font-size: 0.8rem; color: var(--text-secondary, #cbd5e1); }

.informe-done { background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.3); border-radius: 0.5rem; padding: 0.75rem; }
.informe-done h4 { margin: 0 0 0.75rem; color: #4ade80; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.info-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.4rem; }
.info-list li { display: flex; justify-content: space-between; font-size: 0.8rem; gap: 0.5rem; }
.info-list li span { color: var(--text-muted, #94a3b8); flex-shrink: 0; }
.info-list li strong { color: var(--text-primary, #f1f5f9); text-align: right; }
.informe-form { display: flex; flex-direction: column; gap: 0.75rem; }
.informe-form h4 { margin: 0; font-size: 0.9rem; color: var(--text-primary, #f1f5f9); }
.informe-form label { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.8rem; color: var(--text-muted, #94a3b8); }
.informe-form input, .informe-form textarea { padding: 0.5rem 0.65rem; border: 1px solid var(--border, #334155); border-radius: 0.4rem; background: var(--bg, #0f172a); color: var(--text-primary, #f1f5f9); font-size: 0.85rem; font-family: inherit; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.form-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 0.25rem; }
.form-error { color: #f87171; font-size: 0.8rem; margin: 0; }

.btn-primary { padding: 0.5rem 1rem; background: #6366f1; color: #fff; border: none; border-radius: 0.4rem; cursor: pointer; font-size: 0.85rem; font-weight: 600; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-ghost { padding: 0.5rem 1rem; background: transparent; color: var(--text-secondary, #cbd5e1); border: 1px solid var(--border, #334155); border-radius: 0.4rem; cursor: pointer; font-size: 0.85rem; }
.btn-confirm { padding: 0.5rem 1.25rem; background: #16a34a; color: #fff; border: none; border-radius: 0.4rem; cursor: pointer; font-size: 0.85rem; font-weight: 600; }
.btn-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-reject { padding: 0.5rem 1.25rem; background: #dc2626; color: #fff; border: none; border-radius: 0.4rem; cursor: pointer; font-size: 0.85rem; font-weight: 600; }
.btn-reject:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-complete { padding: 0.35rem 0.75rem; background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); border-radius: 0.4rem; cursor: pointer; font-size: 0.78rem; white-space: nowrap; }
.btn-complete:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-upload { padding: 0.4rem 0.75rem; background: rgba(99,102,241,0.15); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.3); border-radius: 0.4rem; cursor: pointer; font-size: 0.8rem; white-space: nowrap; }
.btn-upload:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-add { padding: 0.4rem 0.75rem; background: rgba(99,102,241,0.15); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.3); border-radius: 0.4rem; cursor: pointer; font-size: 0.8rem; white-space: nowrap; }
.btn-remove { padding: 0.15rem 0.35rem; background: rgba(239,68,68,0.1); color: #f87171; border: none; border-radius: 0.25rem; cursor: pointer; font-size: 0.75rem; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.55); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: var(--surface, #1e293b); border-radius: 0.75rem; padding: 1.5rem; width: 420px; max-width: 95vw; display: flex; flex-direction: column; gap: 0.75rem; }
.modal h3 { margin: 0; color: var(--text-primary, #f1f5f9); }
.modal p { margin: 0; font-size: 0.85rem; color: var(--text-secondary, #cbd5e1); }
.modal label { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.8rem; color: var(--text-muted, #94a3b8); }
.modal textarea { padding: 0.5rem; border: 1px solid var(--border, #334155); border-radius: 0.4rem; background: var(--bg, #0f172a); color: var(--text-primary, #f1f5f9); resize: vertical; font-family: inherit; }
.modal-actions { display: flex; justify-content: flex-end; gap: 0.5rem; }
</style>
