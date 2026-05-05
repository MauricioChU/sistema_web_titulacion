<template>
  <div class="pv" :class="theme">

    <!-- ═══════════════════════════════ SIDEBAR ═══════════════════════════════ -->
    <aside class="pv-sidebar">
      <div class="sidebar-head">
        <div class="sidebar-title">
          <span class="sidebar-icon"><LayoutGrid :size="16" /></span>
          <h2>PEDIDOS</h2>
        </div>
        <div class="sidebar-controls">
          <button class="icon-btn" :title="theme === 'dark' ? 'Tema claro' : 'Tema oscuro'" @click="toggleTheme">
            <Sun v-if="theme === 'dark'" :size="14" /><Moon v-else :size="14" />
          </button>
          <button class="btn-create" @click="openCreate"><Plus :size="13" style="vertical-align:middle" /> NUEVO</button>
        </div>
      </div>

      <div class="sidebar-filters">
        <input v-model="search" type="search" placeholder="Buscar OT, cliente..." class="filter-input" />
        <div class="filter-row">
          <select v-model="filterFase" class="filter-select">
            <option value="">Todas las fases</option>
            <option value="creacion">Creación</option>
            <option value="programacion">Programación</option>
            <option value="seguimiento">Seguimiento</option>
            <option value="cierre">Cierre</option>
          </select>
          <select v-model="filterEstado" class="filter-select">
            <option value="">Todos los estados</option>
            <option value="por-confirmar">Por confirmar</option>
            <option value="confirmado">Confirmado</option>
            <option value="rechazado">Rechazado</option>
            <option value="en-labor">En labor</option>
            <option value="cierre-tecnico">Cierre técnico</option>
            <option value="completado">Completado</option>
            <option value="dado-de-baja">Dado de baja</option>
          </select>
        </div>
        <div class="filter-stats">
          <span>{{ filteredPedidos.length }} pedido{{ filteredPedidos.length !== 1 ? 's' : '' }}</span>
          <span v-if="rechazadosCount > 0" class="stat-alert">{{ rechazadosCount }} rechazado{{ rechazadosCount !== 1 ? 's' : '' }}</span>
        </div>
      </div>

      <div class="sidebar-list">
        <div v-if="loading" class="list-empty">Cargando pedidos...</div>
        <div v-else-if="filteredPedidos.length === 0" class="list-empty">Sin resultados</div>
        <button
          v-for="p in filteredPedidos"
          :key="p.id"
          class="list-item"
          :class="{ active: selectedId === p.id, alerta: p.estado === 'rechazado' }"
          @click="selectPedido(p.id)"
        >
          <div class="item-header">
            <span class="item-ot">{{ p.codigo }}</span>
            <span class="item-pri" :class="`pri-${p.prioridad}`">{{ p.prioridad.toUpperCase() }}</span>
          </div>
          <div class="item-cliente">{{ p.cliente_nombre }}</div>
          <div class="item-titulo">{{ p.titulo }}</div>
          <div class="item-footer">
            <span class="item-estado" :class="`est-${p.estado}`">{{ ESTADO_LABEL[p.estado] }}</span>
            <span class="item-fase">{{ FASE_LABEL[p.fase] }}</span>
          </div>
          <div v-if="p.estado === 'rechazado'" class="item-rechazo-flag">
            <AlertTriangle :size="11" style="vertical-align:middle" /> REQUIERE REASIGNACIÓN
          </div>
        </button>
      </div>
    </aside>

    <!-- ═══════════════════════════════ DETALLE ═══════════════════════════════ -->
    <main class="pv-main">

      <!-- Sin selección -->
      <div v-if="!selected && !loading" class="main-empty">
        <div class="empty-glyph"><LayoutGrid :size="40" /></div>
        <p>Selecciona un pedido de la lista</p>
      </div>

      <!-- Detalle del pedido -->
      <template v-else-if="selected">

        <!-- Encabezado fijo -->
        <div class="detail-topbar">
          <div class="topbar-left">
            <span class="topbar-ot">{{ selected.codigo }}</span>
            <span class="topbar-sep">|</span>
            <span class="topbar-titulo">{{ selected.titulo }}</span>
          </div>
          <div class="topbar-right">
            <span class="badge-pri" :class="`pri-${selected.prioridad}`">{{ selected.prioridad.toUpperCase() }}</span>
            <span class="badge-estado" :class="`est-${selected.estado}`">{{ ESTADO_LABEL[selected.estado] }}</span>
            <span class="topbar-cost" title="Costo total del pedido">
              S/ {{ fmt(selected.costo_total) }}
            </span>
            <a :href="pdfUrl" target="_blank" rel="noopener" class="icon-btn" title="Descargar PDF">
              <Download :size="13" /> PDF
            </a>
          </div>
        </div>

        <!-- Botón de acción principal (CTA de cambio de fase) — primero, bien visible -->
        <div v-if="mainCTA" class="main-cta" :class="`cta-${mainCTA.type}`">
          <div class="cta-info">
            <span class="cta-label">ACCIÓN REQUERIDA</span>
            <span class="cta-desc">{{ mainCTA.desc }}</span>
          </div>
          <button class="cta-btn" :disabled="actionLoading" @click="mainCTA.action">
            {{ actionLoading ? 'Procesando...' : mainCTA.label }}
          </button>
        </div>

        <!-- Rail de fases -->
        <div class="phase-rail">
          <div
            v-for="(fase, idx) in FASES"
            :key="fase.key"
            class="phase-step"
            :class="phaseStepClass(fase.key)"
          >
            <div class="phase-num">{{ idx + 1 }}</div>
            <div class="phase-label">{{ fase.label.toUpperCase() }}</div>
            <div v-if="idx < FASES.length - 1" class="phase-connector"></div>
          </div>
        </div>

        <!-- Tabs -->
        <div class="tabs-bar">
          <button
            v-for="t in TABS"
            :key="t.key"
            class="tab"
            :class="{ active: activeTab === t.key }"
            @click="activeTab = t.key"
          >{{ t.label }}</button>
        </div>

        <!-- ── Tab: Información ── -->
        <div v-if="activeTab === 'info'" class="tab-panel">
          <div class="info-cols">

            <!-- DATOS DEL PEDIDO -->
            <section class="info-card">
              <h3 class="info-card-title">DATOS DEL PEDIDO</h3>
              <dl class="info-dl">
                <dt>Fase actual</dt>
                <dd><span class="phase-badge">{{ FASE_LABEL[selected.fase] }}</span></dd>

                <dt>Código OT</dt>
                <dd><span class="code-text">{{ selected.codigo }}</span></dd>

                <dt>Tipo de servicio</dt>
                <dd>{{ selected.tipo_servicio }}</dd>

                <dt>Prioridad</dt>
                <dd><span class="badge-pri" :class="`pri-${selected.prioridad}`">{{ selected.prioridad.toUpperCase() }}</span></dd>

                <dt>Inicio de labor</dt>
                <dd>{{ selected.fecha_inicio_labor ? fmtDt(selected.fecha_inicio_labor) : '—' }}</dd>

                <dt>Fin de labor</dt>
                <dd>{{ selected.fecha_fin_labor ? fmtDt(selected.fecha_fin_labor) : '—' }}</dd>

                <dt>Cierre</dt>
                <dd>{{ selected.fecha_cierre ? fmtDt(selected.fecha_cierre) : '—' }}</dd>

                <dt>Creado</dt>
                <dd>{{ fmtDt(selected.created_at) }}</dd>
              </dl>

              <div class="info-desc-block">
                <span class="info-desc-label">DESCRIPCIÓN DEL PROBLEMA</span>
                <p class="info-body">{{ selected.descripcion || '— Sin descripción' }}</p>
              </div>

              <template v-if="selected.diagnostico_tecnico">
                <div class="info-desc-block">
                  <span class="info-desc-label">DIAGNÓSTICO TÉCNICO</span>
                  <p class="info-body">{{ selected.diagnostico_tecnico }}</p>
                </div>
              </template>

              <template v-if="selected.motivo_rechazo">
                <div class="info-desc-block rechazo-block">
                  <span class="info-desc-label">MOTIVO DE RECHAZO</span>
                  <p class="info-body rechazo-body">{{ selected.motivo_rechazo }}</p>
                </div>
              </template>
            </section>

            <!-- CUENTA / SEDE -->
            <section class="info-card cuenta-card">
              <h3 class="info-card-title">CUENTA / SEDE</h3>

              <template v-if="cuentaActual">
                <!-- Header de la cuenta -->
                <div class="cuenta-header">
                  <div class="cuenta-header-left">
                    <Building2 :size="16" class="cuenta-icon" />
                    <div>
                      <strong class="cuenta-nombre">{{ cuentaActual.nombre }}</strong>
                      <span class="cuenta-numero">Nº {{ cuentaActual.numero }}</span>
                    </div>
                  </div>
                  <span class="cuenta-tipo-badge">{{ cuentaActual.tipo }}</span>
                </div>

                <!-- Mapa Leaflet -->
                <div v-if="cuentaActual.latitud && cuentaActual.longitud" class="map-wrapper">
                  <div ref="mapEl" class="map-container"></div>
                  <div class="map-coords">
                    <MapPin :size="11" />
                    {{ cuentaActual.latitud.toFixed(6) }}, {{ cuentaActual.longitud.toFixed(6) }}
                  </div>
                </div>
                <div v-else class="map-empty">
                  <MapPin :size="20" />
                  <span>Sin coordenadas registradas</span>
                </div>

                <!-- Datos de la cuenta -->
                <dl class="info-dl cuenta-dl">
                  <dt><MapPin :size="12" /> Dirección</dt>
                  <dd>{{ cuentaActual.direccion }}</dd>

                  <dt><MapPin :size="12" /> Distrito</dt>
                  <dd>{{ cuentaActual.distrito }}</dd>

                  <template v-if="selected.zona && selected.zona !== cuentaActual.distrito">
                    <dt>Referencia</dt>
                    <dd class="zona-ref">{{ selected.zona }}</dd>
                  </template>

                  <dt><User :size="12" /> Responsable</dt>
                  <dd>{{ cuentaActual.contacto || '—' }}</dd>

                  <dt><Phone :size="12" /> Teléfono</dt>
                  <dd>{{ cuentaActual.telefono || '—' }}</dd>
                </dl>
              </template>

              <template v-else>
                <div class="map-empty">
                  <Building2 :size="24" />
                  <span>No hay cuenta asociada a este pedido</span>
                </div>
              </template>
            </section>

          </div><!-- /info-cols -->

          <!-- Informe técnico final si existe -->
          <div v-if="selected.informe" class="info-informe">
            <h3 class="info-card-title">INFORME TÉCNICO FINAL</h3>
            <dl class="info-dl">
              <dt>Diagnóstico final</dt><dd>{{ selected.informe.diagnostico_final }}</dd>
              <dt>Responsable local</dt><dd>{{ selected.informe.responsable_local }}</dd>
              <dt>Pedido solicitado</dt><dd>{{ selected.informe.pedido_solicitado }}</dd>
              <dt>Observaciones</dt><dd>{{ selected.informe.observaciones }}</dd>
              <dt>Recomendaciones</dt><dd>{{ selected.informe.recomendaciones }}</dd>
            </dl>
          </div>
        </div>

        <!-- ── Tab: Cliente ── -->
        <div v-else-if="activeTab === 'cliente'" class="tab-panel">
          <div class="info-cols">
            <section class="info-card">
              <h3 class="info-card-title">CLIENTE</h3>
              <dl class="info-dl">
                <dt>Nombre</dt><dd>{{ selected.cliente_nombre }}</dd>
              </dl>
            </section>
            <section class="info-card">
              <h3 class="info-card-title">CUENTA / SEDE</h3>
              <dl class="info-dl">
                <dt>Cuenta</dt><dd>{{ selected.cuenta_nombre }}</dd>
              </dl>
            </section>
          </div>
        </div>

        <!-- ── Tab: Asignación ── -->
        <div v-else-if="activeTab === 'asignacion'" class="tab-panel">

          <!-- Barra de acción -->
          <div v-if="canAsignarEnTab" class="tab-action-bar">
            <div class="tab-action-info">
              <span v-if="!selected.tecnico_asignado_id">Sin técnico asignado</span>
              <span v-else-if="selected.estado === 'rechazado'" class="action-warn">El técnico rechazó el pedido</span>
              <span v-else>Técnico asignado: <strong>{{ selected.tecnico_nombre }}</strong></span>
            </div>
            <button class="btn-assign" @click="openAsignar">
              <UserPlus :size="14" />
              {{ (selected.tecnico_asignado_id || selected.estado === 'rechazado') ? 'REASIGNAR TÉCNICO' : 'ASIGNAR TÉCNICO' }}
            </button>
          </div>

          <!-- Historial de rechazos -->
          <div v-if="selected.historial_rechazos?.length" class="rechazo-log">
            <h3 class="info-card-title rechazo-title">HISTORIAL DE RECHAZOS</h3>
            <div v-for="r in selected.historial_rechazos" :key="r.at" class="rechazo-row">
              <span class="rechazo-quien">{{ r.tecnico_nombre }}</span>
              <span class="rechazo-motivo">{{ r.motivo }}</span>
              <span class="rechazo-fecha">{{ fmtDt(r.at) }}</span>
            </div>
          </div>

          <!-- Técnico asignado: perfil + mapa de ruta -->
          <template v-if="selected.tecnico_asignado_id">
            <div class="asig-cols">

              <!-- Perfil del técnico -->
              <section class="info-card">
                <h3 class="info-card-title">TÉCNICO ASIGNADO</h3>
                <div class="tec-perfil">
                  <div class="tec-perfil-avatar">{{ (tecnicoActual?.nombre || selected.tecnico_nombre)?.charAt(0) }}</div>
                  <div class="tec-perfil-data">
                    <strong class="tec-perfil-nombre">{{ tecnicoActual?.nombre || selected.tecnico_nombre }}</strong>
                    <span class="badge-estado" :class="`est-${selected.estado}`">{{ ESTADO_LABEL[selected.estado] }}</span>
                  </div>
                </div>
                <dl class="info-dl" v-if="tecnicoActual">
                  <dt><MapPin :size="12" /> Zona</dt>
                  <dd>{{ tecnicoActual.zona || '—' }}</dd>
                  <dt><Wrench :size="12" /> Especialidad</dt>
                  <dd>{{ tecnicoActual.especialidad || '—' }}</dd>
                  <dt><Phone :size="12" /> Teléfono</dt>
                  <dd>{{ tecnicoActual.telefono || '—' }}</dd>
                  <dt><User :size="12" /> DNI</dt>
                  <dd>{{ tecnicoActual.dni || '—' }}</dd>
                  <template v-if="tecnicoActual.latitud_base && tecnicoActual.longitud_base">
                    <dt><MapPin :size="12" /> Base</dt>
                    <dd class="code-text" style="font-size:11px">{{ tecnicoActual.latitud_base.toFixed(5) }}, {{ tecnicoActual.longitud_base.toFixed(5) }}</dd>
                  </template>
                  <template v-if="recomendacion?.ranking.find(t => t.id === selected!.tecnico_asignado_id)?.distancia_km != null">
                    <dt>Distancia</dt>
                    <dd style="color:var(--blue);font-weight:600">
                      {{ recomendacion!.ranking.find(t => t.id === selected!.tecnico_asignado_id)!.distancia_km!.toFixed(1) }} km al trabajo
                    </dd>
                  </template>
                </dl>
                <p v-else class="info-none">Cargando datos del técnico...</p>
              </section>

              <!-- Mapa de ruta -->
              <section class="info-card asig-ruta-card">
                <div class="asig-ruta-head">
                  <h3 class="info-card-title" style="border:none;padding:0;margin:0">RUTA AL TRABAJO</h3>
                  <div class="ruta-legend">
                    <span class="legend-item legend-job">Trabajo</span>
                    <span class="legend-item legend-tech">Técnico</span>
                  </div>
                </div>
                <div
                  v-if="tecnicoActual?.latitud_base || cuentaActual?.latitud"
                  ref="mapAsignacionTabEl"
                  class="asig-ruta-map"
                ></div>
                <div v-else class="map-empty">
                  <MapPin :size="18" />
                  <span>Sin coordenadas registradas</span>
                </div>
              </section>

            </div>
          </template>
          <div v-else class="info-card">
            <p class="info-none">Sin técnico asignado</p>
          </div>

          <!-- EPPs asignados -->
          <section class="info-card" v-if="selected.epps_asignados?.length">
            <h3 class="info-card-title">EPPs ASIGNADOS</h3>
            <table class="data-table">
              <thead><tr><th>Ítem</th><th>SKU</th><th>Cant.</th><th>P.Unit</th><th>Subtotal</th></tr></thead>
              <tbody>
                <tr v-for="e in selected.epps_asignados" :key="e.item_id">
                  <td>{{ e.nombre }}</td><td>{{ e.sku }}</td><td>{{ e.cantidad }}</td>
                  <td>S/ {{ e.precio_unitario.toFixed(2) }}</td>
                  <td>S/ {{ (e.cantidad * e.precio_unitario).toFixed(2) }}</td>
                </tr>
              </tbody>
            </table>
          </section>

        </div>

        <!-- ── Tab: Seguimiento ── -->
        <div v-else-if="activeTab === 'seguimiento'" class="tab-panel">
          <div class="info-cols">
            <section class="info-card">
              <h3 class="info-card-title">CHECKLIST DE CAMPO</h3>
              <div class="checklist">
                <div v-for="step in selected.checklist" :key="step.step_id" class="check-row" :class="{ done: step.completado }">
                  <span class="check-mark">
                    <CheckSquare2 v-if="step.completado" :size="16" />
                    <Square v-else :size="16" />
                  </span>
                  <div class="check-body">
                    <strong>{{ step.label }}</strong>
                    <span v-if="step.nota" class="check-nota">{{ step.nota }}</span>
                    <span v-if="step.completado_en" class="check-fecha">{{ fmtDt(step.completado_en!) }}</span>
                  </div>
                </div>
              </div>
            </section>

            <section class="info-card">
              <h3 class="info-card-title">EVIDENCIAS FOTOGRÁFICAS</h3>
              <div v-if="selected.evidencias?.length" class="ev-grid">
                <div v-for="e in selected.evidencias" :key="e.id" class="ev-item">
                  <a :href="evidenciaUrl(e.archivo)" target="_blank">
                    <img :src="evidenciaUrl(e.archivo)" :alt="e.nombre" />
                  </a>
                  <div class="ev-caption">
                    <span class="ev-stage" :class="`stage-${e.stage}`">{{ e.stage.toUpperCase() }}</span>
                    <span>{{ e.descripcion }}</span>
                  </div>
                </div>
              </div>
              <p v-else class="info-none">Sin evidencias cargadas</p>

              <template v-if="selected.materiales_usados?.length">
                <h3 class="info-card-title mt">MATERIALES USADOS</h3>
                <table class="data-table">
                  <thead><tr><th>Material</th><th>Cant.</th><th>P.Unit</th><th>Subtotal</th></tr></thead>
                  <tbody>
                    <tr v-for="m in selected.materiales_usados" :key="m.item_id">
                      <td>{{ m.nombre }}</td><td>{{ m.cantidad }}</td>
                      <td>S/ {{ m.precio_unitario.toFixed(2) }}</td>
                      <td>S/ {{ (m.cantidad * m.precio_unitario).toFixed(2) }}</td>
                    </tr>
                  </tbody>
                </table>
              </template>
            </section>
          </div>
        </div>

        <!-- ── Tab: Costos ── -->
        <div v-else-if="activeTab === 'costos'" class="tab-panel">
          <div class="info-cols">
            <section class="info-card">
              <h3 class="info-card-title">EPPs ASIGNADOS</h3>
              <table v-if="selected.epps_asignados?.length" class="data-table">
                <thead><tr><th>Ítem</th><th>Cant.</th><th>P.Unit</th><th>Subtotal</th></tr></thead>
                <tbody>
                  <tr v-for="e in selected.epps_asignados" :key="e.item_id">
                    <td>{{ e.nombre }}</td><td>{{ e.cantidad }}</td>
                    <td>S/ {{ e.precio_unitario.toFixed(2) }}</td>
                    <td>S/ {{ (e.cantidad * e.precio_unitario).toFixed(2) }}</td>
                  </tr>
                  <tr class="total-row"><td colspan="3">Subtotal EPPs</td><td>S/ {{ fmt(selected.costo_epps) }}</td></tr>
                </tbody>
              </table>
              <p v-else class="info-none">Sin EPPs registrados</p>
            </section>
            <section class="info-card">
              <h3 class="info-card-title">MATERIALES USADOS</h3>
              <table v-if="selected.materiales_usados?.length" class="data-table">
                <thead><tr><th>Material</th><th>Cant.</th><th>P.Unit</th><th>Subtotal</th></tr></thead>
                <tbody>
                  <tr v-for="m in selected.materiales_usados" :key="m.item_id">
                    <td>{{ m.nombre }}</td><td>{{ m.cantidad }}</td>
                    <td>S/ {{ m.precio_unitario.toFixed(2) }}</td>
                    <td>S/ {{ (m.cantidad * m.precio_unitario).toFixed(2) }}</td>
                  </tr>
                  <tr class="total-row"><td colspan="3">Subtotal materiales</td><td>S/ {{ fmt(selected.costo_materiales) }}</td></tr>
                </tbody>
              </table>
              <p v-else class="info-none">Sin materiales registrados</p>
              <div class="grand-total">
                <span>COSTO TOTAL DEL PEDIDO</span>
                <strong>S/ {{ fmt(selected.costo_total) }}</strong>
              </div>
            </section>
          </div>
        </div>

        <!-- ── Tab: Historial ── -->
        <div v-else-if="activeTab === 'historial'" class="tab-panel">
          <div class="timeline">
            <div
              v-for="e in [...(selected.historial || [])].reverse()"
              :key="e.at + e.evento"
              class="tl-row"
            >
              <div class="tl-marker" :class="`ev-${e.evento}`"></div>
              <div class="tl-line"></div>
              <div class="tl-body">
                <strong class="tl-evento">{{ EVENTO_LABEL[e.evento] || e.evento }}</strong>
                <span class="tl-detalle">{{ e.detalle }}</span>
                <span class="tl-meta">{{ e.usuario }} · {{ fmtDt(e.at) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Acciones secundarias -->
        <div class="detail-footer">
          <button v-if="canDarDeBaja" class="btn-danger-ghost" @click="openBaja">
            <Trash2 :size="13" style="vertical-align:middle" /> Dar de baja
          </button>
        </div>

      </template>
    </main>

    <!-- ════════════════════ MODAL: CREAR PEDIDO ════════════════════ -->
    <Teleport to="body">
      <div v-if="modals.create" class="modal-overlay" :class="`pv-modal-${theme}`" @click.self="modals.create = false">
        <div class="modal" style="width:680px">
          <div class="modal-head">
            <h3>NUEVO PEDIDO</h3>
            <button class="icon-btn" @click="modals.create = false"><X :size="14" /></button>
          </div>

          <form @submit.prevent="submitCreate" class="modal-body">
            <div class="form-section">
              <h4 class="form-section-title">DATOS DE CUENTA</h4>
              <div class="form-grid">
                <label class="form-field">
                  <span>Cliente *</span>
                  <select v-model="cf.cliente_id" required @change="onClienteChange">
                    <option value="">— Seleccionar cliente</option>
                    <option v-for="c in clientes" :key="c.id" :value="c.id">{{ c.nombre }}</option>
                  </select>
                </label>
                <label class="form-field">
                  <span>Cuenta / Sede *</span>
                  <select v-model="cf.cuenta_id" required :disabled="!cf.cliente_id" @change="onCuentaChange">
                    <option value="">— Seleccionar cuenta</option>
                    <option v-for="c in cuentasFiltradas" :key="c.id" :value="c.id">{{ c.nombre }} ({{ c.numero }})</option>
                  </select>
                </label>
              </div>

              <!-- Vista previa de la cuenta seleccionada -->
              <div v-if="cuentaPreview" class="cuenta-preview">
                <div class="preview-row"><span>Dirección</span><strong>{{ cuentaPreview.direccion }}, {{ cuentaPreview.distrito }}</strong></div>
                <div class="preview-row"><span>Responsable</span><strong>{{ cuentaPreview.contacto }}</strong></div>
                <div class="preview-row"><span>Teléfono</span><strong>{{ cuentaPreview.telefono }}</strong></div>
                <div class="preview-row"><span>Tipo</span><strong>{{ cuentaPreview.tipo }}</strong></div>
              </div>
            </div>

            <div class="form-section">
              <h4 class="form-section-title">DATOS DEL PEDIDO</h4>
              <label class="form-field wide">
                <span>Título *</span>
                <input v-model="cf.titulo" required placeholder="Descripción breve del pedido" />
              </label>
              <label class="form-field wide">
                <span>Descripción del problema *</span>
                <textarea v-model="cf.descripcion" required rows="3" placeholder="Detalla el problema o servicio requerido..."></textarea>
              </label>
              <div class="form-grid">
                <label class="form-field">
                  <span>Tipo de servicio *</span>
                  <select v-model="cf.tipo_servicio" required>
                    <option value="">— Seleccionar</option>
                    <option v-for="s in SERVICIOS" :key="s" :value="s">{{ s }}</option>
                  </select>
                </label>
                <label class="form-field">
                  <span>Referencia de zona <small>(auto-completado)</small></span>
                  <input v-model="cf.zona" placeholder="Ej: Alt. Av. La Molina, frente al grifo" />
                </label>
                <label class="form-field">
                  <span>Prioridad *</span>
                  <select v-model="cf.prioridad" required>
                    <option value="baja">BAJA</option>
                    <option value="media">MEDIA</option>
                    <option value="alta">ALTA</option>
                    <option value="critica">CRÍTICA</option>
                  </select>
                </label>
                <label class="form-field">
                  <span>Fecha programada</span>
                  <input v-model="cf.fecha_programada" type="datetime-local" />
                </label>
              </div>
            </div>

            <div class="modal-footer">
              <p v-if="createError" class="form-error">{{ createError }}</p>
              <button type="button" class="btn-ghost" @click="modals.create = false">Cancelar</button>
              <button type="submit" class="btn-green" :disabled="saving">
                {{ saving ? 'Creando...' : 'CREAR PEDIDO' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- ════════════════════ MODAL: ASIGNAR TÉCNICO ════════════════════ -->
    <Teleport to="body">
      <div v-if="modals.asignar" class="modal-overlay" :class="`pv-modal-${theme}`" @click.self="modals.asignar = false">
        <div class="modal modal-asignar">

          <div class="modal-head">
            <h3>{{ (selected?.tecnico_asignado_id || selected?.estado === 'rechazado') ? 'REASIGNAR TÉCNICO' : 'ASIGNAR TÉCNICO' }} — {{ selected?.codigo }}</h3>
            <button class="icon-btn" @click="modals.asignar = false"><X :size="14" /></button>
          </div>

          <!-- Tabs del modal -->
          <div class="modal-tabs-bar">
            <button class="modal-tab" :class="{ active: asignarTab === 'asignacion' }" @click="asignarTab = 'asignacion'">
              ASIGNACIÓN
            </button>
            <template v-if="selected?.estado !== 'rechazado'">
              <button class="modal-tab" :class="{ active: asignarTab === 'epps' }" @click="asignarTab = 'epps'">
                EPPs
                <span v-if="af.epps.length" class="modal-tab-badge">{{ af.epps.length }}</span>
              </button>
              <button class="modal-tab" :class="{ active: asignarTab === 'materiales' }" @click="asignarTab = 'materiales'">
                MATERIALES
                <span v-if="af.materiales.length" class="modal-tab-badge">{{ af.materiales.length }}</span>
              </button>
            </template>
          </div>

          <!-- Tab: ASIGNACIÓN -->
          <div v-if="asignarTab === 'asignacion'" class="asignar-body">
            <div class="asignar-panel">

              <!-- Lista de técnicos con ranking -->
              <div class="tech-list">
                <div class="tech-list-header">
                  <span>TÉCNICOS DISPONIBLES</span>
                  <span class="tech-count">{{ recomendacion?.ranking.length ?? '...' }}</span>
                </div>
                <div v-if="!recomendacion" class="tech-loading">Calculando ranking...</div>
                <div
                  v-for="(tech, idx) in recomendacion?.ranking"
                  :key="tech.id"
                  class="tech-card"
                  :class="{ selected: af.tecnico_id === tech.id }"
                  @click="af.tecnico_id = tech.id"
                >
                  <div class="tech-card-head">
                    <div class="tech-avatar">{{ tech.nombre.charAt(0) }}</div>
                    <div class="tech-info">
                      <div class="tech-nombre-row">
                        <span class="tech-nombre">{{ tech.nombre }}</span>
                        <span v-if="idx === 0" class="tech-sugerido-badge">SUGERIDO</span>
                      </div>
                      <span class="tech-meta">
                        {{ tech.zona }}<template v-if="tech.especialidad"> · {{ tech.especialidad }}</template>
                      </span>
                    </div>
                    <div class="tech-score-circle" :class="scoreClass(tech.score)">
                      <span class="score-num">{{ Math.round(tech.score) }}</span>
                      <span class="score-pct">%</span>
                    </div>
                  </div>
                  <div class="tech-score-bar">
                    <div class="score-bar-fill" :class="scoreClass(tech.score)" :style="{ width: tech.score + '%' }"></div>
                  </div>
                  <div class="tech-card-stats">
                    <span class="tech-stat">
                      <MapPin :size="10" />
                      {{ tech.distancia_km != null ? tech.distancia_km.toFixed(1) + ' km' : 'Sin coord.' }}
                    </span>
                    <span class="tech-stat">
                      {{ tech.pedidos_activos }} pedido{{ tech.pedidos_activos !== 1 ? 's' : '' }} activo{{ tech.pedidos_activos !== 1 ? 's' : '' }}
                    </span>
                    <span class="tech-stat" :class="tech.specialty_match ? 'match-yes' : 'match-no'">
                      <Wrench :size="10" />
                      {{ tech.specialty_match ? 'Especialidad ok' : 'Sin coincidencia' }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Panel del mapa -->
              <div class="asignar-map-panel">
                <div class="map-legend">
                  <span class="legend-item legend-job">Trabajo</span>
                  <span class="legend-item legend-tech">Técnico</span>
                  <span v-if="af.tecnico_id" class="legend-dist">
                    {{ recomendacion?.ranking.find(t => t.id === af.tecnico_id)?.distancia_km?.toFixed(1) ?? '—' }} km
                  </span>
                </div>
                <div ref="mapAsignarEl" class="map-asignar-container"></div>
                <div v-if="!af.tecnico_id" class="map-hint">Selecciona un técnico para ver la ruta</div>
              </div>

            </div>
          </div>

          <!-- Tab: EPPs -->
          <div v-else-if="asignarTab === 'epps'" class="inv-tab-body">
            <div class="inv-split">
              <!-- Catálogo -->
              <div class="inv-catalog">
                <div class="inv-search-wrap">
                  <input v-model="eppSearch" type="search" placeholder="Buscar EPP..." class="inv-search" />
                </div>
                <div class="inv-items-list">
                  <div v-if="!filteredEpps.length" class="inv-empty">Sin resultados</div>
                  <div
                    v-for="item in filteredEpps"
                    :key="item.id"
                    class="inv-item"
                    @click="addEppDirect(item)"
                  >
                    <div class="inv-item-info">
                      <span class="inv-item-name">{{ item.nombre }}</span>
                      <span class="inv-item-meta">{{ item.sku }} · S/ {{ item.precio_unitario.toFixed(2) }}</span>
                    </div>
                    <div class="inv-item-right">
                      <span class="inv-stock">{{ item.stock_disponible }} disp.</span>
                      <button class="inv-add-btn" @click.stop="addEppDirect(item)">+</button>
                    </div>
                  </div>
                </div>
              </div>
              <!-- Carrito -->
              <div class="inv-cart">
                <div class="inv-cart-header">
                  SELECCIONADOS <span class="tech-count">{{ af.epps.length }}</span>
                </div>
                <div v-if="!af.epps.length" class="inv-empty" style="padding:20px">Haz clic en los ítems para agregarlos</div>
                <table v-else class="data-table">
                  <thead><tr><th>Ítem</th><th>Cant.</th><th>Subtotal</th><th></th></tr></thead>
                  <tbody>
                    <tr v-for="(e, i) in af.epps" :key="i">
                      <td>{{ e.nombre }}<br><span style="font-size:10px;color:var(--text-3)">{{ e.sku }}</span></td>
                      <td>
                        <div class="qty-ctrl">
                          <button @click="e.cantidad > 1 ? e.cantidad-- : af.epps.splice(i,1)">−</button>
                          <span>{{ e.cantidad }}</span>
                          <button @click="e.cantidad++">+</button>
                        </div>
                      </td>
                      <td>S/ {{ (e.cantidad * e.precio_unitario).toFixed(2) }}</td>
                      <td><button class="btn-remove" @click="af.epps.splice(i,1)"><X :size="10" /></button></td>
                    </tr>
                    <tr class="total-row"><td colspan="2">Total EPPs</td><td>S/ {{ fmtSum(af.epps) }}</td><td></td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- Tab: MATERIALES -->
          <div v-else-if="asignarTab === 'materiales'" class="inv-tab-body">
            <div class="inv-split">
              <!-- Catálogo -->
              <div class="inv-catalog">
                <div class="inv-search-wrap">
                  <input v-model="matSearch" type="search" placeholder="Buscar material..." class="inv-search" />
                </div>
                <div class="inv-items-list">
                  <div v-if="!filteredMats.length" class="inv-empty">Sin resultados</div>
                  <div
                    v-for="item in filteredMats"
                    :key="item.id"
                    class="inv-item"
                    @click="addMatDirect(item)"
                  >
                    <div class="inv-item-info">
                      <span class="inv-item-name">{{ item.nombre }}</span>
                      <span class="inv-item-meta">{{ item.sku }} · S/ {{ item.precio_unitario.toFixed(2) }}</span>
                    </div>
                    <div class="inv-item-right">
                      <span class="inv-stock">{{ item.stock_disponible }} disp.</span>
                      <button class="inv-add-btn" @click.stop="addMatDirect(item)">+</button>
                    </div>
                  </div>
                </div>
              </div>
              <!-- Carrito -->
              <div class="inv-cart">
                <div class="inv-cart-header">
                  SELECCIONADOS <span class="tech-count">{{ af.materiales.length }}</span>
                </div>
                <div v-if="!af.materiales.length" class="inv-empty" style="padding:20px">Haz clic en los ítems para agregarlos</div>
                <table v-else class="data-table">
                  <thead><tr><th>Material</th><th>Cant.</th><th>Subtotal</th><th></th></tr></thead>
                  <tbody>
                    <tr v-for="(m, i) in af.materiales" :key="i">
                      <td>{{ m.nombre }}<br><span style="font-size:10px;color:var(--text-3)">{{ m.sku }}</span></td>
                      <td>
                        <div class="qty-ctrl">
                          <button @click="m.cantidad > 1 ? m.cantidad-- : af.materiales.splice(i,1)">−</button>
                          <span>{{ m.cantidad }}</span>
                          <button @click="m.cantidad++">+</button>
                        </div>
                      </td>
                      <td>S/ {{ (m.cantidad * m.precio_unitario).toFixed(2) }}</td>
                      <td><button class="btn-remove" @click="af.materiales.splice(i,1)"><X :size="10" /></button></td>
                    </tr>
                    <tr class="total-row"><td colspan="2">Total materiales</td><td>S/ {{ fmtSum(af.materiales) }}</td><td></td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- Footer con navegación por pasos -->
          <div class="modal-footer-static">
            <p v-if="asignarError" class="form-error">{{ asignarError }}</p>
            <button class="btn-ghost" @click="modals.asignar = false">Cancelar</button>
            <button v-if="!isFirstAsignarTab" class="btn-ghost" @click="prevAsignarTab">← Volver</button>
            <button
              v-if="!isLastAsignarTab"
              class="btn-green"
              :disabled="asignarTab === 'asignacion' && !af.tecnico_id"
              @click="nextAsignarTab"
            >Siguiente →</button>
            <button
              v-else
              class="btn-green"
              :disabled="!af.tecnico_id || actionLoading"
              @click="submitAsignar"
            >{{ actionLoading ? 'Procesando...' : ((selected?.tecnico_asignado_id || selected?.estado === 'rechazado') ? 'REASIGNAR' : 'ASIGNAR TÉCNICO') }}</button>
          </div>

        </div>
      </div>
    </Teleport>

    <!-- ════════════════════ MODAL: COMPLETAR ════════════════════ -->
    <Teleport to="body">
      <div v-if="modals.completar" class="modal-overlay" :class="`pv-modal-${theme}`" @click.self="modals.completar = false">
        <div class="modal" style="width:440px">
          <div class="modal-head">
            <h3>COMPLETAR PEDIDO</h3>
            <button class="icon-btn" @click="modals.completar = false"><X :size="14" /></button>
          </div>
          <div class="modal-body">
            <p class="confirm-text">
              ¿Confirmas que el pedido <strong>{{ selected?.codigo }}</strong> ha sido completado satisfactoriamente?<br/>
              El estado cambiará a <strong>COMPLETADO</strong> y se registrará el cierre.
            </p>
            <div class="modal-footer">
              <button class="btn-ghost" @click="modals.completar = false">Cancelar</button>
              <button class="btn-green" :disabled="actionLoading" @click="submitCompletar">
                {{ actionLoading ? 'Procesando...' : 'CONFIRMAR CIERRE' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ════════════════════ MODAL: DAR DE BAJA ════════════════════ -->
    <Teleport to="body">
      <div v-if="modals.baja" class="modal-overlay" :class="`pv-modal-${theme}`" @click.self="modals.baja = false">
        <div class="modal" style="width:460px">
          <div class="modal-head">
            <h3>DAR DE BAJA — {{ selected?.codigo }}</h3>
            <button class="icon-btn" @click="modals.baja = false"><X :size="14" /></button>
          </div>
          <div class="modal-body">
            <p class="confirm-text">Esta acción es irreversible. El pedido quedará inactivo.</p>
            <label class="form-field wide">
              <span>Motivo de baja *</span>
              <textarea v-model="bajaMotivo" rows="3" required placeholder="Explica el motivo..."></textarea>
            </label>
            <div class="modal-footer">
              <p v-if="bajaError" class="form-error">{{ bajaError }}</p>
              <button class="btn-ghost" @click="modals.baja = false">Cancelar</button>
              <button class="btn-danger" :disabled="actionLoading" @click="submitBaja">
                {{ actionLoading ? 'Procesando...' : 'CONFIRMAR BAJA' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, reactive, watch, nextTick } from 'vue';
import {
  LayoutGrid, Sun, Moon, Plus, X, AlertTriangle,
  CheckSquare2, Square, Download, Trash2, MapPin, Phone, User, Building2, UserPlus, Wrench,
} from 'lucide-vue-next';
import L, { type Map as LeafletMap } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getSessionUser, esAdmin, esCoordinador } from '../stores/sessionStore';
import {
  listPedidos, getPedido, createPedido as apiCreate,
  asignarTecnico, reasignarTecnico, completarPedido, darDeBaja,
  evidenciaUrl, getPdfUrl,
  type ApiPedido, type ApiItemPedido,
} from '../api/pedidos';
import { listClientes, type ApiCliente } from '../api/clientes';
import { listCuentas, type ApiCuenta } from '../api/cuentas';
import { listTecnicos, getTecnico, getRecomendacion, type ApiTecnico, type ApiRecomendacion, type ApiRecomendacionItem } from '../api/tecnicos';
import { listInventario, type ApiInventario } from '../api/inventario';

// ── Tipos y constantes ─────────────────────────────────────────────────────
const currentUser = getSessionUser();

const FASES = [
  { key: 'creacion',     label: 'Creación' },
  { key: 'programacion', label: 'Programación' },
  { key: 'seguimiento',  label: 'Seguimiento' },
  { key: 'cierre',       label: 'Cierre' },
] as const;

const FASE_LABEL: Record<string, string> = {
  creacion: 'Creación', programacion: 'Programación',
  seguimiento: 'Seguimiento', cierre: 'Cierre',
};

const ESTADO_LABEL: Record<string, string> = {
  'por-confirmar': 'Por confirmar', confirmado: 'Confirmado',
  rechazado: 'Rechazado', 'en-labor': 'En labor',
  'cierre-tecnico': 'Cierre técnico', completado: 'Completado',
  'dado-de-baja': 'Dado de baja',
};

const EVENTO_LABEL: Record<string, string> = {
  creacion: 'Pedido creado', asignacion: 'Técnico asignado',
  confirmacion: 'Confirmado por técnico', rechazo: 'Rechazado por técnico',
  reasignacion: 'Reasignado', inicio_labor: 'Inicio de labor',
  checklist: 'Checklist actualizado', evidencia: 'Evidencia cargada',
  diagnostico: 'Diagnóstico actualizado', materiales: 'Materiales registrados',
  informe: 'Informe enviado', completado: 'Pedido completado', baja: 'Dado de baja',
};

const SERVICIOS = [
  'Instalación CCTV', 'Mantenimiento de red', 'Control de acceso',
  'Sistema de alarmas', 'Instalación DVR/NVR', 'Cableado estructurado',
  'Intercomunicadores', 'Servicio técnico general',
];

const TABS = [
  { key: 'info',       label: 'INFORMACIÓN' },
  { key: 'cliente',    label: 'CLIENTE' },
  { key: 'asignacion', label: 'ASIGNACIÓN' },
  { key: 'seguimiento',label: 'SEGUIMIENTO' },
  { key: 'costos',     label: 'COSTOS' },
  { key: 'historial',  label: 'HISTORIAL' },
];

// ── Estado ─────────────────────────────────────────────────────────────────
const theme = ref<'dark' | 'light'>(
  (localStorage.getItem('pv_theme') as 'dark' | 'light') || 'dark'
);

const pedidos   = ref<ApiPedido[]>([]);
const loading   = ref(false);
const selectedId = ref<string | null>(null);
const selected  = ref<ApiPedido | null>(null);
const activeTab = ref('info');

const search       = ref('');
const filterFase   = ref('');
const filterEstado = ref('');

const clientes   = ref<ApiCliente[]>([]);
const cuentas    = ref<ApiCuenta[]>([]);
const tecnicos   = ref<ApiTecnico[]>([]);
const inventario = ref<ApiInventario[]>([]);
const recomendacion = ref<ApiRecomendacion | null>(null);

const actionLoading = ref(false);
const saving        = ref(false);

const modals = reactive({
  create: false, asignar: false, completar: false, baja: false,
});

// Formulario crear
const cf = reactive({
  cliente_id: '', cuenta_id: '', titulo: '', descripcion: '',
  tipo_servicio: '', zona: '', prioridad: 'media', fecha_programada: '',
});
const cuentaPreview = ref<ApiCuenta | null>(null);
const createError = ref('');

// Formulario asignar
const af = reactive({
  tecnico_id: '',
  epps: [] as ApiItemPedido[],
  materiales: [] as ApiItemPedido[],
});
const asignarError = ref('');

// Dar de baja
const bajaMotivo = ref('');
const bajaError  = ref('');

// Mapa Leaflet (tab info)
const mapEl = ref<HTMLDivElement | null>(null);
let leafletMap: LeafletMap | null = null;

// Modal asignar técnico
const asignarTab = ref<'asignacion' | 'epps' | 'materiales'>('asignacion');
const mapAsignarEl = ref<HTMLDivElement | null>(null);
let leafletAsignarMap: LeafletMap | null = null;
let markerTech: L.Marker | null = null;
let routeLine: L.Polyline | null = null;

// Tab asignación (detalle del pedido)
const tecnicoAsignado = ref<ApiTecnico | null>(null);
const mapAsignacionTabEl = ref<HTMLDivElement | null>(null);
let leafletAsignacionTabMap: LeafletMap | null = null;

// Búsqueda en selectores de EPP/material
const eppSearch = ref('');
const matSearch = ref('');

// ── Computados ─────────────────────────────────────────────────────────────
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
  if (filterFase.value)   list = list.filter(p => p.fase === filterFase.value);
  if (filterEstado.value) list = list.filter(p => p.estado === filterEstado.value);
  return list;
});

const rechazadosCount = computed(() => pedidos.value.filter(p => p.estado === 'rechazado').length);

const cuentasFiltradas = computed(() => cuentas.value.filter(c => c.cliente_id === cf.cliente_id));

const eppsInv = computed(() => inventario.value.filter(i => i.categoria === 'epp' && i.activo && i.stock_disponible > 0));
const matsInv = computed(() => inventario.value.filter(i => i.categoria !== 'epp' && i.activo && i.stock_disponible > 0));

const pdfUrl = computed(() => selected.value ? getPdfUrl(selected.value.id) : '#');

const cuentaActual = computed<ApiCuenta | null>(() => {
  if (!selected.value?.cuenta_id) return null;
  return cuentas.value.find(c => c.id === selected.value!.cuenta_id) ?? null;
});

const tecnicoActual = computed<ApiTecnico | null>(() =>
  tecnicoAsignado.value ?? tecnicos.value.find(t => t.id === selected.value?.tecnico_asignado_id) ?? null
);

const filteredEpps = computed(() => {
  const q = eppSearch.value.toLowerCase();
  return eppsInv.value.filter(i => !q || i.nombre.toLowerCase().includes(q) || i.sku.toLowerCase().includes(q));
});
const filteredMats = computed(() => {
  const q = matSearch.value.toLowerCase();
  return matsInv.value.filter(i => !q || i.nombre.toLowerCase().includes(q) || i.sku.toLowerCase().includes(q));
});

const asignarTabs = computed<Array<'asignacion' | 'epps' | 'materiales'>>(() =>
  selected.value?.estado === 'rechazado' ? ['asignacion'] : ['asignacion', 'epps', 'materiales']
);
const isFirstAsignarTab = computed(() => asignarTab.value === asignarTabs.value[0]);
const isLastAsignarTab  = computed(() => asignarTab.value === asignarTabs.value[asignarTabs.value.length - 1]);

// CTA principal según estado
const mainCTA = computed(() => {
  if (!selected.value) return null;
  if (!esAdmin(currentUser) && !esCoordinador(currentUser)) return null;
  const s = selected.value;

  if (!s.tecnico_asignado_id && s.estado === 'por-confirmar')
    return { type: 'assign', label: 'ASIGNAR TÉCNICO →', desc: 'El pedido no tiene técnico. Asigna uno para continuar.', action: openAsignar };
  if (s.estado === 'rechazado')
    return { type: 'warn', label: 'REASIGNAR TÉCNICO →', desc: `Pedido rechazado: ${s.motivo_rechazo || ''}`, action: openAsignar };
  if (s.estado === 'cierre-tecnico')
    return { type: 'complete', label: 'MARCAR COMPLETADO →', desc: 'El técnico ha enviado el informe. Confirma el cierre.', action: () => { modals.completar = true; } };
  return null;
});

const canDarDeBaja = computed(() =>
  selected.value &&
  !['completado', 'dado-de-baja'].includes(selected.value.estado) &&
  (esAdmin(currentUser) || esCoordinador(currentUser))
);

const canAsignarEnTab = computed(() =>
  selected.value &&
  (esAdmin(currentUser) || esCoordinador(currentUser)) &&
  !['completado', 'dado-de-baja'].includes(selected.value.estado)
);

// ── Helpers ─────────────────────────────────────────────────────────────────
function fmt(n: number) { return n.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
function fmtDt(iso: string) { return new Date(iso).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' }); }
function fmtSum(items: ApiItemPedido[]) { return items.reduce((s, i) => s + i.cantidad * i.precio_unitario, 0).toFixed(2); }
function scoreClass(score: number) {
  if (score >= 70) return 'score-high';
  if (score >= 40) return 'score-mid';
  return 'score-low';
}

function phaseStepClass(key: string) {
  if (!selected.value) return '';
  const order = ['creacion', 'programacion', 'seguimiento', 'cierre'];
  const cur = order.indexOf(selected.value.fase);
  const idx = order.indexOf(key);
  return idx < cur ? 'done' : idx === cur ? 'active' : 'upcoming';
}

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark';
  localStorage.setItem('pv_theme', theme.value);
}

function updateList(p: ApiPedido) {
  const idx = pedidos.value.findIndex(x => x.id === p.id);
  if (idx >= 0) pedidos.value[idx] = p;
}

function nextAsignarTab() {
  const tabs = asignarTabs.value;
  const idx = tabs.indexOf(asignarTab.value);
  if (idx < tabs.length - 1) asignarTab.value = tabs[idx + 1];
}
function prevAsignarTab() {
  const tabs = asignarTabs.value;
  const idx = tabs.indexOf(asignarTab.value);
  if (idx > 0) asignarTab.value = tabs[idx - 1];
}
function addEppDirect(item: ApiInventario) {
  const existing = af.epps.find(e => e.item_id === item.id);
  if (existing) existing.cantidad++;
  else af.epps.push({ item_id: item.id, nombre: item.nombre, sku: item.sku, precio_unitario: item.precio_unitario, cantidad: 1 });
}
function addMatDirect(item: ApiInventario) {
  const existing = af.materiales.find(m => m.item_id === item.id);
  if (existing) existing.cantidad++;
  else af.materiales.push({ item_id: item.id, nombre: item.nombre, sku: item.sku, precio_unitario: item.precio_unitario, cantidad: 1 });
}

// ── Mapa ────────────────────────────────────────────────────────────────────
function destroyMap() {
  if (leafletMap) {
    leafletMap.stop();
    leafletMap.remove();
    leafletMap = null;
  }
}

function initMap() {
  destroyMap();
  const cuenta = cuentaActual.value;
  if (!mapEl.value || !cuenta?.latitud || !cuenta?.longitud) return;

  leafletMap = L.map(mapEl.value, { zoomControl: true, attributionControl: false })
    .setView([cuenta.latitud, cuenta.longitud], 15);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(leafletMap);

  const markerIcon = L.divIcon({
    html: `<div style="width:14px;height:14px;background:#3fb950;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.5);"></div>`,
    className: '',
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
  L.marker([cuenta.latitud, cuenta.longitud], { icon: markerIcon })
    .bindPopup(`<b>${cuenta.nombre}</b><br>${cuenta.direccion}`)
    .addTo(leafletMap);
}

watch(
  [activeTab, () => selected.value?.id, () => selected.value?.tecnico_asignado_id],
  () => {
    if (activeTab.value === 'info') {
      nextTick(initMap);
      destroyAsignacionTabMap();
    } else if (activeTab.value === 'asignacion') {
      destroyMap();
      nextTick(initAsignacionTabMap);
    } else {
      destroyMap();
      destroyAsignacionTabMap();
    }
  }
);

onUnmounted(() => { destroyMap(); destroyAsignarMap(); destroyAsignacionTabMap(); });

// ── Mapa tab asignación ──────────────────────────────────────────────────────
function destroyAsignacionTabMap() {
  if (leafletAsignacionTabMap) { leafletAsignacionTabMap.stop(); leafletAsignacionTabMap.remove(); leafletAsignacionTabMap = null; }
}

function initAsignacionTabMap() {
  destroyAsignacionTabMap();
  if (!mapAsignacionTabEl.value) return;
  const tech = tecnicoActual.value;
  const cuenta = cuentaActual.value;
  const hasTech = !!(tech?.latitud_base && tech?.longitud_base);
  const hasJob  = !!(cuenta?.latitud && cuenta?.longitud);
  if (!hasTech && !hasJob) return;

  const centerLat = hasJob ? cuenta!.latitud  : tech!.latitud_base;
  const centerLon = hasJob ? cuenta!.longitud : tech!.longitud_base;

  leafletAsignacionTabMap = L.map(mapAsignacionTabEl.value, { zoomControl: true, attributionControl: false })
    .setView([centerLat, centerLon], 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(leafletAsignacionTabMap);

  if (hasJob) {
    const icon = L.divIcon({ html: `<div style="width:14px;height:14px;background:#3fb950;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.5);"></div>`, className: '', iconSize: [14,14], iconAnchor: [7,7] });
    L.marker([cuenta!.latitud, cuenta!.longitud], { icon }).bindPopup(`<b>${cuenta!.nombre}</b><br>${cuenta!.direccion}`).addTo(leafletAsignacionTabMap);
  }
  if (hasTech) {
    const icon = L.divIcon({ html: `<div style="width:14px;height:14px;background:#58a6ff;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.5);"></div>`, className: '', iconSize: [14,14], iconAnchor: [7,7] });
    L.marker([tech!.latitud_base, tech!.longitud_base], { icon }).bindPopup(`<b>${tech!.nombre}</b><br>Base del técnico`).addTo(leafletAsignacionTabMap);
  }
  if (hasJob && hasTech) {
    const line = L.polyline([[cuenta!.latitud, cuenta!.longitud], [tech!.latitud_base, tech!.longitud_base]], { color: '#58a6ff', weight: 2, dashArray: '6 4', opacity: 0.8 }).addTo(leafletAsignacionTabMap);
    leafletAsignacionTabMap.fitBounds(line.getBounds(), { padding: [40, 40], animate: false });
  }
  nextTick(() => { leafletAsignacionTabMap?.invalidateSize(); });
}

// ── Mapa asignar técnico ─────────────────────────────────────────────────────
function destroyAsignarMap() {
  if (leafletAsignarMap) {
    leafletAsignarMap.stop();
    leafletAsignarMap.remove();
    leafletAsignarMap = null;
    markerTech = null;
    routeLine = null;
  }
}

function initAsignarMap() {
  destroyAsignarMap();
  if (!mapAsignarEl.value) return;
  const rec = recomendacion.value;
  const centerLat = rec?.lat_job || -12.046374;
  const centerLon = rec?.lon_job || -77.042793;

  leafletAsignarMap = L.map(mapAsignarEl.value, { zoomControl: true, attributionControl: false })
    .setView([centerLat, centerLon], 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(leafletAsignarMap);

  if (rec?.lat_job && rec?.lon_job) {
    const jobIcon = L.divIcon({
      html: `<div style="width:14px;height:14px;background:#3fb950;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.5);"></div>`,
      className: '', iconSize: [14, 14], iconAnchor: [7, 7],
    });
    L.marker([rec.lat_job, rec.lon_job], { icon: jobIcon })
      .bindPopup('<b>Ubicación del trabajo</b>')
      .addTo(leafletAsignarMap);
  }

  nextTick(() => { leafletAsignarMap?.invalidateSize(); });
}

function updateAsignarMap(tech: ApiRecomendacionItem | null) {
  if (!leafletAsignarMap) return;
  if (markerTech) { markerTech.remove(); markerTech = null; }
  if (routeLine) { routeLine.remove(); routeLine = null; }
  if (!tech?.latitud_base || !tech?.longitud_base) return;

  const techIcon = L.divIcon({
    html: `<div style="width:14px;height:14px;background:#58a6ff;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.5);"></div>`,
    className: '', iconSize: [14, 14], iconAnchor: [7, 7],
  });
  markerTech = L.marker([tech.latitud_base, tech.longitud_base], { icon: techIcon })
    .bindPopup(`<b>${tech.nombre}</b><br>Base del técnico`)
    .addTo(leafletAsignarMap);

  const rec = recomendacion.value;
  if (rec?.lat_job && rec?.lon_job) {
    routeLine = L.polyline(
      [[rec.lat_job, rec.lon_job], [tech.latitud_base, tech.longitud_base]],
      { color: '#58a6ff', weight: 2, dashArray: '6 4', opacity: 0.8 }
    ).addTo(leafletAsignarMap);
    leafletAsignarMap.fitBounds(routeLine.getBounds(), { padding: [30, 30], animate: false });
  } else {
    leafletAsignarMap.setView([tech.latitud_base, tech.longitud_base], 13, { animate: false });
  }
}

watch(() => modals.asignar, (open) => {
  if (open) nextTick(() => { if (asignarTab.value === 'asignacion') initAsignarMap(); });
  else destroyAsignarMap();
});

watch(asignarTab, (tab) => {
  if (tab === 'asignacion') nextTick(initAsignarMap);
  else destroyAsignarMap();
});

watch(() => af.tecnico_id, (id) => {
  const tech = recomendacion.value?.ranking.find(t => t.id === id) ?? null;
  updateAsignarMap(tech);
});

// ── Cargar datos ───────────────────────────────────────────────────────────
async function load() {
  loading.value = true;
  try { pedidos.value = await listPedidos(); } finally { loading.value = false; }
}

async function selectPedido(id: string) {
  selectedId.value = id;
  activeTab.value = 'info';
  recomendacion.value = null;
  tecnicoAsignado.value = null;
  selected.value = await getPedido(id);
  if (!selected.value.tecnico_asignado_id || selected.value.estado === 'rechazado') {
    getRecomendacion(id).then(r => { recomendacion.value = r; }).catch(() => {});
  }
  if (selected.value.tecnico_asignado_id) {
    getTecnico(selected.value.tecnico_asignado_id).then(t => { tecnicoAsignado.value = t; }).catch(() => {});
  }
}

// ── Crear pedido ───────────────────────────────────────────────────────────
function openCreate() {
  Object.assign(cf, { cliente_id: '', cuenta_id: '', titulo: '', descripcion: '', tipo_servicio: '', zona: '', prioridad: 'media', fecha_programada: '' });
  cuentaPreview.value = null;
  createError.value = '';
  modals.create = true;
}

function onClienteChange() {
  cf.cuenta_id = '';
  cuentaPreview.value = null;
  cf.zona = '';
}

function onCuentaChange() {
  const cuenta = cuentas.value.find(c => c.id === cf.cuenta_id);
  cuentaPreview.value = cuenta || null;
  if (cuenta) cf.zona = cuenta.distrito || '';
}

async function submitCreate() {
  saving.value = true;
  createError.value = '';
  try {
    const body: Record<string, unknown> = {
      cliente_id: cf.cliente_id,
      cuenta_id: cf.cuenta_id || null,
      titulo: cf.titulo,
      descripcion: cf.descripcion,
      tipo_servicio: cf.tipo_servicio,
      zona: cf.zona,
      prioridad: cf.prioridad,
    };
    if (cf.fecha_programada) body.fecha_programada = cf.fecha_programada;
    const p = await apiCreate(body as Partial<ApiPedido>);
    pedidos.value.unshift(p);
    modals.create = false;
    await selectPedido(p.id);
  } catch (e: unknown) {
    createError.value = e instanceof Error ? e.message : 'Error al crear pedido';
  } finally {
    saving.value = false;
  }
}

// ── Asignar / reasignar ────────────────────────────────────────────────────
function openAsignar() {
  af.tecnico_id = '';
  af.epps = [];
  af.materiales = [];
  asignarTab.value = 'asignacion';
  eppSearch.value = '';
  matSearch.value = '';
  asignarError.value = '';
  modals.asignar = true;
  if (selected.value) {
    recomendacion.value = null;
    getRecomendacion(selected.value.id).then(r => { recomendacion.value = r; }).catch(() => {});
  }
}


async function submitAsignar() {
  if (!selected.value || !af.tecnico_id) return;
  actionLoading.value = true;
  asignarError.value = '';
  try {
    let p: ApiPedido;
    if (selected.value.estado === 'rechazado' || selected.value.tecnico_asignado_id) {
      p = await reasignarTecnico(selected.value.id, af.tecnico_id);
    } else {
      p = await asignarTecnico(selected.value.id, af.tecnico_id, af.epps, af.materiales);
    }
    selected.value = p;
    updateList(p);
    modals.asignar = false;
  } catch (e: unknown) {
    asignarError.value = e instanceof Error ? e.message : 'Error al asignar';
  } finally {
    actionLoading.value = false;
  }
}

// ── Completar ──────────────────────────────────────────────────────────────
async function submitCompletar() {
  if (!selected.value) return;
  actionLoading.value = true;
  try {
    const p = await completarPedido(selected.value.id);
    selected.value = p;
    updateList(p);
    modals.completar = false;
  } finally {
    actionLoading.value = false;
  }
}

// ── Dar de baja ────────────────────────────────────────────────────────────
function openBaja() {
  bajaMotivo.value = '';
  bajaError.value = '';
  modals.baja = true;
}

async function submitBaja() {
  if (!selected.value || !bajaMotivo.value.trim()) {
    bajaError.value = 'El motivo es obligatorio.';
    return;
  }
  actionLoading.value = true;
  bajaError.value = '';
  try {
    const p = await darDeBaja(selected.value.id, bajaMotivo.value);
    selected.value = p;
    updateList(p);
    modals.baja = false;
  } catch (e: unknown) {
    bajaError.value = e instanceof Error ? e.message : 'Error';
  } finally {
    actionLoading.value = false;
  }
}

// ── Init ───────────────────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([
    load(),
    listClientes().then(v => { clientes.value = v; }),
    listCuentas().then(v => { cuentas.value = v; }),
    listTecnicos({ activo: true }).then(v => { tecnicos.value = v; }),
    listInventario({ activo: true }).then(v => { inventario.value = v; }),
  ]);
});
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════
   VARIABLES — TEMA OSCURO (default)
═══════════════════════════════════════════════════════ */
.pv.dark {
  --bg:          #0d1117;
  --surface:     #161b22;
  --surface-2:   #21262d;
  --border:      #30363d;
  --border-2:    #3d444d;
  --text-1:      #e6edf3;
  --text-2:      #9198a1;
  --text-3:      #636c76;
  --green:       #3fb950;
  --green-bg:    rgba(63,185,80,0.12);
  --green-dim:   #196127;
  --green-hover: #2ea043;
  --red:         #f85149;
  --red-bg:      rgba(248,81,73,0.12);
  --yellow:      #d29922;
  --yellow-bg:   rgba(210,153,34,0.12);
  --blue:        #58a6ff;
  --blue-bg:     rgba(88,166,255,0.12);
  --purple:      #bc8cff;
  --shadow:      0 8px 24px rgba(0,0,0,0.4);
}

/* ═══════════════════════════════════════════════════════
   VARIABLES — TEMA CLARO
═══════════════════════════════════════════════════════ */
.pv.light {
  --bg:          #f6f8fa;
  --surface:     #ffffff;
  --surface-2:   #f6f8fa;
  --border:      #d0d7de;
  --border-2:    #c6cdd4;
  --text-1:      #1f2328;
  --text-2:      #59636e;
  --text-3:      #818b98;
  --green:       #1a7f37;
  --green-bg:    rgba(26,127,55,0.1);
  --green-dim:   #dafbe1;
  --green-hover: #116329;
  --red:         #d1242f;
  --red-bg:      rgba(209,36,47,0.1);
  --yellow:      #9a6700;
  --yellow-bg:   rgba(154,103,0,0.1);
  --blue:        #0969da;
  --blue-bg:     rgba(9,105,218,0.1);
  --purple:      #8250df;
  --shadow:      0 1px 3px rgba(31,35,40,0.12);
}

/* ═══════════════════════════════════════════════════════
   LAYOUT BASE
═══════════════════════════════════════════════════════ */
.pv {
  display: grid;
  grid-template-columns: 300px 1fr;
  height: 100%;
  background: var(--bg);
  color: var(--text-1);
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 13px;
  border: 1px solid var(--border);
}

/* ═══════════════════════════════════════════════════════
   SIDEBAR
═══════════════════════════════════════════════════════ */
.pv-sidebar {
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--surface);
}

.sidebar-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  gap: 8px;
}

.sidebar-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sidebar-icon {
  color: var(--green);
  line-height: 1;
  display: flex;
  align-items: center;
}

.sidebar-title h2 {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--text-1);
}

.sidebar-controls {
  display: flex;
  gap: 6px;
  align-items: center;
}

.sidebar-filters {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-input {
  width: 100%;
  padding: 6px 10px;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text-1);
  font-size: 12px;
  outline: none;
  transition: border-color 0.15s;
}
.filter-input:focus { border-color: var(--green); }

.filter-row { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }

.filter-select {
  padding: 5px 8px;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text-1);
  font-size: 11px;
  width: 100%;
  outline: none;
}

.filter-stats {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-3);
  padding: 0 2px;
}

.stat-alert { color: var(--red); font-weight: 600; }

.sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.list-empty {
  padding: 24px;
  text-align: center;
  color: var(--text-3);
  font-size: 12px;
}

.list-item {
  width: 100%;
  text-align: left;
  padding: 10px 11px;
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-1);
  cursor: pointer;
  transition: all 0.1s;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.list-item:hover { background: var(--surface-2); border-color: var(--border); }
.list-item.active { background: var(--green-bg); border-color: var(--green); }
.list-item.alerta { border-left: 2px solid var(--red) !important; }

.item-header { display: flex; justify-content: space-between; align-items: center; }
.item-ot { font-size: 11px; font-weight: 700; letter-spacing: 0.05em; color: var(--green); }
.item-cliente { font-size: 12px; color: var(--text-2); }
.item-titulo {
  font-size: 12px;
  color: var(--text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2px;
}
.item-fase { font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.05em; }
.item-rechazo-flag {
  font-size: 10px;
  color: var(--red);
  font-weight: 700;
  letter-spacing: 0.03em;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* ═══════════════════════════════════════════════════════
   MAIN PANEL
═══════════════════════════════════════════════════════ */
.pv-main {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg);
}

.main-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: var(--text-3);
}
.empty-glyph { color: var(--border-2); }

/* Topbar */
.detail-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  flex-wrap: wrap;
  gap: 8px;
  flex-shrink: 0;
}
.topbar-left { display: flex; align-items: center; gap: 8px; overflow: hidden; }
.topbar-ot { font-size: 13px; font-weight: 700; color: var(--green); letter-spacing: 0.05em; white-space: nowrap; }
.topbar-sep { color: var(--border-2); }
.topbar-titulo { font-size: 13px; color: var(--text-2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.topbar-right { display: flex; gap: 6px; align-items: center; flex-shrink: 0; }
.topbar-cost {
  font-size: 13px;
  font-weight: 700;
  color: var(--green);
  padding: 2px 8px;
  border: 1px solid var(--green);
  background: var(--green-bg);
  letter-spacing: 0.02em;
  white-space: nowrap;
}

/* Phase rail */
.phase-rail {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.phase-step {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  position: relative;
}
.phase-num {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  border: 1px solid var(--border-2);
  color: var(--text-3);
  flex-shrink: 0;
}
.phase-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-3);
  letter-spacing: 0.06em;
  white-space: nowrap;
}
.phase-step.done .phase-num    { background: var(--green); border-color: var(--green); color: #fff; }
.phase-step.done .phase-label  { color: var(--green); }
.phase-step.active .phase-num  { background: var(--green-bg); border-color: var(--green); color: var(--green); }
.phase-step.active .phase-label { color: var(--text-1); font-weight: 700; }
.phase-connector {
  flex: 1;
  height: 1px;
  background: var(--border);
  margin: 0 8px;
}
.phase-step.done .phase-connector { background: var(--green); }

/* CTA principal — destacado, primero en el panel */
.main-cta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  gap: 16px;
}
.cta-assign  { background: var(--blue-bg);   border-left: 4px solid var(--blue);   }
.cta-warn    { background: var(--red-bg);    border-left: 4px solid var(--red);    }
.cta-complete { background: var(--green-bg); border-left: 4px solid var(--green); }
.cta-info { display: flex; flex-direction: column; gap: 4px; }
.cta-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--text-3);
}
.cta-assign  .cta-label { color: var(--blue); }
.cta-warn    .cta-label { color: var(--red); }
.cta-complete .cta-label { color: var(--green); }
.cta-desc  { font-size: 13px; color: var(--text-1); font-weight: 500; }
.cta-btn {
  padding: 10px 24px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  border: none;
  background: var(--green);
  color: #fff;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.1s;
  flex-shrink: 0;
}
.cta-assign  .cta-btn { background: var(--blue); }
.cta-warn    .cta-btn { background: var(--red); }
.cta-complete .cta-btn { background: var(--green); }
.cta-btn:hover { opacity: 0.85; }
.cta-btn:disabled { opacity: 0.45; cursor: not-allowed; }

/* Cost bar */
.cost-bar {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 8px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  flex-shrink: 0;
}
.cost-item { display: flex; flex-direction: column; align-items: center; padding: 0 16px; }
.cost-lbl { font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; }
.cost-val { font-size: 14px; font-weight: 700; color: var(--text-1); }
.cost-total .cost-val { color: var(--green); font-size: 16px; }
.cost-sep { color: var(--text-3); padding: 0 4px; font-size: 16px; }

/* Tabs */
.tabs-bar {
  display: flex;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  flex-shrink: 0;
  overflow-x: auto;
}
.tab {
  padding: 10px 16px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: var(--text-2);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.1s;
}
.tab:hover { color: var(--text-1); }
.tab.active { color: var(--green); border-bottom-color: var(--green); }

/* Tab content */
.tab-panel {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.info-card {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.info-card-title {
  margin: 0;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--text-3);
  border-bottom: 1px solid var(--border);
  padding-bottom: 8px;
}
.info-card-title.mt { margin-top: 12px; }
.info-card-title.rechazo-title { color: var(--red); border-color: var(--red-bg); }
.info-body { margin: 0; font-size: 13px; color: var(--text-2); line-height: 1.6; }
.rechazo-body { color: var(--red); }
.info-none { color: var(--text-3); font-style: italic; margin: 0; font-size: 12px; }

.info-dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 6px 12px;
  margin: 0;
  font-size: 12px;
}
.info-dl dt {
  color: var(--text-3);
  font-weight: 600;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
}
.info-dl dd { margin: 0; color: var(--text-1); }

/* Badges especiales en info-dl */
.phase-badge {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--green);
  text-transform: uppercase;
}
.code-text {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  font-weight: 700;
  color: var(--blue);
  letter-spacing: 0.04em;
}
.zona-ref {
  font-style: italic;
  color: var(--text-2);
}

/* Description block */
.info-desc-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-left: 3px solid var(--green);
}
.info-desc-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--text-3);
}
.rechazo-block { border-left-color: var(--red); }
.rechazo-block .info-desc-label { color: var(--red); }

/* Informe técnico al fondo del tab info */
.info-informe {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* ── Cuenta card ── */
.cuenta-card { overflow: hidden; }

.cuenta-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 10px;
  background: var(--surface-2);
  border: 1px solid var(--border);
}
.cuenta-header-left {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.cuenta-icon { color: var(--green); flex-shrink: 0; margin-top: 2px; }
.cuenta-nombre {
  display: block;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-1);
  line-height: 1.3;
}
.cuenta-numero {
  display: block;
  font-size: 11px;
  color: var(--text-3);
  margin-top: 2px;
}
.cuenta-tipo-badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 3px 8px;
  background: var(--blue-bg);
  color: var(--blue);
  border: 1px solid var(--blue);
  white-space: nowrap;
  text-transform: uppercase;
  flex-shrink: 0;
}

/* ── Mapa ── */
.map-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0;
  border: 1px solid var(--border);
  overflow: hidden;
}
.map-container {
  height: 200px;
  width: 100%;
  background: var(--surface-2);
}
.map-coords {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  background: var(--surface-2);
  border-top: 1px solid var(--border);
  font-size: 10px;
  font-family: 'Courier New', monospace;
  color: var(--text-3);
}
.map-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 100px;
  color: var(--text-3);
  background: var(--bg);
  border: 1px dashed var(--border-2);
  font-size: 12px;
}

.cuenta-dl { margin-top: 4px; }

/* Checklist */
.checklist { display: flex; flex-direction: column; gap: 6px; }
.check-row {
  display: flex;
  gap: 10px;
  padding: 8px 10px;
  border: 1px solid var(--border);
  background: var(--bg);
}
.check-row.done { border-color: var(--green); background: var(--green-bg); }
.check-mark { color: var(--text-3); flex-shrink: 0; line-height: 1.4; display: flex; align-items: center; }
.check-row.done .check-mark { color: var(--green); }
.check-body { display: flex; flex-direction: column; gap: 2px; }
.check-body strong { font-size: 12px; color: var(--text-1); }
.check-nota { font-size: 11px; color: var(--text-2); font-style: italic; }
.check-fecha { font-size: 11px; color: var(--text-3); }

/* Evidencias */
.ev-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 8px; }
.ev-item { border: 1px solid var(--border); overflow: hidden; }
.ev-item img { width: 100%; height: 90px; object-fit: cover; display: block; }
.ev-caption { padding: 6px; display: flex; flex-direction: column; gap: 3px; }
.ev-stage { font-size: 10px; font-weight: 700; letter-spacing: 0.06em; }
.stage-antes { color: var(--yellow); }
.stage-despues { color: var(--green); }
.ev-caption span:not(.ev-stage) { font-size: 10px; color: var(--text-3); }

/* Data table */
.data-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.data-table.mt { margin-top: 12px; }
.data-table th {
  padding: 6px 10px;
  text-align: left;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--text-3);
  border-bottom: 1px solid var(--border);
  background: var(--surface-2);
}
.data-table td { padding: 7px 10px; border-bottom: 1px solid var(--border); color: var(--text-2); }
.data-table tr:hover td { background: var(--surface-2); }
.total-row td { font-weight: 700; color: var(--text-1); border-top: 1px solid var(--border-2); }

/* Grand total */
.grand-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  margin-top: 8px;
  border: 1px solid var(--green);
  background: var(--green-bg);
}
.grand-total span { font-size: 11px; font-weight: 700; letter-spacing: 0.1em; color: var(--text-2); }
.grand-total strong { font-size: 18px; font-weight: 700; color: var(--green); }

/* Tab action bar */
.tab-action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border: 1px solid var(--border);
  background: var(--surface);
  gap: 12px;
}
.tab-action-info {
  font-size: 12px;
  color: var(--text-2);
}
.tab-action-info strong { color: var(--text-1); }
.action-warn { color: var(--red); font-weight: 600; }

.btn-assign {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
  background: var(--green);
  color: #fff;
  border: none;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.1s;
  flex-shrink: 0;
}
.btn-assign:hover { background: var(--green-hover); }

/* Rechazo log */
.rechazo-log {
  background: var(--red-bg);
  border: 1px solid var(--red);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.rechazo-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  font-size: 12px;
  align-items: center;
}
.rechazo-quien { font-weight: 600; color: var(--red); }
.rechazo-motivo { color: var(--text-1); }
.rechazo-fecha { color: var(--text-3); white-space: nowrap; }

/* Técnico card */
.tecnico-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  background: var(--bg);
  border: 1px solid var(--border);
}
.tecnico-avatar {
  width: 36px;
  height: 36px;
  background: var(--green);
  color: #fff;
  font-weight: 700;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.tecnico-card strong { font-size: 13px; color: var(--text-1); }

/* Timeline */
.timeline {
  display: flex;
  flex-direction: column;
  max-width: 720px;
  width: 100%;
  margin: 0 auto;
  padding: 8px 0 24px;
}
.tl-row {
  display: grid;
  grid-template-columns: 14px 2px 1fr;
  gap: 0 18px;
  padding: 0;
}
.tl-marker {
  width: 14px;
  height: 14px;
  background: var(--green);
  border-radius: 50%;
  margin-top: 5px;
  flex-shrink: 0;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--green) 20%, transparent);
}
.ev-completado { background: var(--green); box-shadow: 0 0 0 3px color-mix(in srgb, var(--green) 20%, transparent); }
.ev-rechazo    { background: var(--red);   box-shadow: 0 0 0 3px color-mix(in srgb, var(--red)   20%, transparent); }
.ev-baja       { background: var(--text-3); box-shadow: none; }
.ev-asignacion { background: var(--blue);  box-shadow: 0 0 0 3px color-mix(in srgb, var(--blue)  20%, transparent); }
.tl-line { width: 2px; background: var(--border); min-height: 100%; }
.tl-body { display: flex; flex-direction: column; gap: 4px; padding-bottom: 28px; padding-top: 2px; }
.tl-evento { font-size: 13px; font-weight: 700; color: var(--text-1); }
.tl-detalle { font-size: 12px; color: var(--text-2); line-height: 1.5; }
.tl-meta { font-size: 11px; color: var(--text-3); }

/* Footer */
.detail-footer {
  padding: 10px 16px;
  border-top: 1px solid var(--border);
  background: var(--surface);
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}

/* ═══════════════════════════════════════════════════════
   BADGES
═══════════════════════════════════════════════════════ */
.badge-pri, .item-pri {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 2px 6px;
}
.pri-baja    { background: var(--surface-2); color: var(--text-3); border: 1px solid var(--border); }
.pri-media   { background: var(--yellow-bg); color: var(--yellow); border: 1px solid var(--yellow); }
.pri-alta    { background: rgba(255,130,0,0.12); color: #f08500; border: 1px solid #f08500; }
.pri-critica { background: var(--red-bg); color: var(--red); border: 1px solid var(--red); }

.badge-estado, .item-estado {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  letter-spacing: 0.04em;
}
.est-por-confirmar { background: var(--blue-bg);   color: var(--blue);   border: 1px solid var(--blue);   }
.est-confirmado    { background: var(--green-bg);  color: var(--green);  border: 1px solid var(--green);  }
.est-rechazado     { background: var(--red-bg);    color: var(--red);    border: 1px solid var(--red);    }
.est-en-labor      { background: var(--blue-bg);   color: var(--blue);   border: 1px solid var(--blue);   }
.est-cierre-tecnico { background: rgba(188,140,255,0.12); color: var(--purple); border: 1px solid var(--purple); }
.est-completado    { background: var(--green-bg);  color: var(--green);  border: 1px solid var(--green);  }
.est-dado-de-baja  { background: var(--surface-2); color: var(--text-3); border: 1px solid var(--border); }

/* ═══════════════════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════════════════ */
.btn-create {
  padding: 5px 12px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  background: var(--green);
  color: #fff;
  border: none;
  cursor: pointer;
  transition: background 0.1s;
  display: flex;
  align-items: center;
  gap: 4px;
}
.btn-create:hover { background: var(--green-hover); }

.icon-btn {
  padding: 4px 8px;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-2);
  cursor: pointer;
  font-size: 12px;
  transition: all 0.1s;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.icon-btn:hover { border-color: var(--green); color: var(--green); }

.btn-green {
  padding: 7px 16px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
  background: var(--green);
  color: #fff;
  border: none;
  cursor: pointer;
  transition: background 0.1s;
}
.btn-green:hover { background: var(--green-hover); }
.btn-green:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-green.btn-xs { padding: 4px 10px; font-size: 11px; }

.btn-ghost {
  padding: 7px 16px;
  font-size: 12px;
  font-weight: 600;
  background: transparent;
  color: var(--text-2);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.1s;
}
.btn-ghost:hover { border-color: var(--text-2); color: var(--text-1); }
.btn-ghost.btn-xs { padding: 4px 10px; font-size: 11px; }

.btn-danger {
  padding: 7px 16px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
  background: var(--red);
  color: #fff;
  border: none;
  cursor: pointer;
  transition: opacity 0.1s;
}
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-danger-ghost {
  padding: 6px 14px;
  font-size: 11px;
  font-weight: 600;
  background: transparent;
  color: var(--red);
  border: 1px solid var(--red);
  cursor: pointer;
  transition: all 0.1s;
  letter-spacing: 0.04em;
  display: flex;
  align-items: center;
  gap: 6px;
}
.btn-danger-ghost:hover { background: var(--red-bg); }

.btn-remove {
  padding: 2px 6px;
  background: var(--red-bg);
  color: var(--red);
  border: none;
  cursor: pointer;
  font-size: 11px;
  display: flex;
  align-items: center;
}

/* ═══════════════════════════════════════════════════════
   MODALS
═══════════════════════════════════════════════════════ */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.modal {
  background: var(--surface);
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
  max-width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--surface-2);
  flex-shrink: 0;
}
.modal-head h3 {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--text-1);
}

.modal-body {
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
  margin-top: 4px;
  flex-wrap: wrap;
}

/* Form */
.form-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.form-section-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--text-3);
  border-bottom: 1px solid var(--border);
  padding-bottom: 6px;
  margin: 0;
}
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.form-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: var(--text-2);
}
.form-field.wide { grid-column: 1 / -1; }
.form-field span { font-weight: 600; font-size: 11px; letter-spacing: 0.04em; }
.form-field small { color: var(--text-3); font-style: italic; font-weight: 400; }
.form-field input,
.form-field select,
.form-field textarea {
  padding: 7px 9px;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text-1);
  font-size: 12px;
  outline: none;
  font-family: inherit;
  transition: border-color 0.15s;
}
.form-field input:focus,
.form-field select:focus,
.form-field textarea:focus { border-color: var(--green); }
.form-field input:disabled,
.form-field select:disabled { opacity: 0.5; cursor: not-allowed; }
.form-field textarea { resize: vertical; }

.form-error { font-size: 11px; color: var(--red); margin: 0; flex: 1; }

/* Cuenta preview */
.cuenta-preview {
  background: var(--green-bg);
  border: 1px solid var(--green);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.preview-row {
  display: flex;
  gap: 12px;
  font-size: 12px;
}
.preview-row span { color: var(--text-3); font-weight: 600; min-width: 80px; font-size: 11px; }
.preview-row strong { color: var(--text-1); }

/* Recommendation banner */
.rec-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--blue-bg);
  border: 1px solid var(--blue);
  font-size: 12px;
  flex-wrap: wrap;
}
.rec-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--blue);
  background: var(--blue-bg);
  padding: 2px 6px;
  border: 1px solid var(--blue);
}
.rec-banner strong { color: var(--text-1); }
.rec-banner span { color: var(--text-2); }

/* Item adder */
.item-adder { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.adder-select {
  flex: 1;
  min-width: 200px;
  padding: 6px 8px;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text-1);
  font-size: 12px;
}
.adder-qty {
  width: 70px;
  padding: 6px 8px;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text-1);
  font-size: 12px;
}

.confirm-text {
  font-size: 13px;
  color: var(--text-2);
  line-height: 1.6;
  margin: 0;
}
.confirm-text strong { color: var(--text-1); }

/* ═══════════════════════════════════════════════════════
   TAB ASIGNACIÓN — detalle del pedido
═══════════════════════════════════════════════════════ */
.asig-cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.tec-perfil {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  background: var(--bg);
  border: 1px solid var(--border);
  margin-bottom: 10px;
}
.tec-perfil-avatar {
  width: 40px;
  height: 40px;
  background: var(--green);
  color: #fff;
  font-weight: 700;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  text-transform: uppercase;
}
.tec-perfil-data {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.tec-perfil-nombre {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-1);
}
.asig-ruta-card {
  padding: 0;
  overflow: hidden;
}
.asig-ruta-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
}
.ruta-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 11px;
}
.asig-ruta-map {
  height: 260px;
  width: 100%;
  background: var(--surface-2);
}

/* ═══════════════════════════════════════════════════════
   MODAL ASIGNAR TÉCNICO
═══════════════════════════════════════════════════════ */
.modal-asignar {
  width: 960px;
  height: 640px;
}

/* Tab bar inside modal */
.modal-tabs-bar {
  display: flex;
  border-bottom: 1px solid var(--border);
  background: var(--surface-2);
  flex-shrink: 0;
}
.modal-tab {
  padding: 9px 18px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--text-2);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.1s;
  display: flex;
  align-items: center;
  gap: 6px;
}
.modal-tab:hover { color: var(--text-1); }
.modal-tab.active { color: var(--green); border-bottom-color: var(--green); }

.modal-tab-badge {
  font-size: 9px;
  font-weight: 700;
  background: var(--green);
  color: #fff;
  padding: 1px 5px;
  min-width: 16px;
  text-align: center;
}

/* Static footer (outside tab content so it's always visible) */
.modal-footer-static {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-top: 1px solid var(--border);
  background: var(--surface);
  flex-shrink: 0;
  flex-wrap: wrap;
}

/* Asignación tab layout */
.asignar-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.asignar-panel {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Tech ranking list */
.tech-list {
  width: 310px;
  flex-shrink: 0;
  overflow-y: auto;
  border-right: 1px solid var(--border);
  background: var(--bg);
  display: flex;
  flex-direction: column;
}
.tech-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 9px 14px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--text-3);
}
.tech-count {
  font-size: 10px;
  font-weight: 700;
  background: var(--surface-2);
  color: var(--text-2);
  padding: 2px 6px;
  border: 1px solid var(--border);
}
.tech-loading {
  padding: 24px;
  text-align: center;
  color: var(--text-3);
  font-size: 12px;
}

/* Tech card */
.tech-card {
  position: relative;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.1s;
  display: flex;
  flex-direction: column;
  gap: 7px;
}
.tech-card:hover { background: var(--surface-2); }
.tech-card.selected { background: var(--green-bg); border-left: 3px solid var(--green); }

.tech-card-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.tech-avatar {
  width: 32px;
  height: 32px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  color: var(--text-1);
  font-weight: 700;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  text-transform: uppercase;
}
.tech-card.selected .tech-avatar { background: var(--green); color: #fff; border-color: var(--green); }

.tech-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
  padding-right: 4px;
}
.tech-nombre {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tech-meta {
  font-size: 10px;
  color: var(--text-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Score circle */
.tech-score-circle {
  width: 42px;
  height: 42px;
  border: 2px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--bg);
}
.tech-score-circle.score-high { border-color: var(--green); }
.tech-score-circle.score-mid  { border-color: var(--yellow); }
.tech-score-circle.score-low  { border-color: var(--red); }
.score-num { font-size: 13px; font-weight: 700; line-height: 1; color: var(--text-1); }
.score-pct { font-size: 9px; color: var(--text-3); line-height: 1; }
.score-high .score-num { color: var(--green); }
.score-mid  .score-num { color: var(--yellow); }
.score-low  .score-num { color: var(--red); }

/* Score bar */
.tech-score-bar {
  height: 3px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  overflow: hidden;
}
.score-bar-fill {
  height: 100%;
  transition: width 0.4s ease;
  background: var(--text-3);
}
.score-bar-fill.score-high { background: var(--green); }
.score-bar-fill.score-mid  { background: var(--yellow); }
.score-bar-fill.score-low  { background: var(--red); }

/* Stats row */
.tech-card-stats {
  display: flex;
  gap: 10px;
  font-size: 10px;
  color: var(--text-3);
  flex-wrap: wrap;
  align-items: center;
}
.tech-stat { display: flex; align-items: center; gap: 3px; }
.match-yes { color: var(--green); }
.match-no  { color: var(--text-3); }

/* Nombre + SUGERIDO inline */
.tech-nombre-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.tech-sugerido-badge {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--green);
  background: var(--green-bg);
  border: 1px solid var(--green);
  padding: 1px 5px;
  flex-shrink: 0;
}

/* Map panel */
.asignar-map-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}
.map-legend {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 8px 14px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  font-size: 11px;
  flex-shrink: 0;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-2);
}
.legend-item::before {
  content: '';
  display: inline-block;
  width: 10px;
  height: 10px;
  flex-shrink: 0;
}
.legend-job::before  { background: #3fb950; }
.legend-tech::before { background: #58a6ff; }
.legend-dist {
  margin-left: auto;
  font-weight: 600;
  color: var(--blue);
  font-size: 12px;
}
.map-asignar-container {
  flex: 1;
  background: var(--surface-2);
  min-height: 0;
}
.map-hint {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(13, 17, 23, 0.88);
  color: #e6edf3;
  padding: 7px 16px;
  font-size: 11px;
  white-space: nowrap;
  pointer-events: none;
  letter-spacing: 0.04em;
  border: 1px solid rgba(255,255,255,0.1);
  z-index: 1000;
}

/* ═══════════════════════════════════════════════════════
   INVENTARIO SELECTOR (tabs EPP / Material)
═══════════════════════════════════════════════════════ */
.inv-tab-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.inv-split {
  flex: 1;
  display: flex;
  overflow: hidden;
}
.inv-catalog {
  width: 55%;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.inv-search-wrap {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  flex-shrink: 0;
}
.inv-search {
  width: 100%;
  padding: 6px 10px;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text-1);
  font-size: 12px;
  outline: none;
  box-sizing: border-box;
}
.inv-search:focus { border-color: var(--green); }
.inv-items-list {
  flex: 1;
  overflow-y: auto;
}
.inv-empty {
  padding: 16px;
  text-align: center;
  color: var(--text-3);
  font-size: 12px;
}
.inv-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.1s;
}
.inv-item:hover { background: var(--surface-2); }
.inv-item-info { display: flex; flex-direction: column; gap: 2px; flex: 1; overflow: hidden; }
.inv-item-name { font-size: 12px; color: var(--text-1); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.inv-item-meta { font-size: 10px; color: var(--text-3); }
.inv-item-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.inv-stock { font-size: 10px; color: var(--text-3); }
.inv-add-btn {
  width: 24px; height: 24px;
  background: var(--green);
  color: #fff;
  border: none;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.1s;
}
.inv-add-btn:hover { background: var(--green-hover); }

.inv-cart {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.inv-cart-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 14px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--text-3);
}
.inv-cart .data-table { font-size: 12px; }
.inv-cart .data-table td { vertical-align: middle; }

.qty-ctrl {
  display: flex;
  align-items: center;
  gap: 6px;
}
.qty-ctrl button {
  width: 20px; height: 20px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  color: var(--text-1);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.qty-ctrl button:hover { border-color: var(--green); color: var(--green); }
.qty-ctrl span { font-size: 12px; font-weight: 600; min-width: 20px; text-align: center; color: var(--text-1); }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-2); }
::-webkit-scrollbar-thumb:hover { background: var(--text-3); }
</style>

<!-- Global: Leaflet styles + modal theme vars (teleported elements can't inherit scoped vars) -->
<style>
/* Leaflet */
.leaflet-container { font-family: 'Segoe UI', system-ui, sans-serif; }
.leaflet-popup-content-wrapper { border-radius: 0 !important; font-size: 12px; }
.leaflet-popup-tip { display: none; }

/* Modal theme vars — applied to Teleport overlays so CSS vars cascade to modal content */
.pv-modal-dark {
  --bg:          #0d1117;
  --surface:     #161b22;
  --surface-2:   #21262d;
  --border:      #30363d;
  --border-2:    #3d444d;
  --text-1:      #e6edf3;
  --text-2:      #9198a1;
  --text-3:      #636c76;
  --green:       #3fb950;
  --green-bg:    rgba(63,185,80,0.12);
  --green-hover: #2ea043;
  --red:         #f85149;
  --red-bg:      rgba(248,81,73,0.12);
  --yellow:      #d29922;
  --yellow-bg:   rgba(210,153,34,0.12);
  --blue:        #58a6ff;
  --blue-bg:     rgba(88,166,255,0.12);
  --purple:      #bc8cff;
  --shadow:      0 8px 24px rgba(0,0,0,0.4);
}
.pv-modal-light {
  --bg:          #f6f8fa;
  --surface:     #ffffff;
  --surface-2:   #f6f8fa;
  --border:      #d0d7de;
  --border-2:    #c6cdd4;
  --text-1:      #1f2328;
  --text-2:      #59636e;
  --text-3:      #818b98;
  --green:       #1a7f37;
  --green-bg:    rgba(26,127,55,0.1);
  --green-hover: #116329;
  --red:         #d1242f;
  --red-bg:      rgba(209,36,47,0.1);
  --yellow:      #9a6700;
  --yellow-bg:   rgba(154,103,0,0.1);
  --blue:        #0969da;
  --blue-bg:     rgba(9,105,218,0.1);
  --purple:      #8250df;
  --shadow:      0 1px 3px rgba(31,35,40,0.12);
}
</style>
