<template>
  <section class="tecnico-view">
    <header class="head card">
      <div>
        <h2>Mis Pedidos Tecnico</h2>
        <p>Ejecucion por fases con evidencia obligatoria e informe tecnico final.</p>
      </div>
      <div class="head-actions">
        <button class="btn ghost" @click="showCreatePedido = !showCreatePedido">
          {{ showCreatePedido ? 'Cerrar creador' : 'Crear pedido rapido' }}
        </button>
      </div>
    </header>

    <div class="layout">
      <aside class="list card">
        <div class="list-head">
          <h3>Pedidos asignados</h3>
          <label>
            Tecnico
            <select v-model="tecnicoActual" @change="saveTecnicoActual">
              <option v-for="name in tecnicoOptions" :key="name" :value="name">{{ name }}</option>
            </select>
          </label>
          <input
            v-model="searchQuery"
            class="list-search"
            type="search"
            placeholder="Buscar por OT, cliente o servicio"
          />
          <p v-if="bridge.backendError || actionError" class="camera-error">
            {{ actionError || bridge.backendError }}
          </p>
        </div>

        <div class="list-body">
          <div v-if="pedidosAsignados.length === 0" class="empty">
            No hay pedidos asignados para {{ tecnicoActual }}.
          </div>

          <button
            v-for="pedido in pedidosAsignados"
            :key="pedido.id"
            class="pedido-item"
            :class="{ active: selectedPedidoId === pedido.id }"
            @click="openPedido(pedido.id)"
          >
            <div class="item-top">
              <strong>{{ pedido.code }}</strong>
              <span>{{ pedido.status }}</span>
            </div>
            <p>{{ pedido.client }}</p>
            <small>{{ pedido.service }}</small>
          </button>
        </div>
      </aside>

      <article class="detail card" v-if="selectedPedido">
        <section class="panel workflow-panel">
          <div class="workflow-head">
            <div>
              <h3>Flujo operativo del pedido</h3>
              <p class="muted">La fase avanza automaticamente al completar tareas clave.</p>
            </div>
            <div class="workflow-head-actions">
              <span class="state-chip">Estado: {{ normalizedSelectedStatus }}</span>
              <button v-if="selectedStatusKey === 'por-confirmar'" class="btn primary" @click="confirmSelectedPedido">
                Confirmar pedido
              </button>
            </div>
          </div>

          <div class="workflow-rail" :style="{ '--workflow-progress': `${workflowProgress}%` }">
            <div
              v-for="(phase, index) in workflowPhases"
              :key="phase.key"
              class="workflow-node"
              :class="{
                done: index < currentWorkflowIndex,
                active: index === currentWorkflowIndex,
                upcoming: index > currentWorkflowIndex,
              }"
            >
              <span class="workflow-circle">{{ index + 1 }}</span>
              <strong class="workflow-label">{{ phase.label }}</strong>
            </div>
          </div>
        </section>

        <section class="panel metrics-panel">
          <h3>Panel del tecnico</h3>
          <div class="metrics-grid">
            <article>
              <span>Asignados</span>
              <strong>{{ pedidosAsignados.length }}</strong>
            </article>
            <article>
              <span>Completados</span>
              <strong>{{ pedidosCompletados }}</strong>
            </article>
            <article>
              <span>Reportes IVT</span>
              <strong>{{ reportesTecnico.length }}</strong>
            </article>
            <article>
              <span>Sin reporte final</span>
              <strong>{{ pedidosSinReporte }}</strong>
            </article>
          </div>
        </section>

        <nav class="tecnico-tabs panel" aria-label="Fases tecnico">
          <button class="tab" :class="{ active: activeTecnicoTab === 'resumen' }" @click="openTab('resumen')">
            Resumen
          </button>
          <button
            class="tab"
            :class="{ active: activeTecnicoTab === 'ejecucion', locked: !isExecutionTabUnlocked }"
            :disabled="!isExecutionTabUnlocked"
            @click="openTab('ejecucion')"
          >
            Ejecucion
          </button>
          <button
            class="tab"
            :class="{ active: activeTecnicoTab === 'evidencias', locked: !isEvidenceTabUnlocked }"
            :disabled="!isEvidenceTabUnlocked"
            @click="openTab('evidencias')"
          >
            Evidencias
          </button>
          <button
            class="tab"
            :class="{ active: activeTecnicoTab === 'informe', locked: !isInformeTabUnlocked }"
            :disabled="!isInformeTabUnlocked"
            @click="openTab('informe')"
          >
            Informe tecnico
          </button>
          <button class="tab" :class="{ active: activeTecnicoTab === 'reportes' }" @click="openTab('reportes')">
            IVT anteriores
          </button>
        </nav>

        <section v-if="activeTecnicoTab === 'resumen'" class="summary-flow">
          <section class="panel">
            <div class="summary-head">
              <div class="summary-title">
                <h3>{{ selectedPedido.code }} - {{ selectedPedido.client }}</h3>
                <p class="muted">{{ selectedPedido.service }}</p>
              </div>
              <div class="summary-meta">
                <span class="chip">Fecha {{ selectedPedido.date }}</span>
                <span class="priority" :data-priority="selectedPedido.priority">{{ selectedPedido.priority }}</span>
              </div>
            </div>

            <div class="summary-grid">
              <div><span>Cuenta</span><strong>{{ selectedPedido.accountCode || '-' }}</strong></div>
              <div><span>Contacto</span><strong>{{ selectedPedido.contactName || '-' }}</strong></div>
              <div><span>Telefono</span><strong>{{ selectedPedido.contactPhone || '-' }}</strong></div>
              <div><span>Direccion</span><strong>{{ selectedPedido.referenceAddress || '-' }}</strong></div>
              <div><span>Distrito</span><strong>{{ selectedPedido.district || '-' }}</strong></div>
              <div><span>Coordenadas</span><strong>{{ selectedPedido.coordinates || '-' }}</strong></div>
            </div>
          </section>

          <section class="panel playbook-panel">
            <div class="playbook-head">
              <h3>Guia tecnica operativa</h3>
              <span class="state-chip">Fase actual: {{ currentWorkflowLabel }}</span>
            </div>
            <p class="muted">{{ selectedServiceGuide.summary }}</p>
            <div class="guide-grid">
              <article v-for="(item, idx) in selectedServiceGuide.tasks" :key="`${selectedPedido.id}-${idx}`" class="guide-card">
                <span class="guide-step">Paso {{ idx + 1 }}</span>
                <p>{{ item }}</p>
              </article>
            </div>
          </section>

          <section class="panel map-panel">
            <div class="map-head">
              <h3>Ubicacion del pedido</h3>
              <small>{{ selectedPedido.coordinates || 'Sin coordenadas' }}</small>
            </div>
            <div ref="mapContainerRef" class="map-canvas"></div>
            <p v-if="!parsedCoordinates" class="muted">
              No se encontraron coordenadas validas. Se muestra un centro referencial.
            </p>
          </section>

          <section v-if="showCreatePedido" class="panel create-box">
            <h3>Crear pedido rapido</h3>
            <div class="create-grid">
              <label>
                Cliente
                <input v-model.trim="createForm.client" type="text" placeholder="Cliente" />
              </label>
              <label>
                Codigo cuenta
                <input v-model.trim="createForm.accountCode" type="text" placeholder="CUE-XXXX" />
              </label>
              <label class="wide">
                Servicio
                <input v-model.trim="createForm.service" type="text" placeholder="Servicio a realizar" />
              </label>
              <label class="wide">
                Diagnostico inicial
                <textarea v-model.trim="createForm.diagnosis" rows="3" placeholder="Describe el problema"></textarea>
              </label>
            </div>
            <div class="actions">
              <button class="btn ghost" @click="resetCreateForm">Limpiar</button>
              <button class="btn primary" :disabled="!canCreatePedido" @click="createPedidoFromTecnico">
                Crear y enviar a coordinador
              </button>
            </div>
          </section>
        </section>

        <section v-else-if="activeTecnicoTab === 'ejecucion'" class="panel">
          <div class="execution-head">
            <div>
              <h3>Checklist de ejecucion</h3>
              <p class="muted">Completa los pasos operativos antes de habilitar evidencias.</p>
            </div>
            <strong>{{ checklistDoneCount }}/{{ checklistForSelected.length }} completados</strong>
          </div>

          <div class="execution-track">
            <span :style="{ width: `${executionProgress}%` }"></span>
          </div>

          <ol class="checklist">
            <li
              v-for="(step, index) in checklistForSelected"
              :key="step.id"
              :class="{
                done: step.done,
                locked: !isStepUnlocked(step.id),
                current: isStepUnlocked(step.id) && !step.done,
              }"
            >
              <div class="step-index">{{ index + 1 }}</div>
              <div class="step-content">
                <div class="step-head">
                  <strong>{{ step.label }}</strong>
                  <span v-if="step.done" class="done-pill">{{ step.doneAt }}</span>
                  <span v-else-if="!isStepUnlocked(step.id)" class="locked-pill">Bloqueado</span>
                  <span v-else class="open-pill">Pendiente</span>
                </div>

                <div v-if="step.id === 'nota-adicional'" class="step-note">
                  <label>
                    Informacion adicional
                    <textarea
                      v-model.trim="additionalNote"
                      rows="3"
                      :disabled="!isStepUnlocked(step.id) || step.done"
                      placeholder="Describe hallazgos, pruebas y datos relevantes"
                    ></textarea>
                  </label>
                  <div class="actions">
                    <button
                      class="btn primary save-note-btn"
                      :disabled="!isStepUnlocked(step.id) || step.done || !additionalNote.trim()"
                      @click="saveAdditionalNote"
                    >
                      Guardar nota
                    </button>
                  </div>
                </div>

                <div v-else class="step-actions">
                  <button
                    class="btn mini"
                    :disabled="!isStepUnlocked(step.id) || step.done"
                    @click="completeSimpleStep(step.id)"
                  >
                    Marcar paso completado
                  </button>
                </div>
              </div>
            </li>
          </ol>
        </section>

        <section v-else-if="activeTecnicoTab === 'evidencias'" class="detail-flow">
          <section class="panel phase-status-panel">
            <h3>Evidencias obligatorias</h3>
            <div class="phase-status-grid">
              <article :class="{ complete: hasBeforeEvidence }">
                <span>Antes del servicio</span>
                <strong>{{ hasBeforeEvidence ? 'Completado' : 'Pendiente' }}</strong>
              </article>
              <article :class="{ complete: hasAfterEvidence }">
                <span>Despues del servicio</span>
                <strong>{{ hasAfterEvidence ? 'Completado' : 'Pendiente' }}</strong>
              </article>
            </div>
            <p class="muted">Debes completar ambos bloques para habilitar Informe tecnico.</p>
          </section>

          <section class="panel evidence-step">
            <h3>Bloque antes del servicio</h3>
            <div class="evidence-actions">
              <label class="file-btn">
                <input type="file" accept="image/*" multiple @change="onFileInput($event, 'antes')" />
                Subir archivos
              </label>
              <button class="btn ghost" @click="startCamera('antes')">Abrir camara</button>
            </div>
            <div v-if="pendingAntes.length" class="evidence-grid">
              <article v-for="item in pendingAntes" :key="item.id" class="evidence-item">
                <img :src="item.url" :alt="item.name" />
                <small>{{ item.name }}</small>
                <label>
                  Descripcion de evidencia
                  <input v-model.trim="item.description" type="text" placeholder="Describe brevemente esta imagen" />
                </label>
              </article>
            </div>
            <div class="actions">
              <button class="btn ghost" :disabled="pendingAntes.length === 0" @click="pendingAntes = []">Limpiar</button>
              <button class="btn primary" :disabled="!canSendAntes" @click="sendEvidencias('antes')">
                Enviar bloque antes
              </button>
            </div>
          </section>

          <section class="panel evidence-step">
            <h3>Bloque despues del servicio</h3>
            <div class="evidence-actions">
              <label class="file-btn">
                <input type="file" accept="image/*" multiple @change="onFileInput($event, 'despues')" />
                Subir archivos
              </label>
              <button class="btn ghost" @click="startCamera('despues')">Abrir camara</button>
            </div>
            <div v-if="pendingDespues.length" class="evidence-grid">
              <article v-for="item in pendingDespues" :key="item.id" class="evidence-item">
                <img :src="item.url" :alt="item.name" />
                <small>{{ item.name }}</small>
                <label>
                  Descripcion de evidencia
                  <input v-model.trim="item.description" type="text" placeholder="Describe brevemente esta imagen" />
                </label>
              </article>
            </div>
            <div class="actions">
              <button class="btn ghost" :disabled="pendingDespues.length === 0" @click="pendingDespues = []">Limpiar</button>
              <button class="btn primary" :disabled="!canSendDespues" @click="sendEvidencias('despues')">
                Enviar bloque despues
              </button>
            </div>
          </section>

          <section class="panel" v-if="cameraActive">
            <h3>Camara activa ({{ cameraStage === 'antes' ? 'ANTES' : 'DESPUES' }})</h3>
            <p class="muted">Captura y agrega la imagen al bloque correspondiente.</p>
            <p v-if="cameraError" class="camera-error">{{ cameraError }}</p>
            <div class="camera-wrap">
              <video ref="videoRef" autoplay playsinline muted></video>
              <div class="actions">
                <button class="btn primary" @click="captureFromCamera">Capturar foto</button>
                <button class="btn ghost" @click="stopCamera">Cerrar camara</button>
              </div>
            </div>
          </section>

          <section class="panel">
            <h3>Evidencias enviadas</h3>
            <div v-if="evidenciasForSelected.length" class="evidence-sent-grid">
              <article v-for="item in evidenciasForSelected" :key="item.id" class="evidence-item sent">
                <img :src="item.url" :alt="item.name" />
                <small>{{ item.stage.toUpperCase() }} - {{ item.createdAt }}</small>
                <small v-if="item.description">{{ item.description }}</small>
              </article>
            </div>
            <p v-else class="muted">Aun no se enviaron evidencias.</p>
          </section>
        </section>

        <section v-else-if="activeTecnicoTab === 'informe'" class="panel">
          <h3>Formato de servicio tecnico</h3>
          <p class="muted">Completa el formato final y registra la firma del cliente.</p>

          <div class="service-grid">
            <label>
              Cliente
              <input v-model="reportForm.cliente" type="text" readonly />
            </label>
            <label>
              Responsable del local
              <input v-model.trim="reportForm.responsableLocal" type="text" placeholder="Nombre del responsable" />
            </label>
            <label class="wide">
              Pedido solicitado
              <input v-model.trim="reportForm.pedidoSolicitado" type="text" placeholder="Servicio solicitado" />
            </label>
            <label class="wide">
              Observaciones
              <textarea v-model.trim="reportForm.observaciones" rows="3" placeholder="Observaciones del cliente y del tecnico"></textarea>
            </label>
            <label class="wide">
              Recomendaciones
              <textarea v-model.trim="reportForm.recomendaciones" rows="3" placeholder="Recomendaciones para el cliente"></textarea>
            </label>
          </div>

          <div class="signature-box">
            <div class="signature-head">
              <strong>Firma del cliente (obligatoria)</strong>
              <button class="btn ghost" @click="clearSignature">Limpiar firma</button>
            </div>
            <canvas
              ref="signatureCanvasRef"
              class="signature-canvas"
              @pointerdown="startSignature"
              @pointermove="moveSignature"
              @pointerup="endSignature"
              @pointerleave="endSignature"
            ></canvas>
            <small v-if="!hasSignature" class="muted">Dibuja la firma para continuar.</small>
          </div>

          <div class="actions">
            <button class="btn primary" :disabled="!canSubmitServiceReport" @click="submitServiceReport">
              Enviar formato al coordinador
            </button>
          </div>
        </section>

        <section v-else class="panel">
          <h3>IVT / Reportes anteriores</h3>
          <p class="muted">Historial de formatos de servicio tecnico enviados por {{ tecnicoActual }}.</p>

          <div v-if="reportesTecnico.length === 0" class="empty">Aun no hay reportes enviados.</div>

          <div v-else class="reports-list">
            <article v-for="report in reportesTecnico" :key="report.id" class="report-item">
              <header>
                <strong>{{ report.pedidoId }}</strong>
                <span>{{ report.createdAt }}</span>
              </header>
              <p><strong>Cliente:</strong> {{ report.cliente }}</p>
              <p><strong>Responsable local:</strong> {{ report.responsableLocal }}</p>
              <p><strong>Pedido solicitado:</strong> {{ report.pedidoSolicitado }}</p>
              <p><strong>Observaciones:</strong> {{ report.observaciones }}</p>
              <p><strong>Recomendaciones:</strong> {{ report.recomendaciones }}</p>
              <details>
                <summary>Ver firma del cliente</summary>
                <img :src="report.firmaCliente" alt="Firma cliente" class="signature-preview" />
              </details>
            </article>
          </div>
        </section>
      </article>

      <article v-else class="detail card empty-detail">
        <p>Selecciona un pedido asignado para empezar.</p>
      </article>
    </div>

    <canvas ref="captureCanvasRef" class="hidden-canvas"></canvas>
  </section>
</template>

<script setup lang="ts">
import * as L from 'leaflet';
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import type { ChecklistStepId, EvidenciaStage } from '../stores/tecnicoBridgeStore';
import { useTecnicoBridgeStore } from '../stores/tecnicoBridgeStore';

interface PendingEvidence {
  id: string;
  name: string;
  url: string;
  source: 'archivo' | 'camara';
  description: string;
}

type TecnicoTab = 'resumen' | 'ejecucion' | 'evidencias' | 'informe' | 'reportes';
type OperationalStatusKey = 'por-confirmar' | 'confirmado' | 'en-labor' | 'cierre-tecnico' | 'facturacion' | 'dado-de-baja';
type WorkflowPhaseKey = 'confirmacion' | 'ejecucion' | 'evidencias' | 'cierre-tecnico' | 'facturacion';

const bridge = useTecnicoBridgeStore();
const tecnicoActual = ref('');
const searchQuery = ref('');
const selectedPedidoId = ref('');
const activeTecnicoTab = ref<TecnicoTab>('resumen');
const showCreatePedido = ref(false);
const actionError = ref('');

const createForm = reactive({
  client: '',
  accountCode: '',
  service: '',
  diagnosis: '',
});

const reportForm = reactive({
  cliente: '',
  responsableLocal: '',
  pedidoSolicitado: '',
  observaciones: '',
  recomendaciones: '',
});

const additionalNote = ref('');
const pendingAntes = ref<PendingEvidence[]>([]);
const pendingDespues = ref<PendingEvidence[]>([]);

const SERVICE_PLAYBOOK: Array<{ regex: RegExp; summary: string; tasks: string[] }> = [
  {
    regex: /electr/i,
    summary: 'Prioriza seguridad electrica, continuidad de energia y pruebas funcionales del tablero.',
    tasks: [
      'Verifica fuente principal, llaves termomagneticas y protecciones diferenciales.',
      'Inspecciona cableado, temperatura en puntos criticos y posibles sobrecargas.',
      'Realiza pruebas de voltaje/corriente y confirma estabilidad de operacion.',
      'Documenta recomendaciones preventivas para evitar reincidencias.',
    ],
  },
  {
    regex: /ups|tabler/i,
    summary: 'Enfoca en autonomia, estado de baterias y salud de equipos de respaldo.',
    tasks: [
      'Valida estado de baterias, terminales y alarmas activas del sistema.',
      'Ejecuta prueba de transferencia y retorno para validar respaldo.',
      'Revisa cargas conectadas y distribucion en tableros asociados.',
      'Registra vida util estimada y recambios recomendados.',
    ],
  },
  {
    regex: /bomba|agua|hidraul/i,
    summary: 'Asegura flujo hidraulico estable y funcionamiento seguro de componentes mecanicos.',
    tasks: [
      'Inspecciona valvulas, sellos y tableros de control de arranque.',
      'Confirma presion y caudal en operacion normal.',
      'Evalua vibraciones, ruidos atipicos y temperatura de motor.',
      'Define acciones correctivas y mantenimientos pendientes.',
    ],
  },
  {
    regex: /cable|estructur|red/i,
    summary: 'Garantiza conectividad estable y orden de infraestructura de cableado.',
    tasks: [
      'Revisa integridad fisica de canaletas, patch panels y conectores.',
      'Ejecuta pruebas de continuidad y certificacion de puntos.',
      'Verifica etiquetado y orden logico de los enlaces.',
      'Documenta puntos criticos y mejoras de capacidad.',
    ],
  },
  {
    regex: /.*/,
    summary: 'Sigue el procedimiento estandar: diagnostico, ejecucion segura, validacion y cierre documentado.',
    tasks: [
      'Confirma alcance con el responsable antes de iniciar.',
      'Registra evidencias antes y despues del servicio.',
      'Valida resultado final con pruebas funcionales.',
      'Entrega observaciones y recomendaciones al cliente.',
    ],
  },
];

const workflowPhases: Array<{ key: WorkflowPhaseKey; label: string }> = [
  { key: 'confirmacion', label: 'Confirmacion' },
  { key: 'ejecucion', label: 'Ejecucion' },
  { key: 'evidencias', label: 'Evidencias' },
  { key: 'cierre-tecnico', label: 'Cierre tecnico' },
  { key: 'facturacion', label: 'Facturacion' },
];

function toOperationalStatusKey(rawStatus?: string): OperationalStatusKey {
  const status = (rawStatus || '').toLowerCase();
  if (status.includes('baja')) return 'dado-de-baja';
  if (status.includes('por confirmar')) return 'por-confirmar';
  if (status.includes('confirmado')) return 'confirmado';
  if (status.includes('en labor') || status.includes('proceso')) return 'en-labor';
  if (status.includes('cierre')) return 'cierre-tecnico';
  if (status.includes('factur') || status.includes('complet')) return 'facturacion';
  if (status.includes('pend')) return 'por-confirmar';
  return 'por-confirmar';
}

const tecnicoOptions = computed(() => {
  const names = new Set<string>([tecnicoActual.value]);
  if (bridge.currentTecnicoNombre.value) names.add(bridge.currentTecnicoNombre.value);
  bridge.allPedidosForTecnico.value.forEach((pedido) => {
    if (pedido.tech) names.add(pedido.tech);
  });
  return Array.from(names).sort((a, b) => a.localeCompare(b, 'es'));
});

const pedidosAsignados = computed(() => {
  const query = searchQuery.value.trim().toLowerCase();
  const tecnicoFiltro = tecnicoActual.value.trim().toLowerCase();

  return bridge.allPedidosForTecnico.value
    .filter((pedido) => !tecnicoFiltro || (pedido.tech || '').toLowerCase() === tecnicoFiltro)
    .filter((pedido) => {
      if (!query) return true;
      return [pedido.code, pedido.client, pedido.service].join(' ').toLowerCase().includes(query);
    });
});

const pedidosCompletados = computed(() => {
  return pedidosAsignados.value.filter((pedido) => toOperationalStatusKey(pedido.status) === 'facturacion').length;
});

const pedidosSinReporte = computed(() => {
  return pedidosAsignados.value.filter((pedido) => bridge.getServiceReports(pedido.id).length === 0).length;
});

const selectedPedido = computed(() =>
  pedidosAsignados.value.find((pedido) => pedido.id === selectedPedidoId.value) || null
);

const parsedCoordinates = computed(() => {
  const raw = selectedPedido.value?.coordinates;
  if (!raw) return null;
  const parts = raw.split(',').map((part) => Number(part.trim()));
  if (parts.length !== 2 || parts.some((item) => Number.isNaN(item))) return null;
  const [lat, lng] = parts;
  if (lat < -90 || lat > 90 || lng < -180 || lng > 180) return null;
  return { lat, lng };
});

const selectedServiceGuide = computed(() => {
  const service = (selectedPedido.value?.service || '').toLowerCase();
  const match = SERVICE_PLAYBOOK.find((item) => item.regex.test(service)) || SERVICE_PLAYBOOK[SERVICE_PLAYBOOK.length - 1];
  return {
    summary: match.summary,
    tasks: match.tasks,
  };
});

const selectedStatusKey = computed(() => toOperationalStatusKey(selectedPedido.value?.status));

const normalizedSelectedStatus = computed(() => {
  const labels: Record<OperationalStatusKey, string> = {
    'por-confirmar': 'Por confirmar',
    confirmado: 'Confirmado',
    'en-labor': 'En labor',
    'cierre-tecnico': 'Cierre tecnico',
    facturacion: 'Facturacion',
    'dado-de-baja': 'Dado de baja',
  };
  return labels[selectedStatusKey.value];
});

const hasServiceReportForSelected = computed(() => {
  if (!selectedPedido.value) return false;
  return bridge.getServiceReports(selectedPedido.value.id).length > 0;
});

const currentWorkflowPhase = computed<WorkflowPhaseKey>(() => {
  if (selectedStatusKey.value === 'por-confirmar' || selectedStatusKey.value === 'confirmado') {
    return 'confirmacion';
  }

  if (selectedStatusKey.value === 'facturacion' || hasServiceReportForSelected.value) {
    return 'facturacion';
  }

  if (selectedStatusKey.value === 'cierre-tecnico') {
    return 'cierre-tecnico';
  }

  if (selectedStatusKey.value === 'en-labor') {
    if (!isExecutionComplete.value) return 'ejecucion';
    if (!isEvidenceComplete.value) return 'evidencias';
    return 'cierre-tecnico';
  }

  return 'confirmacion';
});

const currentWorkflowIndex = computed(() => {
  const idx = workflowPhases.findIndex((phase) => phase.key === currentWorkflowPhase.value);
  return idx >= 0 ? idx : 0;
});

const currentWorkflowLabel = computed(() => workflowPhases[currentWorkflowIndex.value]?.label || 'Confirmacion');

const workflowProgress = computed(() => {
  if (workflowPhases.length < 2) return 0;
  return (currentWorkflowIndex.value / (workflowPhases.length - 1)) * 100;
});

const checklistForSelected = computed(() => {
  if (!selectedPedido.value) return [];
  return bridge.getChecklist(selectedPedido.value.id);
});

const checklistDoneCount = computed(() => checklistForSelected.value.filter((step) => step.done).length);
const executionProgress = computed(() => {
  if (!checklistForSelected.value.length) return 0;
  return Math.round((checklistDoneCount.value / checklistForSelected.value.length) * 100);
});
const isExecutionComplete = computed(() => checklistForSelected.value.length > 0 && checklistForSelected.value.every((step) => step.done));

const hasBeforeEvidence = computed(() => {
  if (!selectedPedido.value) return false;
  return bridge.hasEvidenciasStage(selectedPedido.value.id, 'antes');
});

const hasAfterEvidence = computed(() => {
  if (!selectedPedido.value) return false;
  return bridge.hasEvidenciasStage(selectedPedido.value.id, 'despues');
});

const isEvidenceComplete = computed(() => hasBeforeEvidence.value && hasAfterEvidence.value);
const isExecutionTabUnlocked = computed(() => selectedStatusKey.value !== 'por-confirmar');
const isEvidenceTabUnlocked = computed(() => isExecutionTabUnlocked.value && isExecutionComplete.value);
const isInformeTabUnlocked = computed(() => isExecutionComplete.value && isEvidenceComplete.value);

const reportesTecnico = computed(() => bridge.getReportsForTecnico(tecnicoActual.value));

const updatesForSelected = computed(() => {
  if (!selectedPedido.value) return [];
  return bridge.getUpdates(selectedPedido.value.id);
});

const evidenciasForSelected = computed(() => {
  if (!selectedPedido.value) return [];
  return bridge.getEvidencias(selectedPedido.value.id);
});

const canSendAntes = computed(() => {
  if (!pendingAntes.value.length) return false;
  return pendingAntes.value.every((item) => item.description.trim().length > 0);
});

const canSendDespues = computed(() => {
  if (!pendingDespues.value.length) return false;
  return pendingDespues.value.every((item) => item.description.trim().length > 0);
});

const canCreatePedido = computed(() => {
  return createForm.client.trim() && createForm.service.trim() && createForm.diagnosis.trim();
});

const canSubmitServiceReport = computed(() => {
  return (
    isInformeTabUnlocked.value
    && reportForm.cliente.trim()
    && reportForm.responsableLocal.trim()
    && reportForm.pedidoSolicitado.trim()
    && reportForm.observaciones.trim()
    && reportForm.recomendaciones.trim()
    && hasSignature.value
  );
});

function saveTecnicoActual() {
  if (!tecnicoActual.value.trim() && bridge.currentTecnicoNombre.value) {
    tecnicoActual.value = bridge.currentTecnicoNombre.value;
  }
}

function openPedido(pedidoId: string) {
  selectedPedidoId.value = pedidoId;
}

function openTab(tab: TecnicoTab) {
  if (tab === 'ejecucion' && !isExecutionTabUnlocked.value) return;
  if (tab === 'evidencias' && !isEvidenceTabUnlocked.value) return;
  if (tab === 'informe' && !isInformeTabUnlocked.value) return;
  activeTecnicoTab.value = tab;
}

async function confirmSelectedPedido() {
  if (!selectedPedido.value || selectedStatusKey.value !== 'por-confirmar') return;

  actionError.value = '';
  try {
    await bridge.addTecnicoUpdate({
      pedidoId: selectedPedido.value.id,
      tecnico: tecnicoActual.value,
      status: 'Confirmado',
      note: 'Pedido confirmado por tecnico. Se habilita fase de ejecucion.',
    });
    activeTecnicoTab.value = 'ejecucion';
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : 'No se pudo confirmar el pedido.';
  }
}

function resetCreateForm() {
  createForm.client = '';
  createForm.accountCode = '';
  createForm.service = '';
  createForm.diagnosis = '';
}

function createPedidoFromTecnico() {
  if (!canCreatePedido.value) return;

  const newPedido = bridge.createPedidoFromTecnico({
    tecnico: tecnicoActual.value,
    client: createForm.client.trim(),
    accountCode: createForm.accountCode.trim() || undefined,
    service: createForm.service.trim(),
    diagnosis: createForm.diagnosis.trim(),
    contactName: tecnicoActual.value,
  });

  selectedPedidoId.value = newPedido.id;
  showCreatePedido.value = false;
  resetCreateForm();
}

function isStepUnlocked(stepId: ChecklistStepId) {
  if (!selectedPedido.value) return false;
  return bridge.canMarkChecklistStep(selectedPedido.value.id, stepId);
}

async function completeSimpleStep(stepId: ChecklistStepId) {
  if (!selectedPedido.value || !isStepUnlocked(stepId)) return;

  actionError.value = '';
  try {
    await bridge.markChecklistStep({
      pedidoId: selectedPedido.value.id,
      stepId,
      done: true,
    });
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : 'No se pudo actualizar el checklist.';
  }
}

async function saveAdditionalNote() {
  if (!selectedPedido.value || !additionalNote.value.trim() || !isStepUnlocked('nota-adicional')) return;

  actionError.value = '';
  try {
    await bridge.markChecklistStep({
      pedidoId: selectedPedido.value.id,
      stepId: 'nota-adicional',
      done: true,
      note: additionalNote.value.trim(),
    });
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : 'No se pudo guardar la nota adicional.';
  }
}

async function readFileAsDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

async function onFileInput(event: Event, stage: EvidenciaStage) {
  if (!selectedPedido.value) return;

  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files || []);
  if (!files.length) return;

  const urls = await Promise.all(files.map((file) => readFileAsDataUrl(file)));
  const mapped = urls.map((url, index) => ({
    id: `file-${Date.now()}-${index}`,
    name: files[index].name,
    url,
    source: 'archivo' as const,
    description: '',
  }));

  if (stage === 'antes') {
    pendingAntes.value = [...mapped, ...pendingAntes.value];
  } else {
    pendingDespues.value = [...mapped, ...pendingDespues.value];
  }

  input.value = '';
}

const cameraActive = ref(false);
const cameraError = ref('');
const cameraStage = ref<EvidenciaStage>('antes');
const videoRef = ref<HTMLVideoElement | null>(null);
const captureCanvasRef = ref<HTMLCanvasElement | null>(null);
let stream: MediaStream | null = null;

async function startCamera(stage: EvidenciaStage) {
  cameraError.value = '';
  cameraStage.value = stage;

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    cameraError.value = 'Este navegador no soporta captura de camara.';
    return;
  }

  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    if (videoRef.value) {
      videoRef.value.srcObject = stream;
      await videoRef.value.play();
    }
    cameraActive.value = true;
  } catch {
    cameraError.value = 'No se pudo acceder a la camara. Revisa permisos y vuelve a intentar.';
    cameraActive.value = false;
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    stream = null;
  }

  if (videoRef.value) {
    videoRef.value.srcObject = null;
  }

  cameraActive.value = false;
}

function captureFromCamera() {
  if (!videoRef.value || !captureCanvasRef.value) return;

  const video = videoRef.value;
  const canvas = captureCanvasRef.value;

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
  const item = {
    id: `cam-${Date.now()}`,
    name: `captura-${new Date().toISOString().slice(11, 19).replace(/:/g, '-')}.jpg`,
    url: dataUrl,
    source: 'camara' as const,
    description: '',
  };

  if (cameraStage.value === 'antes') {
    pendingAntes.value.unshift(item);
  } else {
    pendingDespues.value.unshift(item);
  }
}

async function sendEvidencias(stage: EvidenciaStage) {
  if (!selectedPedido.value) return;

  const list = stage === 'antes' ? pendingAntes.value : pendingDespues.value;
  if (!list.length) return;
  if (list.some((item) => !item.description.trim())) return;

  actionError.value = '';
  try {
    await bridge.addEvidencias({
      pedidoId: selectedPedido.value.id,
      tecnico: tecnicoActual.value,
      stage,
      items: list.map((item) => ({
        name: item.name,
        url: item.url,
        source: item.source,
        description: item.description.trim(),
      })),
    });

    if (stage === 'antes') {
      pendingAntes.value = [];
    } else {
      pendingDespues.value = [];
    }
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : 'No se pudo enviar evidencias.';
  }
}

const signatureCanvasRef = ref<HTMLCanvasElement | null>(null);
const hasSignature = ref(false);
let isSigning = false;

function resizeSignatureCanvas() {
  const canvas = signatureCanvasRef.value;
  if (!canvas) return;

  const ratio = Math.max(window.devicePixelRatio || 1, 1);
  const width = canvas.clientWidth || 520;
  const height = canvas.clientHeight || 160;

  canvas.width = width * ratio;
  canvas.height = height * ratio;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.fillStyle = '#081320';
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = '#f4fbff';
  ctx.lineWidth = 2;
  hasSignature.value = false;
}

function pointerPosition(event: PointerEvent) {
  const canvas = signatureCanvasRef.value;
  if (!canvas) return { x: 0, y: 0 };

  const rect = canvas.getBoundingClientRect();
  return {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top,
  };
}

function startSignature(event: PointerEvent) {
  const canvas = signatureCanvasRef.value;
  if (!canvas) return;
  isSigning = true;
  canvas.setPointerCapture(event.pointerId);

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const point = pointerPosition(event);
  ctx.beginPath();
  ctx.moveTo(point.x, point.y);
}

function moveSignature(event: PointerEvent) {
  if (!isSigning) return;
  const canvas = signatureCanvasRef.value;
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const point = pointerPosition(event);
  ctx.lineTo(point.x, point.y);
  ctx.stroke();
  hasSignature.value = true;
}

function endSignature(event: PointerEvent) {
  const canvas = signatureCanvasRef.value;
  if (!canvas) return;
  if (canvas.hasPointerCapture(event.pointerId)) {
    canvas.releasePointerCapture(event.pointerId);
  }
  isSigning = false;
}

function clearSignature() {
  resizeSignatureCanvas();
}

async function submitServiceReport() {
  if (!selectedPedido.value || !canSubmitServiceReport.value || !signatureCanvasRef.value) return;

  const firma = signatureCanvasRef.value.toDataURL('image/png');

  actionError.value = '';
  try {
    await bridge.submitServiceReport({
      pedidoId: selectedPedido.value.id,
      tecnico: tecnicoActual.value,
      cliente: reportForm.cliente,
      responsableLocal: reportForm.responsableLocal.trim(),
      pedidoSolicitado: reportForm.pedidoSolicitado.trim(),
      observaciones: reportForm.observaciones.trim(),
      recomendaciones: reportForm.recomendaciones.trim(),
      firmaCliente: firma,
    });

    activeTecnicoTab.value = 'reportes';
    clearSignature();
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : 'No se pudo enviar el informe tecnico.';
  }
}

const mapContainerRef = ref<HTMLElement | null>(null);
let mapInstance: L.Map | null = null;
let mapMarker: L.CircleMarker | null = null;
const DEFAULT_COORDS = { lat: -12.0464, lng: -77.0428 };

function initOrUpdateMap() {
  if (!mapContainerRef.value) return;

  if (!mapInstance) {
    mapInstance = L.map(mapContainerRef.value, {
      zoomControl: true,
      attributionControl: true,
    }).setView([DEFAULT_COORDS.lat, DEFAULT_COORDS.lng], 11);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(mapInstance);
  }

  const coords = parsedCoordinates.value;
  if (coords) {
    mapInstance.setView([coords.lat, coords.lng], 15);
    if (!mapMarker) {
      mapMarker = L.circleMarker([coords.lat, coords.lng], {
        radius: 9,
        color: '#79e3c3',
        fillColor: '#16a34a',
        fillOpacity: 0.85,
        weight: 2,
      }).addTo(mapInstance);
    } else {
      mapMarker.setLatLng([coords.lat, coords.lng]);
    }
  } else {
    mapInstance.setView([DEFAULT_COORDS.lat, DEFAULT_COORDS.lng], 11);
    if (mapMarker) {
      mapInstance.removeLayer(mapMarker);
      mapMarker = null;
    }
  }

  mapInstance.invalidateSize();
}

watch(
  pedidosAsignados,
  (next) => {
    if (!next.length) {
      selectedPedidoId.value = '';
      return;
    }

    const exists = next.some((pedido) => pedido.id === selectedPedidoId.value);
    if (!exists) selectedPedidoId.value = next[0].id;
  },
  { immediate: true }
);

watch(
  selectedPedido,
  async (pedido) => {
    if (!pedido) return;

    const noteStep = bridge.getChecklist(pedido.id).find((item) => item.id === 'nota-adicional');
    additionalNote.value = noteStep?.note || '';

    reportForm.cliente = pedido.client;
    reportForm.pedidoSolicitado = pedido.service;
    reportForm.responsableLocal = '';
    reportForm.observaciones = '';
    reportForm.recomendaciones = '';

    activeTecnicoTab.value = 'resumen';
    pendingAntes.value = [];
    pendingDespues.value = [];
    clearSignature();

    await nextTick();
    initOrUpdateMap();
  },
  { immediate: true }
);

watch(activeTecnicoTab, async (tab) => {
  if (tab === 'resumen') {
    await nextTick();
    initOrUpdateMap();
  }

  if (tab === 'informe') {
    await nextTick();
    resizeSignatureCanvas();
  }
});

watch(
  [isExecutionComplete, selectedStatusKey],
  ([executionComplete, statusKey]) => {
    if (!selectedPedido.value) return;
    if (!executionComplete) return;
    if (statusKey !== 'en-labor') return;
    if (activeTecnicoTab.value !== 'evidencias') {
      activeTecnicoTab.value = 'evidencias';
    }
  },
  { immediate: true }
);

watch(
  [isEvidenceComplete, selectedStatusKey],
  ([evidenceComplete, statusKey]) => {
    if (!selectedPedido.value) return;
    if (!evidenceComplete) return;
    if (statusKey !== 'en-labor') return;

    if (activeTecnicoTab.value !== 'informe') {
      activeTecnicoTab.value = 'informe';
    }
  }
);

onMounted(async () => {
  actionError.value = '';
  try {
    await bridge.hydrateFromApi();
    tecnicoActual.value = bridge.currentTecnicoNombre.value || tecnicoOptions.value[0] || '';
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : 'No se pudo cargar pedidos asignados.';
  }
});

onBeforeUnmount(() => {
  stopCamera();
  if (mapInstance) {
    mapInstance.remove();
    mapInstance = null;
  }
});
</script>

<style scoped>
.tecnico-view {
  --bg-card: #0f1c2b;
  --bg-soft: #13263b;
  --text-main: #ebf2fb;
  --text-muted: #9db3cb;
  --border-light: #4a6078;
  --radius: 4px;

  display: grid;
  grid-template-rows: 60px minmax(0, 1fr);
  gap: 8px;
  min-height: calc(100dvh - 24px);
}

.card {
  background: linear-gradient(180deg, #122235 0%, #0f1c2b 100%);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
}

.head {
  padding: 8px 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

h2,
h3,
h4,
strong {
  color: var(--text-main);
}

p,
small,
span {
  color: #bdd1e7;
}

.muted {
  color: var(--text-muted);
  margin: 0;
}

.head p {
  margin: 2px 0 0;
}

.layout {
  min-height: 0;
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 10px;
}

.list {
  min-height: 0;
  display: grid;
  grid-template-rows: auto 1fr;
  overflow: hidden;
}

.list-head {
  padding: 10px;
  display: grid;
  gap: 8px;
}

.list-body {
  overflow: auto;
  padding: 0 8px 8px;
  display: grid;
  gap: 6px;
}

.detail {
  min-height: 0;
  overflow: auto;
  padding: 10px;
  display: grid;
  gap: 10px;
  align-content: start;
}

.pedido-item {
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  background: #112234;
  color: #d9e7f6;
  text-align: left;
  padding: 8px;
  display: grid;
  gap: 4px;
  cursor: pointer;
}

.pedido-item.active {
  border-color: #dce8f5;
  background: #17314a;
}

.item-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.panel {
  border: 1px solid var(--border-light);
  background: var(--bg-soft);
  border-radius: var(--radius);
  padding: 10px;
  display: grid;
  gap: 8px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.metrics-grid article {
  border: 1px solid #435a73;
  border-radius: var(--radius);
  background: #112235;
  padding: 10px;
  display: grid;
  gap: 4px;
}

.metrics-grid article span {
  color: #9cb7d2;
}

.workflow-panel {
  background:
    radial-gradient(circle at 0% 0%, rgba(121, 227, 195, 0.15), transparent 36%),
    #102235;
}

.workflow-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: flex-start;
}

.workflow-head-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.workflow-rail {
  --workflow-progress: 0%;
  position: relative;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  align-items: center;
  gap: 2px;
  padding: 8px 2px 10px;
  min-height: 62px;
}

.workflow-rail::before,
.workflow-rail::after {
  content: '';
  position: absolute;
  left: calc(10% + 18px);
  right: calc(10% + 18px);
  top: 24px;
  height: 2px;
  border-radius: 999px;
}

.workflow-rail::before {
  background: #3b526a;
}

.workflow-rail::after {
  right: auto;
  width: calc((80% - 36px) * (var(--workflow-progress) / 100));
  background: linear-gradient(90deg, #5bc5ab, #7ad7ef);
  transition: width 0.35s ease;
}

.workflow-node {
  position: relative;
  z-index: 1;
  color: #d5e3f2;
  padding: 0 2px;
  display: grid;
  justify-items: center;
  align-content: start;
  gap: 2px;
}

.workflow-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  border: 1px solid #7f97b1;
  background: #122235;
  color: #c5d8ec;
  font-size: 0.9rem;
  font-weight: 700;
  transition: all 0.25s ease;
}

.workflow-label {
  font-size: 0.68rem;
  line-height: 1;
  letter-spacing: 0.03em;
  color: #dbe8f4;
  white-space: nowrap;
}

.workflow-node.done .workflow-circle {
  background: #0f2f2b;
  border-color: #5bc5ab;
  color: #bdf8ea;
}

.workflow-node.active .workflow-circle {
  background: #15314a;
  border-color: #dce8f5;
  color: #f1f8ff;
  box-shadow: 0 0 0 4px rgba(122, 215, 239, 0.15);
}

.workflow-node.upcoming .workflow-circle {
  opacity: 0.85;
}

.tecnico-tabs {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.tab {
  border: 1px solid #4d667f;
  background: #102235;
  color: #d7e8f9;
  border-radius: var(--radius);
  padding: 8px 10px;
  cursor: pointer;
  font-weight: 600;
}

.tab.active {
  border-color: #dce8f5;
  background: #17314a;
}

.tab.locked,
.tab:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.summary-flow,
.detail-flow {
  display: grid;
  gap: 10px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.summary-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.summary-title {
  display: grid;
  gap: 4px;
}

.summary-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.chip,
.priority,
.state-chip {
  padding: 3px 8px;
  border-radius: var(--radius);
  border: 1px solid #8aa2bc;
  font-size: 0.74rem;
  color: #d7e8f9;
  background: #0f2234;
}

.priority[data-priority='critica'] {
  border-color: #ef4444;
  color: #fecaca;
}

.priority[data-priority='alta'] {
  border-color: #f59e0b;
  color: #fde68a;
}

.priority[data-priority='media'] {
  border-color: #22c55e;
  color: #bbf7d0;
}

.priority[data-priority='baja'] {
  border-color: #38bdf8;
  color: #bae6fd;
}

.summary-grid div {
  border: 1px solid #42566f;
  border-radius: var(--radius);
  background: #112235;
  padding: 8px;
  display: grid;
  gap: 4px;
}

.summary-grid span {
  color: #9fb9d3;
  font-size: 0.75rem;
}

.map-panel {
  gap: 10px;
}

.map-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.map-canvas {
  height: 260px;
  border: 1px solid #47627d;
  border-radius: var(--radius);
  overflow: hidden;
}

.playbook-panel {
  gap: 10px;
}

.playbook-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.guide-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.guide-card {
  border: 1px solid #42566f;
  border-radius: var(--radius);
  background: #0f2234;
  padding: 8px;
  display: grid;
  gap: 6px;
}

.guide-step {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  border: 1px solid #4e697f;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 0.72rem;
}

.guide-card p {
  margin: 0;
  font-size: 0.86rem;
  color: #cce0f4;
}

.create-box {
  border-top: 1px solid #41566f;
  padding-top: 8px;
}

.create-grid,
.service-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.wide {
  grid-column: 1 / -1;
}

label {
  display: grid;
  gap: 6px;
  color: #c0d3e8;
  font-size: 0.84rem;
}

input,
textarea,
select {
  background: #0c1a2a;
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  color: #e4eef8;
  padding: 8px;
  font: inherit;
}

.actions,
.head-actions,
.evidence-actions,
.step-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn,
.file-btn {
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  padding: 7px 10px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
}

.btn.primary,
.file-btn {
  background: linear-gradient(120deg, #16a34a, #059669);
  border-color: #79e3c3;
  color: #f4fff8;
}

.btn.ghost {
  background: #102235;
  color: #d8e7f7;
}

.btn.mini {
  background: #0f2234;
  color: #d8e7f7;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.file-btn input {
  display: none;
}

.execution-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: flex-start;
}

.execution-track {
  height: 9px;
  border-radius: 999px;
  background: #20344a;
  overflow: hidden;
}

.execution-track span {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #22c55e, #14b8a6);
}

.checklist {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 10px;
}

.checklist li {
  border: 1px solid #42566f;
  border-radius: var(--radius);
  background: #112335;
  padding: 10px;
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 10px;
}

.checklist li.done {
  border-color: #2f8f65;
}

.checklist li.locked {
  opacity: 0.65;
}

.checklist li.current {
  border-color: #dce8f5;
}

.step-index {
  width: 30px;
  height: 30px;
  border-radius: 999px;
  border: 1px solid #577392;
  display: grid;
  place-items: center;
  font-size: 0.8rem;
  font-weight: 700;
}

.step-content {
  display: grid;
  gap: 8px;
}

.step-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.done-pill,
.locked-pill,
.open-pill {
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 0.72rem;
  border: 1px solid #4d667f;
}

.done-pill {
  color: #baf6dc;
  border-color: #2f8f65;
}

.locked-pill {
  color: #f6d0d0;
  border-color: #a05a5a;
}

.open-pill {
  color: #bcd4eb;
}

.save-note-btn {
  margin-top: 6px;
}

.phase-status-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.phase-status-grid article {
  border: 1px solid #42566f;
  border-radius: var(--radius);
  background: #112335;
  padding: 10px;
  display: grid;
  gap: 4px;
}

.phase-status-grid article.complete {
  border-color: #2f8f65;
}

.feed {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 8px;
}

.feed li {
  border: 1px solid #42566f;
  border-radius: var(--radius);
  padding: 8px;
  display: grid;
  gap: 3px;
}

.camera-wrap {
  display: grid;
  gap: 8px;
}

.camera-wrap video {
  width: min(520px, 100%);
  border: 1px solid #42566f;
  border-radius: var(--radius);
  background: #0a1522;
}

.camera-error {
  color: #fecaca;
  margin: 0;
}

.hidden-canvas {
  display: none;
}

.evidence-grid,
.evidence-sent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
}

.evidence-item {
  border: 1px solid #42566f;
  border-radius: var(--radius);
  background: #102235;
  padding: 6px;
  display: grid;
  gap: 5px;
}

.evidence-item img {
  width: 100%;
  height: 112px;
  object-fit: cover;
  border-radius: 3px;
}

.evidence-item small {
  color: #abc3db;
}

.evidence-item.sent {
  border-color: #2f8f65;
}

.signature-box {
  border: 1px solid #42566f;
  border-radius: var(--radius);
  background: #102235;
  padding: 8px;
  display: grid;
  gap: 8px;
}

.signature-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.signature-canvas {
  width: 100%;
  min-height: 160px;
  border: 1px dashed #5b7490;
  border-radius: 4px;
  touch-action: none;
  background: #081320;
}

.signature-preview {
  width: min(460px, 100%);
  border: 1px solid #49627d;
  border-radius: 4px;
  background: #081320;
}

.reports-list {
  display: grid;
  gap: 8px;
}

.report-item {
  border: 1px solid #42566f;
  border-radius: var(--radius);
  background: #112335;
  padding: 8px;
  display: grid;
  gap: 6px;
}

.report-item header {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.report-item p {
  margin: 0;
}

.empty,
.empty-detail {
  color: #abc3db;
}

@media (max-width: 1250px) {
  .metrics-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .summary-grid,
  .phase-status-grid {
    grid-template-columns: 1fr;
  }

  .tecnico-tabs {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .guide-grid {
    grid-template-columns: 1fr;
  }

  .summary-meta {
    justify-content: flex-start;
  }

  .workflow-head-actions {
    justify-content: flex-start;
  }
}

@media (max-width: 980px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .list {
    max-height: 320px;
  }
}

@media (max-width: 760px) {
  .create-grid,
  .service-grid,
  .metrics-grid,
  .tecnico-tabs {
    grid-template-columns: 1fr;
  }

  .head-actions,
  .signature-head,
  .execution-head,
  .summary-head,
  .playbook-head,
  .workflow-head {
    flex-direction: column;
    align-items: stretch;
  }

  .checklist li {
    grid-template-columns: 1fr;
  }

  .workflow-rail {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    row-gap: 8px;
    min-height: auto;
    padding: 0;
  }

  .workflow-rail::before,
  .workflow-rail::after {
    display: none;
  }
}
</style>
