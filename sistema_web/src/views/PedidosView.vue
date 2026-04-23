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
                Cliente registrado
                <select
                  v-model="form.clientName"
                  required
                  :disabled="loadingCreateCatalog || createClientOptions.length === 0"
                  @change="onCreateClientChange"
                >
                  <option disabled value="">
                    {{
                      loadingCreateCatalog
                        ? 'Cargando clientes...'
                        : createClientOptions.length
                          ? 'Selecciona un cliente'
                          : 'No hay clientes registrados'
                    }}
                  </option>
                  <option v-for="client in createClientOptions" :key="client" :value="client">
                    {{ client }}
                  </option>
                </select>
              </label>
              <label>
                Cuenta del cliente
                <select
                  v-model="form.accountCode"
                  required
                  :disabled="loadingCreateCatalog || !form.clientName || createAccountOptions.length === 0"
                  @change="applyAccountByCode"
                >
                  <option disabled value="">
                    {{
                      loadingCreateCatalog
                        ? 'Cargando cuentas...'
                        : createAccountOptions.length
                          ? 'Selecciona una cuenta'
                          : 'No hay cuentas para este cliente'
                    }}
                  </option>
                  <option v-for="acc in createAccountOptions" :key="acc.code" :value="acc.code">
                    {{ acc.code }} - {{ acc.accountName }}
                  </option>
                </select>
              </label>
              <p v-if="createCatalogError" class="wide account-helper">{{ createCatalogError }}</p>
              <p v-if="form.clientName && createAccountOptions.length === 0" class="wide account-helper">
                Este cliente no tiene cuentas disponibles para seleccionar.
              </p>
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

            <p v-if="createError" class="wide sync-empty">{{ createError }}</p>

            <div class="form-actions wide">
              <button type="button" class="btn ghost" @click="creating = false">Cancelar</button>
              <button v-if="createStep === 2" type="button" class="btn ghost" @click="createStep = 1">Atras</button>
              <button v-if="createStep === 1" type="button" class="btn primary" @click="goToStepTwo">Siguiente</button>
              <button v-else type="submit" class="btn primary" :disabled="createSaving">
                {{ createSaving ? 'Guardando...' : 'Guardar pedido' }}
              </button>
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
                :disabled="phaseOptions.length === 0"
                @click="openPhaseModal()"
              >
                Cambiar fase
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
              @click="openPhaseModal(phase.key)"
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
                :class="{ active: activeTab === tab.key, locked: !isTabEnabled(tab.key) }"
                :disabled="!isTabEnabled(tab.key)"
                @click="setActiveTab(tab.key)"
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

              <article class="panel sync-panel">
                <h4>Entradas del tecnico</h4>

                <div class="sync-block">
                  <h5>Actualizaciones</h5>
                  <ul v-if="tecnicoUpdatesForSelected.length" class="sync-updates">
                    <li v-for="update in tecnicoUpdatesForSelected" :key="update.id">
                      <strong>{{ update.createdAt }}</strong>
                      <span>{{ update.note }}</span>
                    </li>
                  </ul>
                  <p v-else class="sync-empty">Sin actualizaciones registradas por tecnico.</p>
                </div>

                <div class="sync-block">
                  <h5>Evidencias</h5>
                  <div v-if="tecnicoEvidenciasForSelected.length" class="sync-evidence-grid">
                    <article v-for="evidencia in tecnicoEvidenciasForSelected" :key="evidencia.id" class="sync-evidence-item">
                      <img :src="evidencia.url" :alt="evidencia.name" />
                      <small>{{ evidencia.createdAt }} - {{ evidencia.stage }} - {{ evidencia.source }}</small>
                      <small v-if="evidencia.description">{{ evidencia.description }}</small>
                    </article>
                  </div>
                  <p v-else class="sync-empty">Sin evidencias cargadas por tecnico.</p>
                </div>

                <div class="sync-block">
                  <h5>Checklist tecnico</h5>
                  <ul v-if="tecnicoChecklistForSelected.length" class="sync-checklist">
                    <li v-for="step in tecnicoChecklistForSelected" :key="step.id" :class="{ done: step.done }">
                      <span>{{ step.label }}</span>
                      <strong>{{ step.done ? (step.doneAt || 'Completado') : 'Pendiente' }}</strong>
                    </li>
                  </ul>
                  <p v-else class="sync-empty">Sin checklist registrado por tecnico.</p>
                </div>

                <div class="sync-block">
                  <h5>Formato de servicio tecnico</h5>
                  <div v-if="tecnicoReportsForSelected.length" class="sync-reports">
                    <article v-for="report in tecnicoReportsForSelected" :key="report.id" class="sync-report-item">
                      <p><strong>Fecha:</strong> {{ report.createdAt }}</p>
                      <p><strong>Responsable local:</strong> {{ report.responsableLocal }}</p>
                      <p><strong>Pedido solicitado:</strong> {{ report.pedidoSolicitado }}</p>
                      <p><strong>Observaciones:</strong> {{ report.observaciones }}</p>
                      <p><strong>Recomendaciones:</strong> {{ report.recomendaciones }}</p>
                      <details>
                        <summary>Ver firma del cliente</summary>
                        <img :src="report.firmaCliente" alt="Firma cliente" class="sync-signature" />
                      </details>
                    </article>
                  </div>
                  <p v-else class="sync-empty">Sin formato de servicio tecnico enviado.</p>
                </div>
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
                  <div class="summary-item"><span>Especialidad</span><strong>{{ selectedAssignedTech?.specialty || 'Sin especialidad' }}</strong></div>
                  <div class="summary-item"><span>Zona base</span><strong>{{ selectedAssignedTech?.zone || 'Sin zona' }}</strong></div>
                  <div class="summary-item">
                    <span>Distancia cuenta-tecnico</span>
                    <strong>{{ selectedAssignedTech?.distanceKm != null ? `${selectedAssignedTech.distanceKm.toFixed(2)} km` : 'Sin distancia' }}</strong>
                  </div>
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
                <p v-if="assignmentCatalogLoading" class="assignment-note">Calculando ranking por distancia...</p>
                <p v-if="assignmentCatalogError" class="sync-empty">{{ assignmentCatalogError }}</p>
                <p v-if="!assignmentCatalogLoading && !rankedTechs.length" class="assignment-note">
                  No hay tecnicos con coordenadas disponibles para este pedido.
                </p>
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
                      <span>{{ tech.distanceKm != null ? `${tech.distanceKm.toFixed(2)} km` : 'Sin distancia' }}</span>
                    </div>
                    <p><strong>Especialidad:</strong> {{ tech.specialty }}</p>
                    <p><strong>Zona base:</strong> {{ tech.zone }}</p>
                    <p><strong>Motivo:</strong> {{ tech.reason }}</p>
                    <div class="score-track">
                      <span :style="{ width: `${tech.score}%` }"></span>
                    </div>
                    <small>Score backend: {{ tech.score }}%</small>
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
              <div v-if="tecnicoReportsForSelected.length" class="sync-reports diagnostico-reports">
                <article v-for="report in tecnicoReportsForSelected" :key="report.id" class="sync-report-item">
                  <p><strong>Fecha:</strong> {{ report.createdAt }}</p>
                  <p><strong>Responsable local:</strong> {{ report.responsableLocal }}</p>
                  <p><strong>Pedido solicitado:</strong> {{ report.pedidoSolicitado }}</p>
                  <p><strong>Observaciones:</strong> {{ report.observaciones }}</p>
                  <p><strong>Recomendaciones:</strong> {{ report.recomendaciones }}</p>
                  <details>
                    <summary>Ver firma del cliente</summary>
                    <img :src="report.firmaCliente" alt="Firma cliente" class="sync-signature" />
                  </details>
                </article>
              </div>
              <p v-else class="sync-empty">Aun no existe informe tecnico enviado para este pedido.</p>

              <textarea
                v-model="selectedPedido.diagnosis"
                rows="7"
                placeholder="Describe causa raiz, evidencia y plan de accion"
              ></textarea>
              <p v-if="diagnosticoError" class="sync-empty">{{ diagnosticoError }}</p>
              <button class="btn primary" :disabled="diagnosticoSaving" @click="saveDiagnostico">
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

    <div v-if="showPhaseModal" class="phase-modal-overlay" @click.self="closePhaseModal">
      <article class="phase-modal card">
        <header class="phase-modal-head">
          <h3>Cambiar fase</h3>
          <p>
            Fase actual: <strong>{{ selectedPedido ? phaseLabel[selectedPedido.phase] : '-' }}</strong>
          </p>
        </header>

        <label>
          Fase de destino
          <select v-model="phaseModalTarget" required>
            <option disabled value="">Selecciona fase</option>
            <option v-for="phase in phaseOptions" :key="phase.key" :value="phase.key">
              {{ phase.label }}
            </option>
          </select>
        </label>

        <label>
          Sustento (obligatorio)
          <textarea
            v-model.trim="phaseModalSustento"
            rows="4"
            required
            placeholder="Explica por que se realiza el cambio de fase"
          ></textarea>
        </label>

        <div class="phase-modal-actions">
          <button type="button" class="btn ghost" @click="closePhaseModal">Cancelar</button>
          <button
            type="button"
            class="btn primary"
            :disabled="!phaseModalTarget || !phaseModalSustento.trim()"
            @click="confirmPhaseChange"
          >
            Confirmar cambio
          </button>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue';
import {
  type ApiCliente,
  type ApiCuenta,
  type ApiRecomendacionTecnicoItem,
  type ApiTecnico,
  createCliente,
  createCuenta,
  createPedido as createPedidoApi,
  listClientes,
  listCuentas,
  listTecnicos,
  recomendarTecnico,
  updateCuenta,
} from '../api';
import { usePedidosStore } from '../stores/pedidosStore';

type PhaseKey = 'deteccion' | 'asignacion' | 'cierre' | 'facturacion';
type TabKey =
  | 'detalles'
  | 'historial'
  | 'asignacion'
  | 'diagnostico'
  | 'costos';

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

interface RankedTechProfile {
  id: string;
  fullName: string;
  specialty: string;
  zone: string;
  distanceKm: number | null;
  score: number;
  reason: string;
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

const phaseLabel: Record<PhaseKey, string> = {
  deteccion: 'Deteccion',
  asignacion: 'Asignacion',
  cierre: 'Cierre',
  facturacion: 'Facturacion',
};

const phaseOrder: PhaseKey[] = [
  'deteccion',
  'asignacion',
  'cierre',
  'facturacion',
];

const workflowPhases = [
  { key: 'deteccion' as const, order: '01', label: 'Deteccion' },
  { key: 'asignacion' as const, order: '02', label: 'Asignacion' },
  { key: 'cierre' as const, order: '03', label: 'Cierre' },
  { key: 'facturacion' as const, order: '04', label: 'Facturacion' },
];

const phaseFilters = [
  { key: 'all', label: 'Todos' },
  ...workflowPhases.map((p) => ({ key: p.key, label: p.label })),
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

const eppCatalog: EppItem[] = [
  {
    id: 'epp-1',
    name: 'Casco dielctrico',
    stock: 34,
    category: 'Proteccion cabeza',
  },
  {
    id: 'epp-2',
    name: 'Guantes dielctricos',
    stock: 52,
    category: 'Proteccion manos',
  },
  {
    id: 'epp-3',
    name: 'Lentes de seguridad',
    stock: 41,
    category: 'Proteccion visual',
  },
  {
    id: 'epp-4',
    name: 'Arnes de seguridad',
    stock: 19,
    category: 'Trabajo en altura',
  },
  {
    id: 'epp-5',
    name: 'Botas punta de acero',
    stock: 27,
    category: 'Proteccion pies',
  },
];

const pedidos = ref<PedidoItem[]>([]);

const tecnicoBridge = usePedidosStore();
const allPedidos = computed(() =>
  tecnicoBridge.mergeWithCoordinatorPedidos(pedidos.value),
);

watch(
  pedidos,
  (next) => {
    tecnicoBridge.setCoordinatorSnapshot(next);
  },
  { deep: true, immediate: true },
);

const selectedId = ref<string>(allPedidos.value[0]?.id || '');
const activeTab = ref<TabKey>('detalles');
const creating = ref(false);
const createStep = ref<1 | 2>(1);
const phaseFilter = ref<'all' | PhaseKey>('all');
const searchQuery = ref('');
const showPhaseModal = ref(false);
const phaseModalTarget = ref<PhaseKey | ''>('');
const phaseModalSustento = ref('');
const diagnosticoSaving = ref(false);
const diagnosticoError = ref('');
const createSaving = ref(false);
const createError = ref('');
const loadingCreateCatalog = ref(false);
const createCatalogError = ref('');
const createClientesCatalog = ref<ApiCliente[]>([]);
const createCuentasCatalog = ref<ApiCuenta[]>([]);
const assignmentCatalogLoading = ref(false);
const assignmentCatalogError = ref('');
const assignmentTecnicosCatalog = ref<ApiTecnico[]>([]);
const assignmentRankingByPedido = reactive<
  Record<string, ApiRecomendacionTecnicoItem[]>
>({});

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

const selectedClient = computed(() => {
  const selectedName = form.clientName.trim().toLowerCase();
  if (!selectedName) return null;
  return (
    createClientesCatalog.value.find(
      (cliente) => cliente.nombre.trim().toLowerCase() === selectedName,
    ) || null
  );
});

const selectedAccount = computed(() => {
  const code = form.accountCode.trim().toUpperCase();
  const selectedClientId = selectedClient.value?.id;
  if (!code || !selectedClientId) return null;
  return (
    createCuentasCatalog.value.find(
      (cuenta) =>
        cuenta.cliente === selectedClientId &&
        cuenta.numero.trim().toUpperCase() === code,
    ) || null
  );
});

const createClientOptions = computed(() => {
  const clients = new Set(
    createClientesCatalog.value.map((cliente) => cliente.nombre),
  );
  return Array.from(clients).sort((a, b) => a.localeCompare(b, 'es'));
});

const createAccountOptions = computed(() => {
  const selectedClientId = selectedClient.value?.id;
  if (!selectedClientId) return [];

  return createCuentasCatalog.value
    .filter((cuenta) => cuenta.cliente === selectedClientId)
    .map((cuenta) => ({
      code: cuenta.numero.trim().toUpperCase(),
      accountName: cuenta.nombre,
    }));
});

const linkedAccounts = computed(() => {
  if (!selectedAccount.value) return [];
  return createAccountOptions.value
    .filter(
      (acc) => acc.code !== selectedAccount.value?.numero.trim().toUpperCase(),
    )
    .map((acc) => `${acc.code} (${acc.accountName})`);
});

const filteredPedidos = computed(() => {
  const query = searchQuery.value.trim().toLowerCase();
  return allPedidos.value.filter((p) => {
    const byPhase =
      phaseFilter.value === 'all' || p.phase === phaseFilter.value;
    if (!byPhase) return false;
    if (!query) return true;
    return (
      p.code.toLowerCase().includes(query) ||
      p.client.toLowerCase().includes(query) ||
      p.service.toLowerCase().includes(query)
    );
  });
});

watch(
  allPedidos,
  (next) => {
    if (!next.length) {
      selectedId.value = '';
      return;
    }

    const exists = next.some((pedido) => pedido.id === selectedId.value);
    if (!exists) selectedId.value = next[0].id;
  },
  { immediate: true },
);

const selectedPedido = computed(() =>
  allPedidos.value.find((p) => p.id === selectedId.value),
);
const tecnicoUpdatesForSelected = computed(() => {
  if (!selectedPedido.value) return [];
  return tecnicoBridge.getUpdates(selectedPedido.value.id);
});
const tecnicoEvidenciasForSelected = computed(() => {
  if (!selectedPedido.value) return [];
  return tecnicoBridge.getEvidencias(selectedPedido.value.id);
});
const tecnicoChecklistForSelected = computed(() => {
  if (!selectedPedido.value) return [];
  return tecnicoBridge.getChecklist(selectedPedido.value.id);
});
const tecnicoReportsForSelected = computed(() => {
  if (!selectedPedido.value) return [];
  return tecnicoBridge.getServiceReports(selectedPedido.value.id);
});
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
  if (
    !draft.contactName.trim() ||
    !draft.availableDate ||
    !draft.startTime ||
    !draft.endTime
  )
    return false;
  if (!draft.additionalDetails.trim() || !draft.thirdPartyCompany.trim())
    return false;
  if (Number(draft.mobilityPrice) < 0 || Number(draft.thirdPartyPrice) < 0)
    return false;
  return draft.endTime > draft.startTime;
});

const rankedTechs = computed(() => {
  if (!selectedPedido.value) return [];

  const ranking = assignmentRankingByPedido[selectedPedido.value.id] || [];
  if (!ranking.length) return [];

  return ranking.map((item): RankedTechProfile => {
    const tecnico = assignmentTecnicosCatalog.value.find(
      (entry) => entry.id === item.id,
    );
    const reason = item.motivos?.length
      ? item.motivos.join(', ')
      : 'Sin motivo';
    return {
      id: item.id,
      fullName: tecnico?.nombre || item.nombre,
      specialty: tecnico?.especialidad || 'Sin especialidad',
      zone: tecnico?.zona || 'Sin zona',
      distanceKm: item.distancia_km,
      score: item.score,
      reason,
    };
  });
});

const selectedAssignedTech = computed(() => {
  if (!selectedAssignment.value?.selectedTechId) return null;
  return (
    rankedTechs.value.find(
      (tech) => tech.id === selectedAssignment.value?.selectedTechId,
    ) || null
  );
});

const selectedEppNames = computed(() => {
  const selected = selectedAssignment.value?.selectedEpps || [];
  return eppCatalog
    .filter((item) => selected.includes(item.id))
    .map((item) => item.name);
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

const phaseRank: Record<PhaseKey, number> = {
  deteccion: 0,
  asignacion: 1,
  cierre: 2,
  facturacion: 3,
};

const phaseOptions = computed(() => {
  if (!selectedPedido.value) return [];
  return workflowPhases.filter(
    (phase) => phase.key !== selectedPedido.value?.phase,
  );
});

function isTabEnabled(tab: TabKey) {
  if (!selectedPedido.value) return false;
  const currentRank = phaseRank[selectedPedido.value.phase];

  if (tab === 'detalles' || tab === 'historial') return true;
  if (tab === 'asignacion') return currentRank >= phaseRank.asignacion;
  if (tab === 'diagnostico') return currentRank >= phaseRank.cierre;
  if (tab === 'costos') return currentRank >= phaseRank.facturacion;
  return false;
}

function ensureValidTab() {
  if (!isTabEnabled(activeTab.value)) {
    activeTab.value = 'detalles';
  }
}

function setActiveTab(tab: TabKey) {
  if (!isTabEnabled(tab)) return;
  activeTab.value = tab;
}

function countByPhase(key: 'all' | PhaseKey) {
  if (key === 'all') return allPedidos.value.length;
  return allPedidos.value.filter((p) => p.phase === key).length;
}

function selectPedido(id: string) {
  selectedId.value = id;
  creating.value = false;
  closePhaseModal();
  ensureValidTab();
}

function openPhaseModal(preferredPhase?: PhaseKey) {
  if (!selectedPedido.value) return;

  const canUsePreferred =
    preferredPhase && preferredPhase !== selectedPedido.value.phase;
  phaseModalTarget.value = canUsePreferred
    ? preferredPhase
    : phaseOptions.value[0]?.key || '';
  phaseModalSustento.value = '';
  showPhaseModal.value = true;
}

function closePhaseModal() {
  showPhaseModal.value = false;
  phaseModalTarget.value = '';
  phaseModalSustento.value = '';
}

function confirmPhaseChange() {
  if (
    !selectedPedido.value ||
    !phaseModalTarget.value ||
    !phaseModalSustento.value.trim()
  )
    return;

  applyPhaseChange(phaseModalTarget.value, phaseModalSustento.value.trim());
  closePhaseModal();
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
    selectedAssignment.value.contactName =
      selectedPedido.value.contactName || '';
  }
  selectedAssignment.value.processOpen = true;
  selectedAssignment.value.step = 1;
  void loadAssignmentCatalogAndRanking(selectedPedido.value.id);
}

async function loadAssignmentCatalogAndRanking(pedidoId: string) {
  assignmentCatalogLoading.value = true;
  assignmentCatalogError.value = '';

  try {
    if (!assignmentTecnicosCatalog.value.length) {
      const tecnicos = await listTecnicos({ activo: true });
      assignmentTecnicosCatalog.value = tecnicos;
    }

    const recommendation = await recomendarTecnico(pedidoId);
    assignmentRankingByPedido[pedidoId] = recommendation.ranking || [];
  } catch (error) {
    assignmentRankingByPedido[pedidoId] = [];
    assignmentCatalogError.value =
      error instanceof Error
        ? error.message
        : 'No se pudo cargar el ranking de tecnicos desde backend.';
  } finally {
    assignmentCatalogLoading.value = false;
  }
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
  selectedAssignment.value.selectedEpps =
    selectedAssignment.value.selectedEpps.filter((id) => id !== itemId);
}

function registerVisit() {
  if (
    !selectedAssignment.value ||
    !selectedPedido.value ||
    !canRegisterVisit.value
  )
    return;

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
    `Visita registrada con ${tech.fullName}. EPPs: ${selectedEppNames.value.join(', ') || 'sin EPPs'}`,
  );
}

function applyAccountByCode() {
  const account = selectedAccount.value;
  const client = selectedClient.value;

  if (!account || !client) {
    clearCreateAccountFields();
    return;
  }

  form.accountCode = account.numero.trim().toUpperCase();
  form.clientName = client.nombre;
  form.contactName =
    account.contacto.trim() || form.contactName.trim() || client.nombre;
  form.referenceAddress = account.direccion.trim() || client.direccion.trim();
  form.district = account.distrito.trim();
  form.coordinates = `${account.latitud}, ${account.longitud}`;
  form.documentNumber = client.documento.trim();
  form.contactPhone = account.telefono.trim() || client.telefono.trim();
  form.contactEmail = client.correo.trim();
  if (!form.service.trim())
    form.service = account.nombre.trim() || commonServices[0];
}

function clearCreateAccountFields() {
  form.contactName = '';
  form.referenceAddress = '';
  form.district = '';
  form.coordinates = '';
  form.documentNumber = '';
  form.contactPhone = '';
  form.contactEmail = '';
}

function onCreateClientChange() {
  form.accountCode = '';
  const client = selectedClient.value;
  if (!client) {
    clearCreateAccountFields();
    return;
  }

  form.contactName = client.nombre;
  form.referenceAddress = client.direccion.trim();
  form.documentNumber = client.documento.trim();
  form.contactPhone = client.telefono.trim();
  form.contactEmail = client.correo.trim();
}

function parseCoordinateInput(raw: string) {
  const [latRaw, lonRaw] = raw.split(',').map((part) => part.trim());
  const lat = Number(latRaw);
  const lon = Number(lonRaw);

  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
  if (lat < -90 || lat > 90) return null;
  if (lon < -180 || lon > 180) return null;
  return { lat, lon };
}

async function loadCreateCatalog() {
  loadingCreateCatalog.value = true;
  createCatalogError.value = '';

  try {
    const [clientes, cuentas] = await Promise.all([
      listClientes(),
      listCuentas(),
    ]);
    createClientesCatalog.value = clientes.filter((cliente) => cliente.activo);
    createCuentasCatalog.value = cuentas.filter((cuenta) => cuenta.activa);
  } catch (error) {
    createClientesCatalog.value = [];
    createCuentasCatalog.value = [];
    createCatalogError.value =
      error instanceof Error
        ? error.message
        : 'No se pudo cargar clientes y cuentas desde backend.';
  } finally {
    loadingCreateCatalog.value = false;
  }
}

function goToStepTwo() {
  const stepOneValid =
    form.accountCode.trim() &&
    form.clientName.trim() &&
    form.contactName.trim() &&
    form.referenceAddress.trim() &&
    form.district.trim() &&
    form.coordinates.trim() &&
    form.documentNumber.trim() &&
    form.contactPhone.trim() &&
    form.contactEmail.trim();
  if (!stepOneValid) return;

  const parsed = parseCoordinateInput(form.coordinates);
  if (!parsed) {
    createError.value =
      'Las coordenadas deben tener formato "latitud, longitud" con valores validos.';
    return;
  }

  createError.value = '';
  createStep.value = 2;
}

function applyPhaseChange(phase: PhaseKey, sustento: string) {
  if (!selectedPedido.value) return;
  const prevPhase = selectedPedido.value.phase;

  if (prevPhase === phase) return;

  selectedPedido.value.phase = phase;
  if (phase === 'facturacion') selectedPedido.value.status = 'Por facturar';
  if (phase === 'cierre') selectedPedido.value.status = 'En cierre';
  if (phase === 'asignacion') selectedPedido.value.status = 'En proceso';
  if (phase === 'deteccion') selectedPedido.value.status = 'Pendiente';
  pushHistory(
    `Cambio de fase: ${phaseLabel[prevPhase]} -> ${phaseLabel[phase]}. Sustento: ${sustento}`,
  );
  ensureValidTab();
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

async function saveDiagnostico() {
  if (!selectedPedido.value || !selectedPedido.value.diagnosis.trim()) return;

  diagnosticoSaving.value = true;
  diagnosticoError.value = '';

  try {
    await tecnicoBridge.updateDiagnostico(
      selectedPedido.value.id,
      selectedPedido.value.diagnosis.trim(),
    );
    pushHistory('Diagnostico actualizado');
  } catch (error) {
    diagnosticoError.value =
      error instanceof Error
        ? error.message
        : 'No se pudo guardar el diagnostico.';
  } finally {
    diagnosticoSaving.value = false;
  }
}

async function openCreate() {
  resetCreateForm();
  createError.value = '';
  createCatalogError.value = '';
  creating.value = true;
  createStep.value = 1;
  activeTab.value = 'detalles';
  await loadCreateCatalog();
}

function resetCreateForm() {
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

async function ensureClienteForForm() {
  const nombre = form.clientName.trim();
  const documento = form.documentNumber.trim();
  const telefono = form.contactPhone.trim();
  const correo = form.contactEmail.trim();
  const direccion = form.referenceAddress.trim();

  const found = await listClientes({ search: nombre });
  const existing = found.find((cliente) => {
    const sameName =
      cliente.nombre.trim().toLowerCase() === nombre.toLowerCase();
    const sameDocumento = !documento || cliente.documento.trim() === documento;
    return sameName && sameDocumento;
  });

  if (existing) return existing;

  return createCliente({
    nombre,
    documento,
    telefono,
    correo,
    direccion,
  });
}

async function ensureCuentaForCliente(clienteId: string) {
  const numero = form.accountCode.trim().toUpperCase();
  const search = numero || form.clientName.trim();
  const found = await listCuentas({ cliente: clienteId, search });
  const existing = found.find(
    (cuenta) => cuenta.numero.trim().toUpperCase() === numero,
  );

  const parsed = parseCoordinateInput(form.coordinates);
  if (!parsed) {
    throw new Error('No se pudieron interpretar las coordenadas de la cuenta.');
  }

  const cuentaPayload = {
    direccion: form.referenceAddress.trim(),
    distrito: form.district.trim(),
    contacto: form.contactName.trim(),
    telefono: form.contactPhone.trim(),
    latitud: parsed.lat,
    longitud: parsed.lon,
    activa: true,
  };

  if (existing) {
    return updateCuenta(existing.id, cuentaPayload);
  }

  return createCuenta({
    cliente: clienteId,
    nombre: numero,
    numero,
    ...cuentaPayload,
    tipo: 'empresa',
  });
}

async function createPedido() {
  if (!form.service.trim()) return;

  createSaving.value = true;
  createError.value = '';

  try {
    const cliente = await ensureClienteForForm();
    const cuenta = await ensureCuentaForCliente(cliente.id);
    const service = form.service.trim();
    const problem = form.problemDescription.trim();

    const created = await createPedidoApi({
      cliente: cliente.id,
      cuenta: cuenta.id,
      titulo: `${service} - ${cliente.nombre}`,
      descripcion:
        problem ||
        `Contacto: ${form.contactName.trim()} (${form.contactPhone.trim()})`,
      tipo_servicio: service,
      zona: form.district.trim() || 'Sin zona',
      prioridad: form.urgent ? 'critica' : 'media',
      diagnostico_tecnico: problem,
    });

    await tecnicoBridge.hydrateFromApi(true);
    selectedId.value = String(created.id);
    creating.value = false;
    createStep.value = 1;
    activeTab.value = 'detalles';
    resetCreateForm();
  } catch (error) {
    createError.value =
      error instanceof Error
        ? error.message
        : 'No se pudo crear el pedido. Verifica tus datos e intenta nuevamente.';
  } finally {
    createSaving.value = false;
  }
}

function recalculateCosts() {
  if (!selectedPedido.value) return;
  selectedPedido.value.costs.absorbed = Math.round(
    selectedPedido.value.costs.direct * 0.16,
  );
  selectedPedido.value.costs.total =
    selectedPedido.value.costs.direct + selectedPedido.value.costs.absorbed;
  selectedPedido.value.costs.margin = Math.max(
    8,
    Math.min(34, selectedPedido.value.costs.margin + 1),
  );
  pushHistory('Snapshot de costos recalculado');
}

onMounted(async () => {
  try {
    await Promise.all([tecnicoBridge.hydrateFromApi(), loadCreateCatalog()]);
  } catch {
    // The technical views surface synchronization issues in their own panels.
  }
});
</script>

<style scoped>
.pedidos-view {
  --bg-card: var(--color-surface);
  --bg-soft: var(--color-surface-2);
  --bg-soft-2: var(--color-surface-alt);
  --text-main: var(--color-text);
  --text-muted: var(--color-text-muted);
  --border-light: var(--color-border);
  --border-strong: var(--color-primary-500);
  --scroll-track: var(--color-bg-soft);
  --scroll-thumb: var(--color-primary-200);
  --scroll-thumb-hover: var(--color-primary-400);
  --radius: 4px;

  display: grid;
  grid-template-rows: 48px minmax(0, 1fr);
  gap: 0;
  height: calc(100dvh - 24px);
  max-height: calc(100dvh - 24px);
}

.card {
  background: linear-gradient(180deg, var(--color-surface-2) 0%, var(--color-surface) 100%);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
}

.pedidos-view :where(.list-body, .detail, .tab-content, .table-wrap) {
  scrollbar-width: thin;
  scrollbar-color: var(--scroll-thumb) var(--scroll-track);
}

.pedidos-view :where(.list-body, .detail, .tab-content, .table-wrap)::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.pedidos-view :where(.list-body, .detail, .tab-content, .table-wrap)::-webkit-scrollbar-track {
  background: linear-gradient(180deg, var(--color-bg-soft), var(--color-bg-soft));
  border-radius: 999px;
}

.pedidos-view :where(.list-body, .detail, .tab-content, .table-wrap)::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--color-border-strong), var(--color-border));
  border: 2px solid var(--color-bg-soft);
  border-radius: 999px;
}

.pedidos-view :where(.list-body, .detail, .tab-content, .table-wrap)::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, var(--color-text-muted), var(--color-border-strong));
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
    var(--color-surface);
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
  color: var(--color-text-soft);
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
    linear-gradient(180deg, var(--color-surface-2) 0%, var(--color-surface) 100%);
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
  color: var(--color-text-muted);
}

.list-search {
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  background: var(--color-surface);
  color: var(--color-text);
  padding: 7px 9px;
  font: inherit;
}

.list-search::placeholder {
  color: var(--color-text-muted);
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
  color: var(--color-text-muted);
}

.phase-combobox span {
  font-size: 0.75rem;
}

.phase-combobox select {
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  background: var(--color-surface);
  color: var(--color-text);
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
  border: 1px dashed var(--color-text-muted);
  border-radius: var(--radius);
  color: var(--color-text-muted);
  padding: 12px;
  text-align: center;
  background: var(--color-surface-2);
}

.pedido-item {
  background: var(--color-surface-2);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  color: var(--color-text-soft);
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
  border-color: var(--color-text-muted);
  background: var(--color-surface-alt);
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
  color: var(--color-text-muted);
  font-size: 0.92rem;
}

.pedido-item small {
  color: var(--color-text-muted);
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
  border: 1px solid var(--color-text-muted);
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
  border-color: var(--color-info);
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
    linear-gradient(180deg, var(--color-surface) 0%, var(--color-surface) 100%);
}

.tabs-area {
  min-height: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow: hidden;
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
  color: var(--color-text-muted);
  font-size: 0.84rem;
}

input,
textarea,
select {
  background: var(--color-bg-soft);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  color: var(--color-text);
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
  background: var(--color-surface-alt);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  padding: 6px;
  display: grid;
  gap: 2px;
}

.detail-kpis span {
  color: var(--color-text-muted);
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
  background: var(--color-border);
}

.phase-rail::after {
  right: auto;
  width: calc((75% - 34px) * (var(--phase-progress) / 100));
  background: linear-gradient(90deg, #5bc5ab, var(--color-primary-300));
  transition: width 0.35s ease;
}

.phase-node {
  position: relative;
  z-index: 1;
  border: 0;
  background: transparent;
  color: var(--color-text-soft);
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
  border: 1px solid var(--color-text-muted);
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  font-size: 0.9rem;
  font-weight: 700;
  transition: all 0.25s ease;
}

.phase-label {
  font-size: 0.68rem;
  line-height: 1;
  letter-spacing: 0.03em;
  color: var(--color-text-soft);
  white-space: nowrap;
}

.phase-node.done .phase-circle {
  background: #0f2f2b;
  border-color: #5bc5ab;
  color: #bdf8ea;
}

.phase-node.active .phase-circle {
  background: var(--color-surface-alt);
  border-color: var(--border-strong);
  color: var(--color-text);
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
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 4px;
  overflow: hidden;
  padding: 2px;
  border: 1px solid rgba(227, 237, 248, 0.22);
  border-radius: var(--radius);
  min-height: 38px;
  max-height: none;
  align-items: stretch;
  background: rgba(10, 23, 37, 0.45);
}

.tab {
  border: 1px solid transparent;
  background: transparent;
  color: var(--color-text-muted);
  border-radius: 3px;
  min-height: 32px;
  padding: 4px 10px;
  white-space: normal;
  text-align: center;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.82rem;
  line-height: 1.1;
}

.tab.active {
  color: var(--color-text);
  background: var(--color-surface-alt);
  border-color: var(--border-strong);
}

.tab.locked,
.tab:disabled {
  opacity: 0.48;
  cursor: not-allowed;
}

.phase-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(2, 10, 18, 0.62);
  display: grid;
  place-items: center;
  padding: 16px;
  z-index: 120;
}

.phase-modal {
  width: min(540px, 100%);
  padding: 12px;
  display: grid;
  gap: 10px;
}

.phase-modal-head {
  display: grid;
  gap: 3px;
}

.phase-modal-head p {
  margin: 0;
}

.phase-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.tab-content {
  height: 100%;
  min-height: 0;
  max-height: none;
  overflow: visible;
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

.sync-panel {
  grid-column: 1 / -1;
}

.sync-block {
  display: grid;
  gap: 6px;
}

.sync-block h5 {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 0.82rem;
}

.sync-empty {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 0.8rem;
}

.sync-updates {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 7px;
}

.sync-updates li {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface-2);
  padding: 7px;
  display: grid;
  gap: 3px;
}

.sync-evidence-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
}

.sync-evidence-item {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 6px;
  background: var(--color-surface);
  display: grid;
  gap: 5px;
}

.sync-evidence-item img {
  width: 100%;
  height: 110px;
  object-fit: cover;
  border-radius: 3px;
}

.sync-evidence-item small {
  color: var(--color-text-muted);
}

.sync-checklist {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 6px;
}

.sync-checklist li {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface-2);
  padding: 7px;
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.sync-checklist li.done {
  border-color: #2f8f65;
}

.sync-reports {
  display: grid;
  gap: 8px;
}

.sync-report-item {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface-2);
  padding: 8px;
  display: grid;
  gap: 4px;
}

.sync-report-item p {
  margin: 0;
}

.sync-signature {
  width: min(360px, 100%);
  border: 1px solid var(--color-border-strong);
  border-radius: 4px;
  background: var(--color-bg-soft);
}

.panel {
  border: 1px solid var(--border-light);
  background: var(--bg-soft);
  border-radius: var(--radius);
  padding: 10px;
  color: var(--color-text-soft);
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
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 7px;
}

.panel li span {
  color: var(--color-text-muted);
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
  border-left: 2px solid var(--color-text-muted);
}

.timeline p {
  margin: 0;
}

.checks li {
  border: 0;
  padding: 0;
  justify-content: flex-start;
  color: var(--color-text-muted);
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
  background: var(--color-surface-2);
  color: var(--color-text-muted);
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
  background: var(--color-surface-alt);
  color: var(--color-text);
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
  color: var(--color-text-muted);
  font-size: 0.8rem;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.tech-card {
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius);
  background: var(--color-surface-2);
  color: var(--color-text-soft);
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
  color: var(--color-text-muted);
  font-size: 0.74rem;
}

.tech-card p {
  margin: 0;
  font-size: 0.78rem;
}

.score-track {
  height: 8px;
  border-radius: 999px;
  background: var(--color-border);
  overflow: hidden;
}

.score-track span {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #22c55e, #5bc5ab);
}

.tech-card small {
  color: var(--color-text-muted);
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
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 8px;
  background: var(--color-surface-2);
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
  color: var(--color-text-muted);
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
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 6px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.summary-item {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface-2);
  padding: 8px;
  display: grid;
  gap: 4px;
}

.summary-item span {
  color: var(--color-text-muted);
  font-size: 0.75rem;
}

.summary-item strong {
  color: var(--color-text);
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
  color: var(--color-text-muted);
}

.subtotals p {
  margin: 0;
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid var(--color-border);
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
  border-bottom: 1px solid var(--color-border);
  text-align: left;
}

th {
  color: var(--color-text-muted);
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

  .tabs {
    grid-template-columns: repeat(3, minmax(0, 1fr));
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

@media (max-width: 680px) {
  .tabs {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
