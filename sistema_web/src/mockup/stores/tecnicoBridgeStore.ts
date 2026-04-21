import { computed, reactive, ref } from 'vue';
import { fetchMe } from '../../services/authService';
import { getApiOrigin } from '../../services/http';
import {
  type ApiChecklistStep,
  type ApiEvidencia,
  type ApiInformeTecnico,
  type ApiPedido,
  confirmarTecnico,
  fetchPedidoById,
  listMisAsignados,
  listPedidos,
  submitInformeTecnico,
  updateDiagnostico as patchDiagnostico,
  uploadEvidencia,
  upsertChecklist,
} from '../../services/pedidosService';

export type PhaseKey = 'deteccion' | 'asignacion' | 'cierre' | 'facturacion';
export type EvidenciaStage = 'antes' | 'despues';
export type ChecklistStepId =
  | 'materiales-listos'
  | 'llegada-sitio'
  | 'inicio-trabajo'
  | 'nota-adicional';

export interface SharedCostLine {
  type: string;
  name: string;
  qty: number;
  unit: number;
  amount: number;
  pending?: boolean;
}

export interface SharedPedido {
  id: string;
  code: string;
  accountCode?: string;
  client: string;
  contactName?: string;
  referenceAddress?: string;
  district?: string;
  coordinates?: string;
  documentNumber?: string;
  contactPhone?: string;
  contactEmail?: string;
  urgent?: boolean;
  service: string;
  status: string;
  phase: PhaseKey;
  priority: 'baja' | 'media' | 'alta' | 'critica';
  date: string;
  tech?: string;
  diagnosis: string;
  history: Array<{ when: string; note: string }>;
  costs: {
    total: number;
    direct: number;
    absorbed: number;
    margin: number;
    materials: number;
    mobility: number;
    thirdParties: number;
    tech: number;
    lines: SharedCostLine[];
  };
}

export interface TecnicoUpdate {
  id: string;
  pedidoId: string;
  tecnico: string;
  note: string;
  status?: string;
  createdAt: string;
}

export interface EvidenciaItem {
  id: string;
  pedidoId: string;
  tecnico: string;
  name: string;
  url: string;
  description?: string;
  source: 'archivo' | 'camara';
  stage: EvidenciaStage;
  createdAt: string;
}

export interface ChecklistStep {
  id: ChecklistStepId;
  label: string;
  done: boolean;
  doneAt?: string;
  note?: string;
}

export interface ServiceReport {
  id: string;
  pedidoId: string;
  tecnico: string;
  cliente: string;
  responsableLocal: string;
  pedidoSolicitado: string;
  observaciones: string;
  recomendaciones: string;
  firmaCliente: string;
  createdAt: string;
}

interface BridgeState {
  coordinatorSnapshot: SharedPedido[];
  tecnicoCreatedPedidos: SharedPedido[];
  updatesByPedido: Record<string, TecnicoUpdate[]>;
  evidenciasByPedido: Record<string, EvidenciaItem[]>;
  checklistByPedido: Record<string, ChecklistStep[]>;
  serviceReportsByPedido: Record<string, ServiceReport[]>;
}

const CHECKLIST_TEMPLATE: ChecklistStep[] = [
  { id: 'materiales-listos', label: 'Materiales listos antes de salir', done: false },
  { id: 'llegada-sitio', label: 'Llegue al sitio de trabajo', done: false },
  { id: 'inicio-trabajo', label: 'Inicie el trabajo tecnico', done: false },
  { id: 'nota-adicional', label: 'Registre informacion adicional', done: false },
];

function nowStamp() {
  return new Date().toLocaleString('es-PE', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function cloneChecklistTemplate() {
  return CHECKLIST_TEMPLATE.map((step) => ({ ...step }));
}

const CHECKLIST_LABELS: Record<ChecklistStepId, string> = {
  'materiales-listos': 'Materiales listos antes de salir',
  'llegada-sitio': 'Llegue al sitio de trabajo',
  'inicio-trabajo': 'Inicie el trabajo tecnico',
  'nota-adicional': 'Registre informacion adicional',
};

function normalizeChecklist(source?: ChecklistStep[]) {
  const base = cloneChecklistTemplate();
  if (!source?.length) return base;

  return base.map((step) => {
    const previous = source.find((item) => item.id === step.id);
    if (!previous) return step;
    return {
      ...step,
      done: previous.done,
      doneAt: previous.doneAt,
      note: previous.note,
    };
  });
}

function formatIsoAsStamp(iso?: string | null) {
  if (!iso) return nowStamp();
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return nowStamp();
  return date.toLocaleString('es-PE', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function statusLabel(status: ApiPedido['status_operativo']) {
  const labels: Record<ApiPedido['status_operativo'], string> = {
    'por-confirmar': 'Por confirmar',
    confirmado: 'Confirmado',
    'en-labor': 'En labor',
    'cierre-tecnico': 'Cierre tecnico',
    facturacion: 'Facturacion',
    completado: 'Completado',
    'dado-de-baja': 'Dado de baja',
  };
  return labels[status] || 'Pendiente';
}

function toPhaseFromApi(pedido: ApiPedido): PhaseKey {
  const status = pedido.status_operativo;

  if (status === 'dado-de-baja') return 'cierre';
  if (status === 'facturacion' || status === 'completado') return 'facturacion';
  if (status === 'en-labor' || status === 'cierre-tecnico') return 'cierre';
  if (status === 'por-confirmar' || status === 'confirmado') return 'asignacion';

  if (pedido.fase === 'creacion') return 'deteccion';
  if (pedido.fase === 'programacion') return 'asignacion';
  if (pedido.fase === 'seguimiento') return 'cierre';
  return 'facturacion';
}

function toAbsoluteMediaUrl(pathOrUrl: string) {
  if (!pathOrUrl) return '';
  if (/^https?:\/\//i.test(pathOrUrl)) return pathOrUrl;
  const normalizedPath = pathOrUrl.startsWith('/') ? pathOrUrl : `/${pathOrUrl}`;
  return `${getApiOrigin()}${normalizedPath}`;
}

function mapApiUpdates(pedido: ApiPedido): TecnicoUpdate[] {
  return (pedido.tecnico_updates || []).map((entry) => ({
    id: String(entry.id),
    pedidoId: String(pedido.id),
    tecnico: entry.tecnico_nombre || pedido.tecnico_nombre || 'Tecnico',
    note: entry.nota,
    status: entry.nuevo_estado ? statusLabel(entry.nuevo_estado as ApiPedido['status_operativo']) : undefined,
    createdAt: formatIsoAsStamp(entry.created_at),
  }));
}

function mapApiChecklist(pedido: ApiPedido): ChecklistStep[] {
  const byId = new Map<ChecklistStepId, ApiChecklistStep>();

  (pedido.checklist_steps || []).forEach((item) => {
    const stepId = item.step_id as ChecklistStepId;
    if (CHECKLIST_LABELS[stepId]) {
      byId.set(stepId, item);
    }
  });

  return CHECKLIST_TEMPLATE.map((step) => {
    const source = byId.get(step.id);
    return {
      id: step.id,
      label: step.label,
      done: Boolean(source?.completado),
      doneAt: source?.completado_en ? formatIsoAsStamp(source.completado_en) : undefined,
      note: source?.nota || undefined,
    };
  });
}

function mapApiEvidencias(pedido: ApiPedido): EvidenciaItem[] {
  return (pedido.evidencias || []).map((item: ApiEvidencia) => ({
    id: String(item.id),
    pedidoId: String(pedido.id),
    tecnico: item.tecnico_nombre || pedido.tecnico_nombre || 'Tecnico',
    name: item.nombre,
    url: toAbsoluteMediaUrl(item.archivo),
    description: item.descripcion,
    source: item.source,
    stage: item.stage,
    createdAt: formatIsoAsStamp(item.created_at),
  }));
}

function mapApiReport(pedido: ApiPedido, informe: ApiInformeTecnico | null): ServiceReport[] {
  if (!informe) return [];

  return [{
    id: String(informe.id),
    pedidoId: String(pedido.id),
    tecnico: informe.tecnico_nombre || pedido.tecnico_nombre || 'Tecnico',
    cliente: pedido.cliente_nombre || 'Cliente',
    responsableLocal: informe.responsable_local,
    pedidoSolicitado: informe.pedido_solicitado,
    observaciones: informe.observaciones,
    recomendaciones: informe.recomendaciones,
    firmaCliente: toAbsoluteMediaUrl(informe.firma_cliente),
    createdAt: formatIsoAsStamp(informe.created_at),
  }];
}

function mapApiHistory(pedido: ApiPedido) {
  const history = Array.isArray(pedido.historial) ? [...pedido.historial] : [];
  history.reverse();
  return history.map((entry) => ({
    when: formatIsoAsStamp(entry.timestamp),
    note: entry.detalle || entry.evento,
  }));
}

function mapApiPedido(pedido: ApiPedido, previous?: SharedPedido): SharedPedido {
  const fallbackCosts = previous?.costs || {
    total: 0,
    direct: 0,
    absorbed: 0,
    margin: 0,
    materials: 0,
    mobility: 0,
    thirdParties: 0,
    tech: 0,
    lines: [],
  };

  return {
    id: String(pedido.id),
    code: pedido.codigo || previous?.code || `A${String(pedido.id).slice(-4).padStart(4, '0')}`,
    accountCode: pedido.cuenta_numero || previous?.accountCode,
    client: pedido.cliente_nombre || previous?.client || 'Cliente sin nombre',
    contactName: previous?.contactName,
    referenceAddress: pedido.cuenta_direccion || previous?.referenceAddress,
    district: pedido.cuenta_distrito || previous?.district,
    coordinates: (
      pedido.cuenta_latitud != null && pedido.cuenta_longitud != null
        ? `${pedido.cuenta_latitud}, ${pedido.cuenta_longitud}`
        : previous?.coordinates
    ),
    documentNumber: previous?.documentNumber,
    contactPhone: previous?.contactPhone,
    contactEmail: previous?.contactEmail,
    urgent: pedido.prioridad === 'critica',
    service: pedido.titulo || pedido.tipo_servicio,
    status: statusLabel(pedido.status_operativo),
    phase: toPhaseFromApi(pedido),
    priority: pedido.prioridad,
    date: (pedido.fecha_programada || pedido.created_at || '').slice(0, 10),
    tech: pedido.tecnico_nombre || previous?.tech,
    diagnosis: pedido.diagnostico_tecnico || pedido.descripcion || previous?.diagnosis || '',
    history: mapApiHistory(pedido),
    costs: fallbackCosts,
  };
}

function clearRecord<T>(record: Record<string, T>) {
  Object.keys(record).forEach((key) => {
    delete record[key];
  });
}

function dataUrlToFile(dataUrl: string, fileName: string) {
  const chunks = dataUrl.split(',');
  if (chunks.length < 2) {
    throw new Error('Formato de imagen invalido para enviar evidencia.');
  }

  const header = chunks[0];
  const body = chunks[1];
  const mimeMatch = /data:(.*?);base64/.exec(header);
  const mime = mimeMatch?.[1] || 'image/jpeg';
  const binary = atob(body);
  const bytes = new Uint8Array(binary.length);

  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }

  return new File([bytes], fileName, { type: mime });
}

function toStateFromApi(pedidos: ApiPedido[]): BridgeState {
  const snapshot: SharedPedido[] = [];
  const nextUpdates: Record<string, TecnicoUpdate[]> = {};
  const nextEvidencias: Record<string, EvidenciaItem[]> = {};
  const nextChecklist: Record<string, ChecklistStep[]> = {};
  const nextReports: Record<string, ServiceReport[]> = {};

  pedidos.forEach((pedidoApi) => {
    const pedidoId = String(pedidoApi.id);
    const previous = coordinatorSnapshot.value.find((item) => item.id === pedidoId);
    const mappedPedido = mapApiPedido(pedidoApi, previous);
    snapshot.push(mappedPedido);
    nextUpdates[pedidoId] = mapApiUpdates(pedidoApi);
    nextEvidencias[pedidoId] = mapApiEvidencias(pedidoApi);
    nextChecklist[pedidoId] = mapApiChecklist(pedidoApi);
    nextReports[pedidoId] = mapApiReport(pedidoApi, pedidoApi.informe_tecnico);
  });

  return {
    coordinatorSnapshot: snapshot,
    tecnicoCreatedPedidos: tecnicoCreatedPedidos.value,
    updatesByPedido: nextUpdates,
    evidenciasByPedido: nextEvidencias,
    checklistByPedido: nextChecklist,
    serviceReportsByPedido: nextReports,
  };
}

const coordinatorSnapshot = ref<SharedPedido[]>([]);
const tecnicoCreatedPedidos = ref<SharedPedido[]>([]);
const updatesByPedido = reactive<Record<string, TecnicoUpdate[]>>({});
const evidenciasByPedido = reactive<Record<string, EvidenciaItem[]>>({});
const checklistByPedido = reactive<Record<string, ChecklistStep[]>>({});
const serviceReportsByPedido = reactive<Record<string, ServiceReport[]>>({});

const isBackendReady = ref(false);
const backendError = ref('');
const currentRole = ref<'admin' | 'coordinador' | 'tecnico' | 'usuario'>('usuario');
const currentTecnicoNombre = ref('');

let syncPromise: Promise<void> | null = null;

function applyState(next: BridgeState) {
  coordinatorSnapshot.value = next.coordinatorSnapshot;
  tecnicoCreatedPedidos.value = next.tecnicoCreatedPedidos;

  clearRecord(updatesByPedido);
  Object.assign(updatesByPedido, next.updatesByPedido);

  clearRecord(evidenciasByPedido);
  Object.assign(evidenciasByPedido, next.evidenciasByPedido);

  clearRecord(checklistByPedido);
  Object.assign(checklistByPedido, next.checklistByPedido);

  clearRecord(serviceReportsByPedido);
  Object.assign(serviceReportsByPedido, next.serviceReportsByPedido);
}

async function refreshPedidosFromApi(force = false) {
  if (syncPromise && !force) return syncPromise;

  syncPromise = (async () => {
    const me = await fetchMe();
    currentRole.value = me.role;
    currentTecnicoNombre.value = me.tecnicoNombre || me.username;

    const pedidos = me.role === 'tecnico' ? await listMisAsignados() : await listPedidos();
    applyState(toStateFromApi(pedidos));

    isBackendReady.value = true;
    backendError.value = '';
  })();

  try {
    await syncPromise;
  } catch (error) {
    backendError.value = error instanceof Error ? error.message : 'No se pudo sincronizar pedidos.';
    throw error;
  } finally {
    syncPromise = null;
  }
}

function getNextOtCode(basePedidos: SharedPedido[]) {
  const max = basePedidos.reduce((acc, pedido) => {
    const match = /^A(\d+)$/i.exec(pedido.code);
    if (!match) return acc;
    return Math.max(acc, Number(match[1]));
  }, 0);

  return `A${String(max + 1).padStart(4, '0')}`;
}

export function useTecnicoBridgeStore() {
  const allPedidosForTecnico = computed(() => {
    const byId = new Map<string, SharedPedido>();

    coordinatorSnapshot.value.forEach((pedido) => {
      byId.set(pedido.id, pedido);
    });

    tecnicoCreatedPedidos.value.forEach((pedido) => {
      byId.set(pedido.id, pedido);
    });

    return Array.from(byId.values()).sort((a, b) => String(b.date).localeCompare(String(a.date)));
  });

  async function hydrateFromApi(force = false) {
    await refreshPedidosFromApi(force);
  }

  async function refreshPedidoById(pedidoId: string) {
    const apiPedido = await fetchPedidoById(pedidoId);
    const previous = coordinatorSnapshot.value.find((item) => item.id === pedidoId);
    const mapped = mapApiPedido(apiPedido, previous);
    const idx = coordinatorSnapshot.value.findIndex((item) => item.id === pedidoId);

    if (idx >= 0) {
      coordinatorSnapshot.value[idx] = mapped;
    } else {
      coordinatorSnapshot.value.unshift(mapped);
    }

    updatesByPedido[pedidoId] = mapApiUpdates(apiPedido);
    evidenciasByPedido[pedidoId] = mapApiEvidencias(apiPedido);
    checklistByPedido[pedidoId] = mapApiChecklist(apiPedido);
    serviceReportsByPedido[pedidoId] = mapApiReport(apiPedido, apiPedido.informe_tecnico);
  }

  function ensureChecklist(pedidoId: string) {
    const current = checklistByPedido[pedidoId];
    if (!current) {
      checklistByPedido[pedidoId] = normalizeChecklist();
      return checklistByPedido[pedidoId];
    }

    const templateIds = CHECKLIST_TEMPLATE.map((step) => step.id);
    const currentIds = current.map((step) => step.id);
    const needsNormalization =
      current.length !== CHECKLIST_TEMPLATE.length
      || templateIds.some((id, index) => id !== currentIds[index]);

    if (needsNormalization) {
      checklistByPedido[pedidoId] = normalizeChecklist(current);
    }

    return checklistByPedido[pedidoId];
  }

  function getChecklist(pedidoId: string) {
    return ensureChecklist(pedidoId);
  }

  function canMarkChecklistStep(pedidoId: string, stepId: ChecklistStepId) {
    const checklist = ensureChecklist(pedidoId);
    const index = checklist.findIndex((step) => step.id === stepId);
    if (index <= 0) return true;
    return checklist[index - 1].done;
  }

  function markChecklistStep(payload: {
    pedidoId: string;
    stepId: ChecklistStepId;
    done: boolean;
    note?: string;
  }) {
    if (payload.done && !canMarkChecklistStep(payload.pedidoId, payload.stepId)) return Promise.resolve();

    return upsertChecklist(payload.pedidoId, {
      stepId: payload.stepId,
      completado: payload.done,
      nota: payload.note,
    }).then(() => refreshPedidoById(payload.pedidoId));
  }

  function setCoordinatorSnapshot(pedidos: SharedPedido[]) {
    if (isBackendReady.value) return;
    coordinatorSnapshot.value = pedidos;
  }

  function mergeWithCoordinatorPedidos(coordinatorPedidos: SharedPedido[]) {
    if (isBackendReady.value) {
      const byId = new Map<string, SharedPedido>();
      coordinatorSnapshot.value.forEach((pedido) => byId.set(pedido.id, pedido));
      tecnicoCreatedPedidos.value.forEach((pedido) => byId.set(pedido.id, pedido));
      return Array.from(byId.values()).sort((a, b) => String(b.date).localeCompare(String(a.date)));
    }

    const coordinatorIds = new Set(coordinatorPedidos.map((pedido) => pedido.id));
    const externos = tecnicoCreatedPedidos.value.filter((pedido) => !coordinatorIds.has(pedido.id));
    return [...externos, ...coordinatorPedidos];
  }

  function createPedidoFromTecnico(input: {
    tecnico: string;
    client: string;
    service: string;
    diagnosis: string;
    accountCode?: string;
    contactName?: string;
  }) {
    const pool = [...coordinatorSnapshot.value, ...tecnicoCreatedPedidos.value];
    const code = getNextOtCode(pool);

    const pedido: SharedPedido = {
      id: `tec-${Date.now()}`,
      code,
      accountCode: input.accountCode,
      client: input.client,
      contactName: input.contactName || input.tecnico,
      referenceAddress: '-',
      district: '-',
      coordinates: '-',
      documentNumber: '-',
      contactPhone: '-',
      contactEmail: '-',
      service: input.service,
      status: 'Por confirmar',
      phase: 'deteccion',
      priority: 'media',
      date: new Date().toISOString().slice(0, 10),
      tech: input.tecnico,
      diagnosis: input.diagnosis || 'Sin diagnostico',
      history: [
        {
          when: nowStamp(),
          note: `Pedido creado por tecnico ${input.tecnico}.`,
        },
      ],
      costs: {
        total: 0,
        direct: 0,
        absorbed: 0,
        margin: 0,
        materials: 0,
        mobility: 0,
        thirdParties: 0,
        tech: 0,
        lines: [],
      },
    };

    tecnicoCreatedPedidos.value.unshift(pedido);
    ensureChecklist(pedido.id);
    return pedido;
  }

  function addTecnicoUpdate(payload: {
    pedidoId: string;
    tecnico: string;
    note: string;
    status?: string;
  }) {
    const statusLower = (payload.status || '').toLowerCase();
    if (statusLower.includes('confirmado')) {
      return confirmarTecnico(payload.pedidoId).then(() => refreshPedidoById(payload.pedidoId));
    }

    const update: TecnicoUpdate = {
      id: `upd-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      pedidoId: payload.pedidoId,
      tecnico: payload.tecnico,
      note: payload.note,
      status: payload.status,
      createdAt: nowStamp(),
    };

    updatesByPedido[payload.pedidoId] = [update, ...(updatesByPedido[payload.pedidoId] || [])];

    const all = [...coordinatorSnapshot.value, ...tecnicoCreatedPedidos.value];
    const pedido = all.find((item) => item.id === payload.pedidoId);
    if (pedido) {
      if (payload.status) pedido.status = payload.status;
      pedido.history.unshift({
        when: update.createdAt,
        note: `[Tecnico ${payload.tecnico}] ${payload.note}${payload.status ? ` (Estado: ${payload.status})` : ''}`,
      });
    }

    return Promise.resolve();
  }

  function addEvidencias(payload: {
    pedidoId: string;
    tecnico: string;
    stage: EvidenciaStage;
    items: Array<{ name: string; url: string; source: 'archivo' | 'camara'; description?: string }>;
  }) {
    const uploads = payload.items.map((item) => {
      const file = dataUrlToFile(item.url, item.name || `evidencia-${Date.now()}.jpg`);
      return uploadEvidencia(payload.pedidoId, {
        file,
        descripcion: item.description || item.name || 'Evidencia tecnica',
        stage: payload.stage,
        source: item.source,
        nombre: item.name,
      });
    });

    return Promise.all(uploads).then(() => refreshPedidoById(payload.pedidoId));
  }

  function hasEvidenciasStage(pedidoId: string, stage: EvidenciaStage) {
    return (evidenciasByPedido[pedidoId] || []).some((item) => item.stage === stage);
  }

  function hasCompleteEvidenceSet(pedidoId: string) {
    return hasEvidenciasStage(pedidoId, 'antes') && hasEvidenciasStage(pedidoId, 'despues');
  }

  function submitServiceReport(payload: {
    pedidoId: string;
    tecnico: string;
    cliente: string;
    responsableLocal: string;
    pedidoSolicitado: string;
    observaciones: string;
    recomendaciones: string;
    firmaCliente: string;
  }) {
    const firmaFile = dataUrlToFile(payload.firmaCliente, `firma-${Date.now()}.png`);

    return submitInformeTecnico(payload.pedidoId, {
      diagnosticoFinal: payload.observaciones,
      responsableLocal: payload.responsableLocal,
      pedidoSolicitado: payload.pedidoSolicitado,
      observaciones: payload.observaciones,
      recomendaciones: payload.recomendaciones,
      firmaCliente: firmaFile,
    }).then(async (response) => {
      const pedido = response.pedido;
      const mapped = mapApiPedido(pedido, coordinatorSnapshot.value.find((item) => item.id === String(pedido.id)));
      const pedidoId = String(pedido.id);
      const idx = coordinatorSnapshot.value.findIndex((item) => item.id === pedidoId);
      if (idx >= 0) coordinatorSnapshot.value[idx] = mapped;
      else coordinatorSnapshot.value.unshift(mapped);

      updatesByPedido[pedidoId] = mapApiUpdates(pedido);
      evidenciasByPedido[pedidoId] = mapApiEvidencias(pedido);
      checklistByPedido[pedidoId] = mapApiChecklist(pedido);
      serviceReportsByPedido[pedidoId] = mapApiReport(pedido, response.informe);

      return serviceReportsByPedido[pedidoId][0];
    });
  }

  function updateDiagnostico(pedidoId: string, diagnostico: string) {
    return patchDiagnostico(pedidoId, diagnostico).then(() => refreshPedidoById(pedidoId));
  }

  function getUpdates(pedidoId: string) {
    return updatesByPedido[pedidoId] || [];
  }

  function getEvidencias(pedidoId: string) {
    return evidenciasByPedido[pedidoId] || [];
  }

  function getServiceReports(pedidoId: string) {
    return serviceReportsByPedido[pedidoId] || [];
  }

  function getReportsForTecnico(tecnico: string) {
    const normalized = tecnico.trim().toLowerCase();
    return Object.values(serviceReportsByPedido)
      .flat()
      .filter((report) => report.tecnico.toLowerCase() === normalized)
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  }

  return {
    coordinatorSnapshot,
    tecnicoCreatedPedidos,
    allPedidosForTecnico,
    isBackendReady,
    backendError,
    currentRole,
    currentTecnicoNombre,
    hydrateFromApi,
    setCoordinatorSnapshot,
    mergeWithCoordinatorPedidos,
    createPedidoFromTecnico,
    addTecnicoUpdate,
    addEvidencias,
    getUpdates,
    getEvidencias,
    getChecklist,
    canMarkChecklistStep,
    markChecklistStep,
    hasEvidenciasStage,
    hasCompleteEvidenceSet,
    submitServiceReport,
    updateDiagnostico,
    getServiceReports,
    getReportsForTecnico,
  };
}
