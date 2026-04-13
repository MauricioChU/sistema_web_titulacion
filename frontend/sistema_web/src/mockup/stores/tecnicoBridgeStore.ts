import { computed, reactive, ref } from 'vue';

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

const STORAGE_KEY = 'prointel_tecnico_bridge_v4';

const CHECKLIST_TEMPLATE: ChecklistStep[] = [
  { id: 'materiales-listos', label: 'Materiales listos antes de salir', done: false },
  { id: 'llegada-sitio', label: 'Llegue al sitio de trabajo', done: false },
  { id: 'inicio-trabajo', label: 'Inicie el trabajo tecnico', done: false },
  { id: 'nota-adicional', label: 'Registre informacion adicional', done: false },
];

const seedPedidos: SharedPedido[] = [
  {
    id: '1',
    code: 'OT-1084',
    accountCode: 'CUE-1001',
    client: 'Clinica Miraflores',
    contactName: 'Laura Medina',
    referenceAddress: 'Av. Arequipa 1001, frente a farmacia central',
    district: 'Miraflores',
    coordinates: '-12.1211, -77.0297',
    documentNumber: '20548796321',
    contactPhone: '987 123 111',
    contactEmail: 'laura.medina@clinicamf.pe',
    service: 'Mantenimiento electrico integral',
    status: 'Por confirmar',
    phase: 'asignacion',
    priority: 'alta',
    date: '2026-03-22',
    tech: 'Luis Rojas',
    diagnosis: 'Se detecta sobrecarga en tablero secundario y cableado deteriorado.',
    history: [{ when: '24 Mar 10:46', note: 'Asignacion confirmada a Luis Rojas.' }],
    costs: {
      total: 4280,
      direct: 3720,
      absorbed: 560,
      margin: 19,
      materials: 2200,
      mobility: 180,
      thirdParties: 640,
      tech: 1260,
      lines: [],
    },
  },
  {
    id: '4',
    code: 'OT-1090',
    accountCode: 'CUE-1002',
    client: 'Clinica Miraflores',
    contactName: 'Pedro Chavez',
    referenceAddress: 'Jr. Las Flores 221, torre 2',
    district: 'La Molina',
    coordinates: '-12.0749, -76.9512',
    documentNumber: '20548796321',
    contactPhone: '987 123 222',
    contactEmail: 'pedro.chavez@clinicamf.pe',
    urgent: true,
    service: 'Mantenimiento de UPS y tableros',
    status: 'Confirmado',
    phase: 'cierre',
    priority: 'critica',
    date: '2026-03-24',
    tech: 'Carlos Palacios',
    diagnosis: 'Bateria en degradacion acelerada, se recomienda reemplazo parcial.',
    history: [{ when: '24 Mar 11:42', note: 'Prueba de autonomia completada.' }],
    costs: {
      total: 6120,
      direct: 5280,
      absorbed: 840,
      margin: 21,
      materials: 3610,
      mobility: 140,
      thirdParties: 430,
      tech: 1100,
      lines: [],
    },
  },
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

function loadState(): BridgeState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return {
        coordinatorSnapshot: [...seedPedidos],
        tecnicoCreatedPedidos: [],
        updatesByPedido: {},
        evidenciasByPedido: {},
        checklistByPedido: {},
        serviceReportsByPedido: {},
      };
    }

    const parsed = JSON.parse(raw) as Partial<BridgeState>;
    return {
      coordinatorSnapshot: parsed.coordinatorSnapshot || [...seedPedidos],
      tecnicoCreatedPedidos: parsed.tecnicoCreatedPedidos || [],
      updatesByPedido: parsed.updatesByPedido || {},
      evidenciasByPedido: parsed.evidenciasByPedido || {},
      checklistByPedido: parsed.checklistByPedido || {},
      serviceReportsByPedido: parsed.serviceReportsByPedido || {},
    };
  } catch {
    return {
      coordinatorSnapshot: [...seedPedidos],
      tecnicoCreatedPedidos: [],
      updatesByPedido: {},
      evidenciasByPedido: {},
      checklistByPedido: {},
      serviceReportsByPedido: {},
    };
  }
}

const initialState = loadState();
const coordinatorSnapshot = ref<SharedPedido[]>(initialState.coordinatorSnapshot);
const tecnicoCreatedPedidos = ref<SharedPedido[]>(initialState.tecnicoCreatedPedidos);
const updatesByPedido = reactive<Record<string, TecnicoUpdate[]>>(initialState.updatesByPedido);
const evidenciasByPedido = reactive<Record<string, EvidenciaItem[]>>(initialState.evidenciasByPedido);
const checklistByPedido = reactive<Record<string, ChecklistStep[]>>(initialState.checklistByPedido);
const serviceReportsByPedido = reactive<Record<string, ServiceReport[]>>(initialState.serviceReportsByPedido);

function persistState() {
  const payload: BridgeState = {
    coordinatorSnapshot: coordinatorSnapshot.value,
    tecnicoCreatedPedidos: tecnicoCreatedPedidos.value,
    updatesByPedido,
    evidenciasByPedido,
    checklistByPedido,
    serviceReportsByPedido,
  };

  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

function getNextOtCode(basePedidos: SharedPedido[]) {
  const max = basePedidos.reduce((acc, pedido) => {
    const match = /OT-(\d+)/i.exec(pedido.code);
    if (!match) return acc;
    return Math.max(acc, Number(match[1]));
  }, 1090);

  return `OT-${max + 1}`;
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
    const checklist = ensureChecklist(payload.pedidoId);
    const step = checklist.find((item) => item.id === payload.stepId);
    if (!step) return;

    if (payload.done && !canMarkChecklistStep(payload.pedidoId, payload.stepId)) return;

    step.done = payload.done;
    step.doneAt = payload.done ? nowStamp() : undefined;
    step.note = payload.note ?? step.note;
    persistState();
  }

  function setCoordinatorSnapshot(pedidos: SharedPedido[]) {
    coordinatorSnapshot.value = pedidos;
    persistState();
  }

  function mergeWithCoordinatorPedidos(coordinatorPedidos: SharedPedido[]) {
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
    persistState();
    return pedido;
  }

  function addTecnicoUpdate(payload: {
    pedidoId: string;
    tecnico: string;
    note: string;
    status?: string;
  }) {
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

    persistState();
  }

  function addEvidencias(payload: {
    pedidoId: string;
    tecnico: string;
    stage: EvidenciaStage;
    items: Array<{ name: string; url: string; source: 'archivo' | 'camara'; description?: string }>;
  }) {
    const createdAt = nowStamp();
    const items = payload.items.map((item) => ({
      id: `ev-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      pedidoId: payload.pedidoId,
      tecnico: payload.tecnico,
      name: item.name,
      url: item.url,
      description: item.description,
      source: item.source,
      stage: payload.stage,
      createdAt,
    }));

    evidenciasByPedido[payload.pedidoId] = [...items, ...(evidenciasByPedido[payload.pedidoId] || [])];

    const all = [...coordinatorSnapshot.value, ...tecnicoCreatedPedidos.value];
    const pedido = all.find((entry) => entry.id === payload.pedidoId);
    if (pedido) {
      pedido.history.unshift({
        when: createdAt,
        note: `[Tecnico ${payload.tecnico}] Evidencias ${payload.stage} cargadas (${items.length}).`,
      });
    }

    persistState();
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
    const report: ServiceReport = {
      id: `srv-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      pedidoId: payload.pedidoId,
      tecnico: payload.tecnico,
      cliente: payload.cliente,
      responsableLocal: payload.responsableLocal,
      pedidoSolicitado: payload.pedidoSolicitado,
      observaciones: payload.observaciones,
      recomendaciones: payload.recomendaciones,
      firmaCliente: payload.firmaCliente,
      createdAt: nowStamp(),
    };

    serviceReportsByPedido[payload.pedidoId] = [report, ...(serviceReportsByPedido[payload.pedidoId] || [])];

    addTecnicoUpdate({
      pedidoId: payload.pedidoId,
      tecnico: payload.tecnico,
      status: 'Facturacion',
      note: 'Formato de servicio tecnico enviado con firma del cliente. Pedido listo para facturacion.',
    });

    persistState();
    return report;
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
    getServiceReports,
    getReportsForTecnico,
  };
}
