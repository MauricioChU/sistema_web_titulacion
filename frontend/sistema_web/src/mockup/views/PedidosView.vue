<template>
  <section class="pedidos-view">
    <header class="head card">
      <div>
        <h2>Pedidos</h2>
        <p>Seguimiento por fases y control de costos operativo</p>
      </div>
      <div class="head-actions">
        <button class="btn ghost" @click="creating = false">Ver panel</button>
        <button class="btn primary" @click="openCreate">Crear pedido</button>
      </div>
    </header>

    <div class="layout">
      <aside class="list card">
        <div class="list-head">
          <div class="list-head-top">
            <h3>Cola activa</h3>
            <small>{{ filteredPedidos.length }} pedidos</small>
          </div>
          <input
            v-model="searchQuery"
            class="list-search"
            type="search"
            placeholder="Buscar por OT, cliente o servicio"
          />
        </div>

        <div class="phase-filter">
          <label class="phase-combobox" for="phaseFilter">
            <span>Filtrar por fase</span>
            <select id="phaseFilter" v-model="phaseFilter">
              <option v-for="phase in phaseFilters" :key="phase.key" :value="phase.key">
                {{ phase.label }} ({{ countByPhase(phase.key) }})
              </option>
            </select>
          </label>
        </div>

        <div class="list-body">
          <div v-if="filteredPedidos.length === 0" class="list-empty">
            No hay pedidos para el filtro actual.
          </div>
          <button
            v-for="pedido in filteredPedidos"
            :key="pedido.id"
            class="pedido-item"
            :class="{ active: selectedId === pedido.id }"
            @click="selectPedido(pedido.id)"
          >
            <div class="pedido-top">
              <strong>{{ pedido.code }}</strong>
              <span class="priority" :data-priority="pedido.priority">{{ pedido.priority }}</span>
            </div>
            <p>{{ pedido.client }}</p>
            <small>{{ pedido.service }}</small>
            <div class="pedido-meta">
              <span class="chip">{{ phaseLabel[pedido.phase] }}</span>
              <span>{{ pedido.date }}</span>
            </div>
          </button>
        </div>
      </aside>

      <article class="detail card">
        <template v-if="creating">
          <div class="create-head">
            <h3>Nuevo pedido</h3>
            <p>Paso {{ createStep }} de 2 - {{ createStep === 1 ? 'Datos de cuenta' : 'Identificar pedido' }}</p>
          </div>

          <form class="create-form" @submit.prevent="createPedido">
            <template v-if="createStep === 1">
              <label>
                Codigo de cuenta
                <input
                  v-model="form.accountCode"
                  list="account-codes"
                  required
                  placeholder="Ej: CUE-1002"
                  @change="applyAccountByCode"
                  @blur="applyAccountByCode"
                />
              </label>
              <datalist id="account-codes">
                <option v-for="acc in accountCatalog" :key="acc.code" :value="acc.code">
                  {{ acc.clientName }} - {{ acc.accountName }}
                </option>
              </datalist>
              <label>
                Nombre del cliente
                <input v-model="form.clientName" required placeholder="Nombre del cliente" />
              </label>
              <label>
                Contacto
                <input v-model="form.contactName" required placeholder="Nombre del contacto" />
              </label>
              <label>
                Direccion referencia
                <input v-model="form.referenceAddress" required placeholder="Direccion de referencia" />
              </label>
              <label>
                Distrito
                <input v-model="form.district" required placeholder="Distrito" />
              </label>
              <label>
                Coordenadas
                <input v-model="form.coordinates" required placeholder="-12.0464, -77.0428" />
              </label>
              <label>
                DNI/RUC/CE
                <input v-model="form.documentNumber" required placeholder="Documento del cliente" />
              </label>
              <label>
                Telefono del contacto
                <input v-model="form.contactPhone" required placeholder="999 999 999" />
              </label>
              <label>
                Correo del contacto
                <input v-model="form.contactEmail" type="email" required placeholder="contacto@cliente.com" />
              </label>
            </template>

            <template v-else>
              <label class="wide">
                Servicio
                <select v-model="form.service" required>
                  <option disabled value="">Selecciona un servicio</option>
                  <option v-for="service in commonServices" :key="service" :value="service">{{ service }}</option>
                </select>
              </label>
              <label class="wide">
                Descripcion del problema
                <textarea
                  v-model="form.problemDescription"
                  rows="5"
                  placeholder="Info adicional del problema reportado"
                ></textarea>
              </label>
              <label class="urgent-check wide">
                <input v-model="form.urgent" type="checkbox" />
                <span>Marcar como urgente</span>
              </label>
            </template>

            <p v-if="linkedAccounts.length" class="wide account-helper">
              Este cliente tiene otras cuentas: {{ linkedAccounts.join(', ') }}.
            </p>

            <div class="form-actions wide">
              <button type="button" class="btn ghost" @click="creating = false">Cancelar</button>
              <button v-if="createStep === 2" type="button" class="btn ghost" @click="createStep = 1">Atras</button>
              <button v-if="createStep === 1" type="button" class="btn primary" @click="goToStepTwo">Siguiente</button>
              <button v-else type="submit" class="btn primary">Guardar pedido</button>
            </div>
          </form>
        </template>

        <template v-else-if="selectedPedido">
          <div class="detail-head">
            <div>
              <h3>{{ selectedPedido.code }} - {{ selectedPedido.client }}</h3>
              <p>{{ selectedPedido.service }}</p>
            </div>
            <div class="detail-kpis">
              <article>
                <span>Costo estimado</span>
                <strong>S/ {{ selectedPedido.costs.total.toLocaleString('es-PE') }}</strong>
              </article>
              <article>
                <span>Margen</span>
                <strong>{{ selectedPedido.costs.margin }}%</strong>
              </article>
              <article>
                <span>Estado</span>
                <strong>{{ selectedPedido.status }}</strong>
              </article>
              <button
                class="btn primary phase-next"
                :disabled="currentPhaseIndex >= phaseOrder.length - 1"
                @click="goToNextPhase"
              >
                Siguiente fase
              </button>
            </div>
          </div>

          <div class="phase-rail" :style="{ '--phase-progress': `${phaseProgress}%` }">
            <button
              v-for="(phase, index) in workflowPhases"
              :key="phase.key"
              class="phase-node"
              :class="{
                done: index < currentPhaseIndex,
                active: index === currentPhaseIndex,
                upcoming: index > currentPhaseIndex,
              }"
              @click="updatePhase(phase.key)"
            >
              <span class="phase-circle">{{ index + 1 }}</span>
              <strong class="phase-label">{{ phase.label }}</strong>
            </button>
          </div>

          <section class="tabs-area">
            <nav class="tabs" aria-label="Detalle de pedido">
              <button
                v-for="tab in tabs"
                :key="tab.key"
                class="tab"
                :class="{ active: activeTab === tab.key }"
                @click="activeTab = tab.key"
              >
                {{ tab.label }}
              </button>
            </nav>

            <div class="tab-content">
            <section v-if="activeTab === 'detalles'" class="grid-two">
              <article class="panel">
                <h4>Datos de cuenta y contacto</h4>
                <ul>
                  <li><span>Codigo de cuenta</span><strong>{{ selectedPedido.accountCode || 'Sin codigo' }}</strong></li>
                  <li><span>Cliente</span><strong>{{ selectedPedido.client || 'Sin cliente' }}</strong></li>
                  <li><span>Contacto</span><strong>{{ selectedPedido.contactName || 'Sin contacto' }}</strong></li>
                  <li><span>Direccion referencia</span><strong>{{ selectedPedido.referenceAddress || 'Sin direccion' }}</strong></li>
                  <li><span>Distrito</span><strong>{{ selectedPedido.district || 'Sin distrito' }}</strong></li>
                  <li><span>Coordenadas</span><strong>{{ selectedPedido.coordinates || 'Sin coordenadas' }}</strong></li>
                  <li><span>DNI/RUC/CE</span><strong>{{ selectedPedido.documentNumber || 'Sin documento' }}</strong></li>
                  <li><span>Telefono contacto</span><strong>{{ selectedPedido.contactPhone || 'Sin telefono' }}</strong></li>
                  <li><span>Correo contacto</span><strong>{{ selectedPedido.contactEmail || 'Sin correo' }}</strong></li>
                </ul>
              </article>
              <article class="panel">
                <h4>Identificacion del pedido</h4>
                <ul>
                  <li><span>Servicio</span><strong>{{ selectedPedido.service || 'Sin servicio' }}</strong></li>
                  <li><span>Descripcion del problema</span><strong>{{ selectedPedido.diagnosis || 'Sin descripcion' }}</strong></li>
                  <li><span>Urgente</span><strong>{{ selectedPedido.urgent ? 'Si' : 'No' }}</strong></li>
                  <li><span>Fecha alta</span><strong>{{ selectedPedido.date }}</strong></li>
                  <li><span>Prioridad</span><strong>{{ selectedPedido.priority }}</strong></li>
                </ul>
              </article>
            </section>

            <section v-else-if="activeTab === 'historial'" class="panel timeline">
              <h4>Historial</h4>
              <ol>
                <li v-for="entry in selectedPedido.history" :key="entry.when + entry.note">
                  <strong>{{ entry.when }}</strong>
                  <p>{{ entry.note }}</p>
                </li>
              </ol>
            </section>

            <section v-else-if="activeTab === 'asignacion'" class="asignacion-flow">
              <article class="panel assignment-control" v-if="selectedAssignment">
                <div>
                  <h4>Asignacion tecnica</h4>
                  <p class="assignment-note">
                    {{ selectedAssignment.registered ? 'Ya existe una visita registrada. Puedes reprogramar cuando lo necesites.' : 'Inicia el flujo para asignar tecnico y equipamiento.' }}
                  </p>
                </div>
                <button class="btn primary assign-trigger" @click="openAssignmentProcess">
                  {{ selectedAssignment.registered ? 'Reprogramar' : 'Asignar tecnico' }}
                </button>
              </article>

              <article class="panel assignment-summary" v-if="selectedAssignment?.registered">
                <h4>Resumen de asignacion registrada</h4>
                <div class="summary-grid">
                  <div class="summary-item"><span>Contacto</span><strong>{{ selectedAssignment.contactName }}</strong></div>
                  <div class="summary-item"><span>Fecha visita</span><strong>{{ selectedAssignment.availableDate }}</strong></div>
                  <div class="summary-item"><span>Horario</span><strong>{{ selectedAssignment.startTime }} - {{ selectedAssignment.endTime }}</strong></div>
                  <div class="summary-item"><span>Tecnico</span><strong>{{ selectedAssignedTech?.fullName || 'Sin tecnico' }}</strong></div>
                  <div class="summary-item"><span>DNI tecnico</span><strong>{{ selectedAssignedTech?.dni || 'Sin DNI' }}</strong></div>
                  <div class="summary-item"><span>Especialidad</span><strong>{{ selectedAssignedTech?.specialty || 'Sin especialidad' }}</strong></div>
                  <div class="summary-item"><span>Movilidad</span><strong>S/ {{ Number(selectedAssignment.mobilityPrice || 0).toFixed(2) }}</strong></div>
                  <div class="summary-item"><span>Terceros</span><strong>S/ {{ Number(selectedAssignment.thirdPartyPrice || 0).toFixed(2) }}</strong></div>
                  <div class="summary-item"><span>Empresa terceros</span><strong>{{ selectedAssignment.thirdPartyCompany }}</strong></div>
                  <div class="summary-item full"><span>EPPs seleccionados</span><strong>{{ selectedEppNames.join(', ') || 'Sin EPPs seleccionados' }}</strong></div>
                </div>
              </article>

              <article class="panel assignment-steps" v-if="selectedAssignment?.processOpen">
                <button class="step-pill" :class="{ active: selectedAssignment.step === 1, done: selectedAssignment.step > 1 }" @click="goToAssignmentStep(1)">1. Visita</button>
                <button class="step-pill" :class="{ active: selectedAssignment.step === 2, done: selectedAssignment.step > 2 }" @click="goToAssignmentStep(2)" :disabled="!canGoTechStep">2. Personal</button>
                <button class="step-pill" :class="{ active: selectedAssignment.step === 3, done: selectedAssignment.registered }" @click="goToAssignmentStep(3)" :disabled="!selectedAssignment.selectedTechId">3. Equipamiento</button>
              </article>

              <article class="panel" v-if="selectedAssignment?.processOpen && selectedAssignment.step === 1">
                <h4>Planificacion de visita</h4>
                <div class="assign-form-grid">
                  <label>
                    Contacto (autocompletado)
                    <input v-model="selectedAssignment.contactName" placeholder="Contacto del cliente" />
                  </label>
                  <label>
                    Fecha disponible
                    <input v-model="selectedAssignment.availableDate" type="date" />
                  </label>
                  <label>
                    Hora inicio
                    <input v-model="selectedAssignment.startTime" type="time" />
                  </label>
                  <label>
                    Hora fin
                    <input v-model="selectedAssignment.endTime" type="time" />
                  </label>
                  <label>
                    Precio movilidad (S/)
                    <input v-model="selectedAssignment.mobilityPrice" type="number" min="0" step="0.01" />
                  </label>
                  <label>
                    Precio terceros / empresa (S/)
                    <input v-model="selectedAssignment.thirdPartyPrice" type="number" min="0" step="0.01" />
                  </label>
                  <label>
                    Empresa de terceros
                    <input v-model="selectedAssignment.thirdPartyCompany" placeholder="Proveedor / tercero" />
                  </label>
                  <label class="wide">
                    Detalles adicionales
                    <textarea
                      v-model="selectedAssignment.additionalDetails"
                      rows="4"
                      placeholder="Indicaciones, accesos, restricciones, observaciones"
                    ></textarea>
                  </label>
                </div>
                <div class="form-actions">
                  <button class="btn ghost" @click="selectedAssignment.processOpen = false">Cancelar</button>
                  <button class="btn primary" :disabled="!canGoTechStep" @click="goToAssignmentStep(2)">
                    Continuar a personal
                  </button>
                </div>
              </article>

              <article class="panel" v-else-if="selectedAssignment?.processOpen && selectedAssignment.step === 2">
                <h4>Seleccion de personal recomendado</h4>
                <div class="tech-grid">
                  <button
                    v-for="tech in rankedTechs"
                    :key="tech.id"
                    class="tech-card"
                    :class="{ active: selectedAssignment.selectedTechId === tech.id }"
                    @click="selectTechnician(tech.id)"
                  >
                    <div class="tech-head">
                      <strong>{{ tech.fullName }}</strong>
                      <span>DNI {{ tech.dni }}</span>
                    </div>
                    <p><strong>Especialidad:</strong> {{ tech.specialty }}</p>
                    <p><strong>Vive en:</strong> {{ tech.homeDistrict }}</p>
                    <p><strong>Horario:</strong> {{ tech.workSchedule }}</p>
                    <div class="score-track">
                      <span :style="{ width: `${tech.score}%` }"></span>
                    </div>
                    <small>{{ tech.score }}% apto - {{ aptitudeLabel(tech.score) }}</small>
                  </button>
                </div>
                <div class="form-actions">
                  <button class="btn ghost" @click="selectedAssignment.processOpen = false">Cancelar</button>
                  <button class="btn ghost" @click="goToAssignmentStep(1)">Volver</button>
                  <button class="btn primary" :disabled="!selectedAssignment.selectedTechId" @click="goToAssignmentStep(3)">
                    Continuar a equipamiento
                  </button>
                </div>
              </article>

              <article class="panel" v-else-if="selectedAssignment?.processOpen">
                <h4>Equipamiento y EPPs de inventario</h4>
                <p class="assignment-note">Selecciona el equipamiento necesario para registrar la visita.</p>
                <div class="epp-grid">
                  <label v-for="item in eppCatalog" :key="item.id" class="epp-item">
                    <input
                      type="checkbox"
                      :checked="selectedAssignment.selectedEpps.includes(item.id)"
                      @change="toggleEpp(item.id, ($event.target as HTMLInputElement).checked)"
                    />
                    <div>
                      <strong>{{ item.name }}</strong>
                      <small>Stock: {{ item.stock }} - {{ item.category }}</small>
                    </div>
                  </label>
                </div>
                <div class="form-actions">
                  <button class="btn ghost" @click="selectedAssignment.processOpen = false">Cancelar</button>
                  <button class="btn ghost" @click="goToAssignmentStep(2)">Volver</button>
                  <button class="btn primary" :disabled="!canRegisterVisit" @click="registerVisit">
                    Registrar visita
                  </button>
                </div>
              </article>
            </section>

            <section v-else-if="activeTab === 'diagnostico'" class="panel">
              <h4>Diagnostico tecnico</h4>
              <textarea
                v-model="selectedPedido.diagnosis"
                rows="7"
                placeholder="Describe causa raiz, evidencia y plan de accion"
              ></textarea>
              <button class="btn primary" @click="pushHistory('Diagnostico actualizado')">
                Guardar diagnostico
              </button>
            </section>

            <section v-else class="costs-stack">
              <div class="cost-toolbar panel">
                <div>
                  <h4>Costos del pedido</h4>
                  <p>Snapshot referencial del pedido. Puedes recalcular para actualizar montos.</p>
                </div>
                <button class="btn ghost" @click="recalculateCosts">Recalcular</button>
              </div>

              <div class="cost-kpis">
                <article class="panel mini">
                  <span>Total directo</span>
                  <strong>S/ {{ selectedPedido.costs.direct.toLocaleString('es-PE') }}</strong>
                </article>
                <article class="panel mini">
                  <span>Total absorbido</span>
                  <strong>S/ {{ selectedPedido.costs.absorbed.toLocaleString('es-PE') }}</strong>
                </article>
                <article class="panel mini">
                  <span>Lineas</span>
                  <strong>{{ selectedPedido.costs.lines.length }}</strong>
                </article>
              </div>

              <article class="panel subtotals">
                <h4>Subtotales</h4>
                <div>
                  <p><span>Materiales</span><strong>S/ {{ selectedPedido.costs.materials.toLocaleString('es-PE') }}</strong></p>
                  <p><span>Movilidad</span><strong>S/ {{ selectedPedido.costs.mobility.toLocaleString('es-PE') }}</strong></p>
                  <p><span>Terceros</span><strong>S/ {{ selectedPedido.costs.thirdParties.toLocaleString('es-PE') }}</strong></p>
                  <p><span>Tecnico</span><strong>S/ {{ selectedPedido.costs.tech.toLocaleString('es-PE') }}</strong></p>
                </div>
              </article>

              <article class="panel">
                <h4>Lineas de costo</h4>
                <div class="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Tipo</th>
                        <th>Descripcion</th>
                        <th class="num">Cant.</th>
                        <th class="num">Unitario</th>
                        <th class="num">Importe</th>
                        <th>Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="line in selectedPedido.costs.lines" :key="line.name">
                        <td>{{ line.type }}</td>
                        <td>{{ line.name }}</td>
                        <td class="num">{{ line.qty }}</td>
                        <td class="num">S/ {{ line.unit.toLocaleString('es-PE') }}</td>
                        <td class="num">S/ {{ line.amount.toLocaleString('es-PE') }}</td>
                        <td>
                          <span class="state" :data-state="line.pending ? 'pending' : 'ok'">
                            {{ line.pending ? 'Pendiente' : 'Completo' }}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </article>
            </section>
            </div>
          </section>
        </template>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';

type PhaseKey = 'deteccion' | 'asignacion' | 'cierre' | 'facturacion';
type TabKey = 'detalles' | 'historial' | 'asignacion' | 'diagnostico' | 'costos';

interface CostLine {
  type: string;
  name: string;
  qty: number;
  unit: number;
  amount: number;
  pending?: boolean;
}

interface PedidoItem {
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
    lines: CostLine[];
  };
}

interface TechnicianProfile {
  id: string;
  fullName: string;
  dni: string;
  specialty: string;
  homeDistrict: string;
  workSchedule: string;
}

interface EppItem {
  id: string;
  name: string;
  stock: number;
  category: string;
}

interface AssignmentDraft {
  step: 1 | 2 | 3;
  processOpen: boolean;
  contactName: string;
  availableDate: string;
  startTime: string;
  endTime: string;
  additionalDetails: string;
  mobilityPrice: string;
  thirdPartyPrice: string;
  thirdPartyCompany: string;
  selectedTechId: string;
  selectedEpps: string[];
  registered: boolean;
  registeredAt: string;
}

interface AccountCatalogItem {
  code: string;
  clientName: string;
  accountName: string;
  contactName: string;
  referenceAddress: string;
  district: string;
  coordinates: string;
  documentNumber: string;
  contactPhone: string;
  contactEmail: string;
  defaultService: string;
}

const phaseLabel: Record<PhaseKey, string> = {
  deteccion: 'Deteccion',
  asignacion: 'Asignacion',
  cierre: 'Cierre',
  facturacion: 'Facturacion',
};

const phaseOrder: PhaseKey[] = ['deteccion', 'asignacion', 'cierre', 'facturacion'];

const workflowPhases = [
  { key: 'deteccion' as const, order: '01', label: 'Deteccion' },
  { key: 'asignacion' as const, order: '02', label: 'Asignacion' },
  { key: 'cierre' as const, order: '03', label: 'Cierre' },
  { key: 'facturacion' as const, order: '04', label: 'Facturacion' },
];

const phaseFilters = [{ key: 'all', label: 'Todos' }, ...workflowPhases.map((p) => ({ key: p.key, label: p.label }))];

const accountCatalog: AccountCatalogItem[] = [
  {
    code: 'CUE-1001',
    clientName: 'Clinica Miraflores',
    accountName: 'Sede Principal',
    contactName: 'Laura Medina',
    referenceAddress: 'Av. Arequipa 1001, frente a farmacia central',
    district: 'Miraflores',
    coordinates: '-12.1211, -77.0297',
    documentNumber: '20548796321',
    contactPhone: '987 123 111',
    contactEmail: 'laura.medina@clinicamf.pe',
    defaultService: 'Mantenimiento electrico integral',
  },
  {
    code: 'CUE-1002',
    clientName: 'Clinica Miraflores',
    accountName: 'Sede Emergencias',
    contactName: 'Pedro Chavez',
    referenceAddress: 'Jr. Las Flores 221, torre 2',
    district: 'La Molina',
    coordinates: '-12.0749, -76.9512',
    documentNumber: '20548796321',
    contactPhone: '987 123 222',
    contactEmail: 'pedro.chavez@clinicamf.pe',
    defaultService: 'Mantenimiento de UPS y tableros',
  },
  {
    code: 'CUE-2001',
    clientName: 'Condominio Brisas',
    accountName: 'Torre A',
    contactName: 'Marta Solis',
    referenceAddress: 'Calle Parque Norte 450',
    district: 'Surco',
    coordinates: '-12.1405, -76.9910',
    documentNumber: '20600154789',
    contactPhone: '965 774 100',
    contactEmail: 'administracion@brisas.pe',
    defaultService: 'Reparacion de bombas de agua',
  },
  {
    code: 'CUE-3001',
    clientName: 'Retail Norte SAC',
    accountName: 'Local San Isidro',
    contactName: 'Rosa Calderon',
    referenceAddress: 'Av. Rivera Navarrete 3201',
    district: 'San Isidro',
    coordinates: '-12.0962, -77.0307',
    documentNumber: '20114589632',
    contactPhone: '955 441 990',
    contactEmail: 'soporte@retailnorte.com',
    defaultService: 'Cableado estructurado piso 3',
  },
];

const commonServices = [
  'Mantenimiento electrico integral',
  'Mantenimiento de UPS y tableros',
  'Reparacion de bombas de agua',
  'Cableado estructurado',
  'Instalacion de luminarias',
  'Soporte de infraestructura',
];

const tabs: Array<{ key: TabKey; label: string }> = [
  { key: 'detalles', label: 'Detalles' },
  { key: 'historial', label: 'Historial' },
  { key: 'asignacion', label: 'Asignacion' },
  { key: 'diagnostico', label: 'Diagnostico' },
  { key: 'costos', label: 'Costos' },
];

const techniciansCatalog: TechnicianProfile[] = [
  {
    id: 'tec-1',
    fullName: 'Luis Rojas Alvarado',
    dni: '45874521',
    specialty: 'Electrico industrial',
    homeDistrict: 'Miraflores',
    workSchedule: '08:00 - 17:00',
  },
  {
    id: 'tec-2',
    fullName: 'Carlos Palacios Vera',
    dni: '47221850',
    specialty: 'UPS y tableros',
    homeDistrict: 'La Molina',
    workSchedule: '09:00 - 18:00',
  },
  {
    id: 'tec-3',
    fullName: 'Martha Pino Cardenas',
    dni: '43661772',
    specialty: 'Cableado estructurado',
    homeDistrict: 'San Isidro',
    workSchedule: '07:30 - 16:30',
  },
  {
    id: 'tec-4',
    fullName: 'Jorge Saldana Quispe',
    dni: '48977534',
    specialty: 'Bombas y sistemas hidraulicos',
    homeDistrict: 'Surco',
    workSchedule: '08:00 - 17:00',
  },
];

const eppCatalog: EppItem[] = [
  { id: 'epp-1', name: 'Casco dielctrico', stock: 34, category: 'Proteccion cabeza' },
  { id: 'epp-2', name: 'Guantes dielctricos', stock: 52, category: 'Proteccion manos' },
  { id: 'epp-3', name: 'Lentes de seguridad', stock: 41, category: 'Proteccion visual' },
  { id: 'epp-4', name: 'Arnes de seguridad', stock: 19, category: 'Trabajo en altura' },
  { id: 'epp-5', name: 'Botas punta de acero', stock: 27, category: 'Proteccion pies' },
];

const pedidos = ref<PedidoItem[]>([
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
    urgent: false,
    service: 'Mantenimiento electrico integral',
    status: 'En proceso',
    phase: 'asignacion',
    priority: 'alta',
    date: '2026-03-22',
    tech: 'Luis Rojas',
    diagnosis: 'Se detecta sobrecarga en tablero secundario y cableado deteriorado.',
    history: [
      { when: '24 Mar 11:10', note: 'Validacion de materiales completada.' },
      { when: '24 Mar 10:46', note: 'Asignacion confirmada a Luis Rojas.' },
      { when: '24 Mar 10:20', note: 'Cliente confirma ventana de atencion de 2:00 p.m. a 4:00 p.m.' },
      { when: '24 Mar 09:55', note: 'Se adjunta evidencia fotografica del tablero secundario.' },
      { when: '23 Mar 18:30', note: 'Se solicita prueba termografica con tercero.' },
      { when: '23 Mar 16:12', note: 'Diagnostico preliminar registrado por tecnico.' },
      { when: '22 Mar 09:10', note: 'Visita tecnica preliminar coordinada.' },
      { when: '22 Mar 08:21', note: 'Pedido creado por mesa de ayuda.' },
    ],
    costs: {
      total: 4280,
      direct: 3720,
      absorbed: 560,
      margin: 19,
      materials: 2200,
      mobility: 180,
      thirdParties: 640,
      tech: 1260,
      lines: [
        { type: 'Material', name: 'Interruptor termomagnetico', qty: 2, unit: 280, amount: 560 },
        { type: 'Material', name: 'Cable NYY 3x10', qty: 35, unit: 22, amount: 770 },
        { type: 'Movilidad', name: 'Traslado tecnico', qty: 1, unit: 180, amount: 180 },
        { type: 'Tecnico', name: 'HH tecnico campo', qty: 9, unit: 140, amount: 1260 },
        { type: 'Terceros', name: 'Prueba termografica', qty: 1, unit: 640, amount: 640, pending: true },
      ],
    },
  },
  {
    id: '2',
    code: 'OT-1085',
    accountCode: 'CUE-2001',
    client: 'Condominio Brisas',
    contactName: 'Marta Solis',
    referenceAddress: 'Calle Parque Norte 450',
    district: 'Surco',
    coordinates: '-12.1405, -76.9910',
    documentNumber: '20600154789',
    contactPhone: '965 774 100',
    contactEmail: 'administracion@brisas.pe',
    urgent: false,
    service: 'Reparacion de bombas de agua',
    status: 'Pendiente',
    phase: 'deteccion',
    priority: 'media',
    date: '2026-03-23',
    diagnosis: 'Requiere inspeccion de tablero de control y valvulas de retencion.',
    history: [{ when: '23 Mar 10:45', note: 'Cliente reporta falla intermitente en bomba principal.' }],
    costs: {
      total: 2650,
      direct: 2190,
      absorbed: 460,
      margin: 15,
      materials: 1320,
      mobility: 210,
      thirdParties: 320,
      tech: 800,
      lines: [
        { type: 'Material', name: 'Kit sello mecanico', qty: 1, unit: 690, amount: 690 },
        { type: 'Material', name: 'Valvula check 2"', qty: 2, unit: 315, amount: 630 },
        { type: 'Tecnico', name: 'HH tecnico especialista', qty: 5, unit: 160, amount: 800 },
        { type: 'Movilidad', name: 'Traslado y carga', qty: 1, unit: 210, amount: 210 },
        { type: 'Terceros', name: 'Balanceo de rotor', qty: 1, unit: 320, amount: 320 },
      ],
    },
  },
  {
    id: '3',
    code: 'OT-1081',
    accountCode: 'CUE-3001',
    client: 'Retail Norte SAC',
    contactName: 'Rosa Calderon',
    referenceAddress: 'Av. Rivera Navarrete 3201',
    district: 'San Isidro',
    coordinates: '-12.0962, -77.0307',
    documentNumber: '20114589632',
    contactPhone: '955 441 990',
    contactEmail: 'soporte@retailnorte.com',
    urgent: false,
    service: 'Cableado estructurado piso 3',
    status: 'Por facturar',
    phase: 'facturacion',
    priority: 'baja',
    date: '2026-03-19',
    tech: 'Martha Pino',
    diagnosis: 'Instalacion culminada, pendiente conformidad administrativa.',
    history: [
      { when: '19 Mar 14:10', note: 'Pedido creado y validado con compras.' },
      { when: '20 Mar 16:30', note: 'Trabajo ejecutado y cliente conforme.' },
      { when: '21 Mar 11:02', note: 'Pendiente emision de factura.' },
    ],
    costs: {
      total: 5170,
      direct: 4470,
      absorbed: 700,
      margin: 22,
      materials: 2850,
      mobility: 120,
      thirdParties: 540,
      tech: 1660,
      lines: [
        { type: 'Material', name: 'Patch panel 48 puertos', qty: 2, unit: 460, amount: 920 },
        { type: 'Material', name: 'Cable UTP Cat6', qty: 9, unit: 185, amount: 1665 },
        { type: 'Tecnico', name: 'HH cuadrilla cableado', qty: 10, unit: 166, amount: 1660 },
        { type: 'Terceros', name: 'Certificacion puntos', qty: 1, unit: 540, amount: 540 },
        { type: 'Movilidad', name: 'Traslado de materiales', qty: 1, unit: 120, amount: 120 },
      ],
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
    status: 'En proceso',
    phase: 'cierre',
    priority: 'critica',
    date: '2026-03-24',
    tech: 'Carlos Palacios',
    diagnosis: 'Bateria en degradacion acelerada, se recomienda reemplazo parcial.',
    history: [
      { when: '24 Mar 13:10', note: 'Informe de cierre enviado al cliente.' },
      { when: '24 Mar 11:42', note: 'Prueba de autonomia completada.' },
      { when: '24 Mar 09:05', note: 'Pedido marcado como urgente por cliente.' },
    ],
    costs: {
      total: 6120,
      direct: 5280,
      absorbed: 840,
      margin: 21,
      materials: 3610,
      mobility: 140,
      thirdParties: 430,
      tech: 1100,
      lines: [
        { type: 'Material', name: 'Bateria UPS 12V', qty: 8, unit: 320, amount: 2560 },
        { type: 'Tecnico', name: 'HH tecnico electrico', qty: 8, unit: 138, amount: 1104 },
        { type: 'Terceros', name: 'Gestion de residuos', qty: 1, unit: 430, amount: 430 },
      ],
    },
  },
  {
    id: '5',
    code: 'OT-1091',
    accountCode: 'CUE-2001',
    client: 'Condominio Brisas',
    contactName: 'Marta Solis',
    referenceAddress: 'Calle Parque Norte 450',
    district: 'Surco',
    coordinates: '-12.1405, -76.9910',
    documentNumber: '20600154789',
    contactPhone: '965 774 100',
    contactEmail: 'administracion@brisas.pe',
    urgent: false,
    service: 'Instalacion de luminarias',
    status: 'Pendiente',
    phase: 'deteccion',
    priority: 'media',
    date: '2026-03-24',
    diagnosis: 'Se reportan 12 puntos de luz apagados en sotano.',
    history: [{ when: '24 Mar 09:02', note: 'Pedido generado desde inspeccion preventiva.' }],
    costs: {
      total: 1680,
      direct: 1470,
      absorbed: 210,
      margin: 12,
      materials: 970,
      mobility: 120,
      thirdParties: 0,
      tech: 380,
      lines: [
        { type: 'Material', name: 'Luminaria LED 24W', qty: 12, unit: 62, amount: 744 },
        { type: 'Tecnico', name: 'HH tecnico campo', qty: 3, unit: 126, amount: 378 },
      ],
    },
  },
  {
    id: '6',
    code: 'OT-1092',
    accountCode: 'CUE-3001',
    client: 'Retail Norte SAC',
    contactName: 'Rosa Calderon',
    referenceAddress: 'Av. Rivera Navarrete 3201',
    district: 'San Isidro',
    coordinates: '-12.0962, -77.0307',
    documentNumber: '20114589632',
    contactPhone: '955 441 990',
    contactEmail: 'soporte@retailnorte.com',
    urgent: false,
    service: 'Soporte de infraestructura',
    status: 'Por facturar',
    phase: 'facturacion',
    priority: 'baja',
    date: '2026-03-18',
    tech: 'Martha Pino',
    diagnosis: 'Incidencia cerrada, pendiente envio de conformidad.',
    history: [
      { when: '23 Mar 15:40', note: 'Conformidad tecnica aprobada.' },
      { when: '21 Mar 12:15', note: 'Trabajo finalizado sin observaciones.' },
    ],
    costs: {
      total: 2890,
      direct: 2440,
      absorbed: 450,
      margin: 18,
      materials: 950,
      mobility: 110,
      thirdParties: 280,
      tech: 1100,
      lines: [
        { type: 'Tecnico', name: 'HH soporte campo', qty: 7, unit: 157, amount: 1099 },
        { type: 'Material', name: 'Canaleta PVC', qty: 18, unit: 26, amount: 468 },
      ],
    },
  },
]);

const selectedId = ref<string>(pedidos.value[0]?.id || '');
const activeTab = ref<TabKey>('detalles');
const creating = ref(false);
const createStep = ref<1 | 2>(1);
const phaseFilter = ref<'all' | PhaseKey>('all');
const searchQuery = ref('');

const form = reactive({
  accountCode: '',
  clientName: '',
  contactName: '',
  referenceAddress: '',
  district: '',
  coordinates: '',
  documentNumber: '',
  contactPhone: '',
  contactEmail: '',
  service: '',
  problemDescription: '',
  urgent: false,
});

const assignmentByPedido = reactive<Record<string, AssignmentDraft>>({});

const selectedAccount = computed(() => {
  const code = form.accountCode.trim().toUpperCase();
  return accountCatalog.find((acc) => acc.code === code) || null;
});

const linkedAccounts = computed(() => {
  if (!selectedAccount.value) return [];
  return accountCatalog
    .filter((acc) => acc.clientName === selectedAccount.value?.clientName && acc.code !== selectedAccount.value?.code)
    .map((acc) => `${acc.code} (${acc.accountName})`);
});

const filteredPedidos = computed(() => {
  const query = searchQuery.value.trim().toLowerCase();
  return pedidos.value.filter((p) => {
    const byPhase = phaseFilter.value === 'all' || p.phase === phaseFilter.value;
    if (!byPhase) return false;
    if (!query) return true;
    return (
      p.code.toLowerCase().includes(query)
      || p.client.toLowerCase().includes(query)
      || p.service.toLowerCase().includes(query)
    );
  });
});

const selectedPedido = computed(() => pedidos.value.find((p) => p.id === selectedId.value));
const selectedAssignment = computed(() => {
  if (!selectedPedido.value) return null;
  const pedido = selectedPedido.value;
  if (!assignmentByPedido[pedido.id]) {
    assignmentByPedido[pedido.id] = {
      step: 1,
      processOpen: false,
      contactName: pedido.contactName || '',
      availableDate: '',
      startTime: '',
      endTime: '',
      additionalDetails: '',
      mobilityPrice: String(pedido.costs.mobility || ''),
      thirdPartyPrice: String(pedido.costs.thirdParties || ''),
      thirdPartyCompany: '',
      selectedTechId: '',
      selectedEpps: [],
      registered: false,
      registeredAt: '',
    };
  }
  return assignmentByPedido[pedido.id];
});

const canGoTechStep = computed(() => {
  const draft = selectedAssignment.value;
  if (!draft) return false;
  if (!draft.contactName.trim() || !draft.availableDate || !draft.startTime || !draft.endTime) return false;
  if (!draft.additionalDetails.trim() || !draft.thirdPartyCompany.trim()) return false;
  if (Number(draft.mobilityPrice) < 0 || Number(draft.thirdPartyPrice) < 0) return false;
  return draft.endTime > draft.startTime;
});

const rankedTechs = computed(() => {
  if (!selectedPedido.value || !selectedAssignment.value) return [];
  return techniciansCatalog
    .map((tech) => ({
      ...tech,
      score: calculateTechScore(selectedPedido.value!, tech, selectedAssignment.value!),
    }))
    .sort((a, b) => b.score - a.score);
});

const selectedAssignedTech = computed(() => {
  if (!selectedAssignment.value?.selectedTechId) return null;
  return techniciansCatalog.find((tech) => tech.id === selectedAssignment.value?.selectedTechId) || null;
});

const selectedEppNames = computed(() => {
  const selected = selectedAssignment.value?.selectedEpps || [];
  return eppCatalog.filter((item) => selected.includes(item.id)).map((item) => item.name);
});

const canRegisterVisit = computed(() => {
  const draft = selectedAssignment.value;
  if (!draft) return false;
  return Boolean(draft.selectedTechId && draft.selectedEpps.length > 0);
});
const currentPhaseIndex = computed(() => {
  const phase = selectedPedido.value?.phase;
  if (!phase) return 0;
  const idx = phaseOrder.indexOf(phase);
  return idx >= 0 ? idx : 0;
});
const phaseProgress = computed(() => {
  if (workflowPhases.length < 2) return 0;
  return (currentPhaseIndex.value / (workflowPhases.length - 1)) * 100;
});

function countByPhase(key: 'all' | PhaseKey) {
  if (key === 'all') return pedidos.value.length;
  return pedidos.value.filter((p) => p.phase === key).length;
}

function selectPedido(id: string) {
  selectedId.value = id;
  creating.value = false;
}

function goToAssignmentStep(step: 1 | 2 | 3) {
  if (!selectedAssignment.value) return;
  if (step === 2 && !canGoTechStep.value) return;
  if (step === 3 && !selectedAssignment.value.selectedTechId) return;
  selectedAssignment.value.step = step;
}

function openAssignmentProcess() {
  if (!selectedAssignment.value || !selectedPedido.value) return;
  if (!selectedAssignment.value.contactName.trim()) {
    selectedAssignment.value.contactName = selectedPedido.value.contactName || '';
  }
  selectedAssignment.value.processOpen = true;
  selectedAssignment.value.step = 1;
}

function aptitudeLabel(score: number) {
  if (score >= 85) return 'Muy recomendado';
  if (score >= 70) return 'Recomendado';
  if (score >= 55) return 'Aceptable';
  return 'Baja afinidad';
}

function calculateTechScore(pedido: PedidoItem, tech: TechnicianProfile, draft: AssignmentDraft) {
  const text = `${pedido.service} ${pedido.diagnosis}`.toLowerCase();
  const specialty = tech.specialty.toLowerCase();
  let score = 35;

  if (text.includes('electr') && specialty.includes('electr')) score += 28;
  if (text.includes('ups') && specialty.includes('ups')) score += 28;
  if (text.includes('cable') && specialty.includes('cable')) score += 28;
  if ((text.includes('bomba') || text.includes('hidraul')) && specialty.includes('bomba')) score += 28;

  if ((pedido.district || '').toLowerCase().includes(tech.homeDistrict.toLowerCase())) score += 16;
  if (draft.startTime >= '08:00' && draft.endTime <= '18:30') score += 10;
  if (pedido.urgent) score += 6;

  return Math.max(35, Math.min(98, score));
}

function selectTechnician(techId: string) {
  if (!selectedAssignment.value) return;
  selectedAssignment.value.selectedTechId = techId;
}

function toggleEpp(itemId: string, checked: boolean) {
  if (!selectedAssignment.value) return;
  if (checked) {
    if (!selectedAssignment.value.selectedEpps.includes(itemId)) {
      selectedAssignment.value.selectedEpps.push(itemId);
    }
    return;
  }
  selectedAssignment.value.selectedEpps = selectedAssignment.value.selectedEpps.filter((id) => id !== itemId);
}

function registerVisit() {
  if (!selectedAssignment.value || !selectedPedido.value || !canRegisterVisit.value) return;

  const draft = selectedAssignment.value;
  const tech = selectedAssignedTech.value;
  if (!tech) return;

  selectedPedido.value.tech = tech.fullName;
  selectedPedido.value.costs.mobility = Number(draft.mobilityPrice || 0);
  selectedPedido.value.costs.thirdParties = Number(draft.thirdPartyPrice || 0);
  draft.registered = true;
  draft.registeredAt = new Date().toISOString();
  draft.processOpen = false;

  pushHistory(
    `Visita registrada con ${tech.fullName} (${tech.dni}). EPPs: ${selectedEppNames.value.join(', ') || 'sin EPPs'}`
  );
}

function applyAccountByCode() {
  const account = selectedAccount.value;
  if (!account) return;
  form.accountCode = account.code;
  form.clientName = account.clientName;
  form.contactName = account.contactName;
  form.referenceAddress = account.referenceAddress;
  form.district = account.district;
  form.coordinates = account.coordinates;
  form.documentNumber = account.documentNumber;
  form.contactPhone = account.contactPhone;
  form.contactEmail = account.contactEmail;
  if (!form.service.trim()) form.service = account.defaultService;
}

function goToStepTwo() {
  const stepOneValid = (
    form.accountCode.trim()
    && form.clientName.trim()
    && form.contactName.trim()
    && form.referenceAddress.trim()
    && form.district.trim()
    && form.coordinates.trim()
    && form.documentNumber.trim()
    && form.contactPhone.trim()
    && form.contactEmail.trim()
  );
  if (!stepOneValid) return;
  createStep.value = 2;
}

function updatePhase(phase: PhaseKey) {
  if (!selectedPedido.value) return;
  selectedPedido.value.phase = phase;
  if (phase === 'facturacion') selectedPedido.value.status = 'Por facturar';
  if (phase === 'cierre') selectedPedido.value.status = 'En cierre';
  if (phase === 'asignacion') selectedPedido.value.status = 'En proceso';
  if (phase === 'deteccion') selectedPedido.value.status = 'Pendiente';
  pushHistory(`Fase actualizada a ${phaseLabel[phase]}`);
}

function goToNextPhase() {
  if (!selectedPedido.value) return;
  const current = phaseOrder.indexOf(selectedPedido.value.phase);
  if (current < 0 || current >= phaseOrder.length - 1) return;
  updatePhase(phaseOrder[current + 1]);
}

function pushHistory(note: string) {
  if (!selectedPedido.value) return;
  const now = new Date();
  const stamp = now.toLocaleString('es-PE', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
  selectedPedido.value.history.unshift({ when: stamp, note });
}

function openCreate() {
  creating.value = true;
  createStep.value = 1;
  activeTab.value = 'detalles';
}

function createPedido() {
  if (!form.service.trim()) return;
  const nextNumber = 1086 + pedidos.value.length;
  const newPedido: PedidoItem = {
    id: String(Date.now()),
    code: `OT-${nextNumber}`,
    accountCode: form.accountCode,
    client: form.clientName,
    contactName: form.contactName,
    referenceAddress: form.referenceAddress,
    district: form.district,
    coordinates: form.coordinates,
    documentNumber: form.documentNumber,
    contactPhone: form.contactPhone,
    contactEmail: form.contactEmail,
    urgent: form.urgent,
    service: form.service,
    status: 'Pendiente',
    phase: 'deteccion',
    priority: form.urgent ? 'critica' : 'media',
    date: new Date().toISOString().slice(0, 10),
    diagnosis: form.problemDescription || 'Sin info adicional.',
    history: [{ when: 'Ahora', note: `Cuenta ${form.accountCode || 'SIN-CODIGO'} - ${form.contactName} (${form.contactPhone})` }],
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

  pedidos.value.unshift(newPedido);
  selectedId.value = newPedido.id;
  creating.value = false;
  createStep.value = 1;
  activeTab.value = 'detalles';

  form.accountCode = '';
  form.clientName = '';
  form.contactName = '';
  form.referenceAddress = '';
  form.district = '';
  form.coordinates = '';
  form.documentNumber = '';
  form.contactPhone = '';
  form.contactEmail = '';
  form.service = '';
  form.problemDescription = '';
  form.urgent = false;
}

function recalculateCosts() {
  if (!selectedPedido.value) return;
  selectedPedido.value.costs.absorbed = Math.round(selectedPedido.value.costs.direct * 0.16);
  selectedPedido.value.costs.total = selectedPedido.value.costs.direct + selectedPedido.value.costs.absorbed;
  selectedPedido.value.costs.margin = Math.max(8, Math.min(34, selectedPedido.value.costs.margin + 1));
  pushHistory('Snapshot de costos recalculado');
}
</script>

<style scoped>
.pedidos-view {
  --bg-card: #0f1c2b;
  --bg-soft: #122437;
  --bg-soft-2: #13263b;
  --text-main: #ebf2fb;
  --text-muted: #9db3cb;
  --border-light: #4a6078;
  --border-strong: #e3edf8;
  --radius: 4px;

  display: grid;
  grid-template-rows: 48px minmax(0, 1fr);
  gap: 0;
  height: calc(100dvh - 24px);
  max-height: calc(100dvh - 24px);
}

.card {
  background: linear-gradient(180deg, #122235 0%, #0f1c2b 100%);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
}

.head {
  height: 48px;
  padding: 4px 8px;
  min-height: 48px;
  max-height: 48px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 6px;
  background:
    linear-gradient(90deg, rgba(83, 188, 255, 0.14), rgba(121, 227, 195, 0.06) 45%, transparent 75%),
    #0f1c2b;
}

h2,
h3,
h4 {
  margin: 0;
  color: var(--text-main);
}

h2 {
  font-size: 0.93rem;
  line-height: 1.05;
}

.head p,
.create-head p,
.detail-head p,
.cost-toolbar p {
  margin: 2px 0 0;
  color: var(--text-muted);
}

.head p {
  font-size: 0.72rem;
}

.head-actions {
  display: flex;
  gap: 6px;
}

.btn {
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  padding: 4px 8px;
  font-size: 0.76rem;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.btn:hover {
  border-color: var(--border-strong);
  transform: translateY(-1px);
}

.btn.primary {
  background: linear-gradient(120deg, #16a34a, #059669);
  border-color: #79e3c3;
  color: #f4fff8;
}

.btn.ghost {
  background: var(--bg-soft-2);
  color: #d5e5f7;
}

.layout {
  min-height: 0;
  height: auto;
  display: grid;
  grid-template-columns: 315px 1fr;
  gap: 10px;
  padding-top: 6px;
  margin-top: 0;
}

.list {
  min-height: 0;
  display: grid;
  grid-template-rows: auto auto 1fr;
  overflow: hidden;
  background:
    radial-gradient(circle at 10% 0%, rgba(83, 188, 255, 0.12), transparent 38%),
    linear-gradient(180deg, #12263a 0%, #102033 100%);
}

.list-head {
  padding: 10px;
  display: grid;
  gap: 8px;
}

.list-head-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.list-head small {
  color: #b8c9db;
}

.list-search {
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  background: #0d1a29;
  color: #e7f0fb;
  padding: 7px 9px;
  font: inherit;
}

.list-search::placeholder {
  color: #91a9c3;
}

.phase-filter {
  padding: 0 10px 10px;
  border-top: 1px solid rgba(227, 237, 248, 0.12);
  border-bottom: 1px solid rgba(227, 237, 248, 0.12);
  background: rgba(8, 18, 31, 0.26);
}

.phase-combobox {
  display: grid;
  gap: 6px;
  padding: 8px 0;
  color: #b8c9db;
}

.phase-combobox span {
  font-size: 0.75rem;
}

.phase-combobox select {
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  background: #102235;
  color: #e7f0fb;
  padding: 7px 9px;
  font: inherit;
}

.list-body {
  overflow: auto;
  padding: 0 8px 10px;
  display: grid;
  gap: 6px;
}

.list-empty {
  border: 1px dashed #90a9c4;
  border-radius: var(--radius);
  color: #c7d9ec;
  padding: 12px;
  text-align: center;
  background: #112235;
}

.pedido-item {
  background: #12253a;
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  color: #d9e7f6;
  text-align: left;
  padding: 8px;
  cursor: pointer;
  display: grid;
  gap: 4px;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.pedido-top strong {
  font-size: 1.05rem;
}

.pedido-item:hover {
  border-color: #c9d8e8;
  background: #152b42;
}

.pedido-item.active {
  border-color: var(--border-strong);
  box-shadow: inset 0 0 0 1px rgba(227, 237, 248, 0.22);
}

.pedido-item p,
.pedido-item small {
  margin: 0;
}

.pedido-item p {
  color: #c8daf0;
  font-size: 0.92rem;
}

.pedido-item small {
  color: #a2bcd6;
  font-size: 0.82rem;
}

.pedido-top,
.pedido-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.priority,
.chip,
.state {
  padding: 2px 7px;
  border-radius: var(--radius);
  border: 1px solid #8aa2bc;
  font-size: 0.76rem;
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

.detail {
  min-height: 0;
  overflow: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  background:
    radial-gradient(circle at 100% 0%, rgba(121, 227, 195, 0.11), transparent 36%),
    linear-gradient(180deg, #102033 0%, #0f1c2b 100%);
}

.tabs-area {
  min-height: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.create-head,
.detail-head,
.cost-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.create-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
}

.urgent-check {
  display: flex;
  align-items: center;
  gap: 8px;
}

.urgent-check input {
  width: 16px;
  height: 16px;
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

textarea {
  resize: vertical;
}

.wide {
  grid-column: 1 / -1;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.account-helper {
  margin: 0;
  color: #98b8d6;
  font-size: 0.76rem;
  border: 1px dashed rgba(227, 237, 248, 0.2);
  border-radius: var(--radius);
  padding: 8px;
  background: rgba(19, 38, 59, 0.55);
}

.detail-kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 5px;
}

.detail-kpis article {
  background: #14293f;
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  padding: 6px;
  display: grid;
  gap: 2px;
}

.detail-kpis span {
  color: #b0c5dc;
  font-size: 0.78rem;
}

.phase-rail {
  --phase-progress: 0%;
  position: relative;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  align-items: center;
  gap: 2px;
  padding: 8px 2px 10px;
  min-height: 62px;
  max-height: 62px;
}

.phase-rail::before,
.phase-rail::after {
  content: '';
  position: absolute;
  left: calc(12.5% + 17px);
  right: calc(12.5% + 17px);
  top: 24px;
  height: 2px;
  border-radius: 999px;
}

.phase-rail::before {
  background: #3b526a;
}

.phase-rail::after {
  right: auto;
  width: calc((75% - 34px) * (var(--phase-progress) / 100));
  background: linear-gradient(90deg, #5bc5ab, #7ad7ef);
  transition: width 0.35s ease;
}

.phase-node {
  position: relative;
  z-index: 1;
  border: 0;
  background: transparent;
  color: #d5e3f2;
  padding: 0 2px;
  display: grid;
  justify-items: center;
  align-content: start;
  gap: 2px;
  cursor: pointer;
}

.phase-circle {
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

.phase-label {
  font-size: 0.68rem;
  line-height: 1;
  letter-spacing: 0.03em;
  color: #dbe8f4;
  white-space: nowrap;
}

.phase-node.done .phase-circle {
  background: #0f2f2b;
  border-color: #5bc5ab;
  color: #bdf8ea;
}

.phase-node.active .phase-circle {
  background: #15314a;
  border-color: var(--border-strong);
  color: #f1f8ff;
  box-shadow: 0 0 0 4px rgba(122, 215, 239, 0.15);
  animation: phasePulse 1.2s ease-in-out infinite;
}

.phase-node.upcoming .phase-circle {
  opacity: 0.85;
}

.phase-next:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
}

.detail-kpis .phase-next {
  align-self: stretch;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 112px;
  width: 100%;
  height: 100%;
}

@keyframes phasePulse {
  0% { box-shadow: 0 0 0 0 rgba(122, 215, 239, 0.25); }
  70% { box-shadow: 0 0 0 7px rgba(122, 215, 239, 0); }
  100% { box-shadow: 0 0 0 0 rgba(122, 215, 239, 0); }
}

.tabs {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  padding: 2px;
  border: 1px solid rgba(227, 237, 248, 0.22);
  border-radius: var(--radius);
  min-height: 32px;
  max-height: 32px;
  align-items: center;
  background: rgba(10, 23, 37, 0.45);
}

.tab {
  border: 1px solid transparent;
  background: transparent;
  color: #b8cee6;
  border-radius: 3px;
  height: 30px;
  min-height: 30px;
  max-height: 30px;
  padding: 0 12px;
  white-space: nowrap;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  font-size: 0.82rem;
}

.tab.active {
  color: #eef6ff;
  background: #1a334c;
  border-color: var(--border-strong);
}

.tab-content {
  height: 100%;
  min-height: 0;
  max-height: none;
  overflow-y: auto;
  overflow-x: hidden;
  background: rgba(8, 18, 31, 0.3);
  border: 1px solid rgba(227, 237, 248, 0.22);
  border-radius: var(--radius);
  padding: 8px;
}

.grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
}

.panel {
  border: 1px solid var(--border-light);
  background: var(--bg-soft);
  border-radius: var(--radius);
  padding: 10px;
  color: #d2e2f2;
  display: grid;
  gap: 8px;
}

.panel ul,
.checks {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 8px;
}

.panel li {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  border-bottom: 1px solid #3a4f67;
  padding-bottom: 7px;
}

.panel li span {
  color: #a9c1da;
}

.timeline ol {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}

.timeline li {
  display: grid;
  gap: 3px;
  padding-left: 10px;
  border-left: 2px solid #9db3cb;
}

.timeline p {
  margin: 0;
}

.checks li {
  border: 0;
  padding: 0;
  justify-content: flex-start;
  color: #c7daee;
}

.asignacion-flow {
  display: grid;
  gap: 9px;
}

.assignment-control {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.assign-trigger {
  min-width: 150px;
}

.assignment-steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
}

.step-pill {
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  background: #112235;
  color: #cde0f3;
  padding: 7px;
  font-size: 0.78rem;
  cursor: pointer;
}

.step-pill:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.step-pill.active {
  border-color: var(--border-strong);
  background: #17324a;
  color: #f2f8ff;
}

.step-pill.done {
  border-color: #79e3c3;
  color: #baf7e5;
}

.assign-form-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.assignment-note {
  margin: 0;
  color: #a6bfd8;
  font-size: 0.8rem;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.tech-card {
  border: 1px solid #49637d;
  border-radius: var(--radius);
  background: #112335;
  color: #dbe8f6;
  padding: 9px;
  display: grid;
  gap: 4px;
  text-align: left;
  cursor: pointer;
}

.tech-card:hover {
  border-color: var(--border-strong);
}

.tech-card.active {
  border-color: #79e3c3;
  box-shadow: inset 0 0 0 1px rgba(121, 227, 195, 0.35);
}

.tech-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tech-head span {
  color: #a9bfd8;
  font-size: 0.74rem;
}

.tech-card p {
  margin: 0;
  font-size: 0.78rem;
}

.score-track {
  height: 8px;
  border-radius: 999px;
  background: #24394f;
  overflow: hidden;
}

.score-track span {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #22c55e, #5bc5ab);
}

.tech-card small {
  color: #b6d2eb;
  font-size: 0.74rem;
}

.epp-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.epp-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  border: 1px solid #465f79;
  border-radius: var(--radius);
  padding: 8px;
  background: #112235;
}

.epp-item input {
  margin-top: 2px;
  width: 14px;
  height: 14px;
}

.epp-item strong {
  font-size: 0.81rem;
}

.epp-item small {
  display: block;
  color: #9fb8d3;
  font-size: 0.74rem;
}

.assignment-summary ul {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 7px;
}

.assignment-summary li {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  border-bottom: 1px solid #3a4f67;
  padding-bottom: 6px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.summary-item {
  border: 1px solid #42566f;
  border-radius: var(--radius);
  background: #112335;
  padding: 8px;
  display: grid;
  gap: 4px;
}

.summary-item span {
  color: #9fb9d3;
  font-size: 0.75rem;
}

.summary-item strong {
  color: #e8f2fd;
  font-size: 0.82rem;
  line-height: 1.25;
}

.summary-item.full {
  grid-column: 1 / -1;
}

.costs-stack {
  display: grid;
  gap: 9px;
}

.cost-kpis {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.mini span {
  color: #b1c7de;
}

.subtotals p {
  margin: 0;
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid #3a4f67;
  padding: 7px 0;
}

.subtotals p:last-child {
  border-bottom: 0;
}

.table-wrap {
  overflow: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 650px;
}

th,
td {
  padding: 7px;
  border-bottom: 1px solid #3a4f67;
  text-align: left;
}

th {
  color: #bdd0e2;
  font-weight: 600;
}

.num {
  text-align: right;
}

.state[data-state='ok'] {
  border-color: #22c55e;
  color: #bbf7d0;
}

.state[data-state='pending'] {
  border-color: #f59e0b;
  color: #fde68a;
}

@media (max-width: 1100px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .list {
    max-height: 320px;
  }

  .phase-rail,
  .grid-two,
  .cost-kpis,
  .detail-kpis,
  .create-form,
  .assign-form-grid,
  .tech-grid,
  .epp-grid,
  .assignment-steps,
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .assignment-control {
    flex-direction: column;
    align-items: stretch;
  }

  .tab-content {
    height: 100%;
    max-height: none;
  }

  .phase-rail {
    gap: 12px;
  }

  .phase-rail::before,
  .phase-rail::after {
    display: none;
  }

  .phase-node {
    gap: 4px;
  }

  .phase-rail {
    min-height: 64px;
    max-height: 64px;
  }

  .phase-circle {
    grid-area: circle;
  }

  .phase-node strong {
    grid-area: title;
  }

}
</style>
