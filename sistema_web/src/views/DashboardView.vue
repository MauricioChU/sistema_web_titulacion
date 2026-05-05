<template>
  <div class="dash-root">
    <!-- ── Header ─────────────────────────────────────────────────────── -->
    <header class="dash-header">
      <div>
        <h2 class="dash-title">Dashboard</h2>
        <p class="dash-sub">Resumen operativo en tiempo real · PROINTEL</p>
      </div>
      <div class="dash-header-right">
        <span v-if="lastUpdated" class="refresh-tag">
          Actualizado {{ lastUpdatedLabel }}
        </span>
        <button class="btn-refresh" :disabled="loading" type="button" @click="load">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
          Refrescar
        </button>
      </div>
    </header>

    <!-- ── Error state ─────────────────────────────────────────────────── -->
    <div v-if="error && !loading" class="error-banner">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      {{ error }}
      <button type="button" @click="load">Reintentar</button>
    </div>

    <!-- ── Loading skeleton ────────────────────────────────────────────── -->
    <template v-if="loading && !data">
      <div class="kpi-grid">
        <div v-for="i in 4" :key="i" class="skeleton-kpi"></div>
      </div>
      <div class="charts-row">
        <div class="skeleton-chart"></div>
        <div class="skeleton-chart"></div>
      </div>
      <div class="charts-row">
        <div class="skeleton-chart tall"></div>
        <div class="skeleton-chart tall"></div>
      </div>
    </template>

    <!-- ── Main content ────────────────────────────────────────────────── -->
    <template v-if="data">
      <!-- Row 1: KPI cards -->
      <div class="kpi-grid">
        <article class="kpi-card kpi-blue">
          <div class="kpi-icon">📋</div>
          <div class="kpi-body">
            <p class="kpi-label">Pedidos activos</p>
            <p class="kpi-value">{{ data.kpis.pedidos_activos }}</p>
            <p class="kpi-sub">de {{ data.kpis.total_pedidos }} totales</p>
          </div>
          <div class="kpi-accent blue"></div>
        </article>

        <article class="kpi-card kpi-red">
          <div class="kpi-icon">🚨</div>
          <div class="kpi-body">
            <p class="kpi-label">Críticos activos</p>
            <p class="kpi-value kpi-danger">{{ data.kpis.criticos_activos }}</p>
            <p class="kpi-sub">prioridad crítica</p>
          </div>
          <div class="kpi-accent red"></div>
        </article>

        <article class="kpi-card kpi-amber">
          <div class="kpi-icon">👤</div>
          <div class="kpi-body">
            <p class="kpi-label">Sin técnico</p>
            <p class="kpi-value kpi-warning">{{ data.kpis.sin_tecnico }}</p>
            <p class="kpi-sub">requieren asignación</p>
          </div>
          <div class="kpi-accent amber"></div>
        </article>

        <article class="kpi-card kpi-green">
          <div class="kpi-icon">✅</div>
          <div class="kpi-body">
            <p class="kpi-label">Tasa cierre 7d</p>
            <p class="kpi-value kpi-success">{{ data.kpis.tasa_cierre_7d.toFixed(1) }}%</p>
            <p class="kpi-sub">{{ data.kpis.tecnicos_activos }} técnicos activos</p>
          </div>
          <div class="kpi-accent green"></div>
        </article>
      </div>

      <!-- Row 2: Doughnut + Line chart -->
      <div class="charts-row">
        <article class="chart-card">
          <h4 class="chart-title">Pedidos por estado</h4>
          <div class="chart-wrap pie-wrap">
            <Doughnut :data="estadoChartData" :options="doughnutOptions" />
          </div>
        </article>

        <article class="chart-card">
          <h4 class="chart-title">Tendencia 7 días</h4>
          <div class="chart-wrap">
            <Line :data="tendenciaChartData" :options="lineOptions" />
          </div>
        </article>
      </div>

      <!-- Row 3: Leaflet map + Bar chart -->
      <div class="charts-row">
        <article class="chart-card map-card">
          <h4 class="chart-title">
            Pedidos activos · Mapa
            <span class="legend-row">
              <span class="legend-dot" style="background:#dc2626;"></span>Crítica
              <span class="legend-dot" style="background:#f97316;"></span>Alta
              <span class="legend-dot" style="background:#3b82f6;"></span>Media
              <span class="legend-dot" style="background:#22c55e;"></span>Baja
            </span>
          </h4>
          <div id="prointel-map" class="leaflet-container"></div>
        </article>

        <article class="chart-card">
          <h4 class="chart-title">Carga por técnico</h4>
          <div class="chart-wrap">
            <Bar :data="tecnicoChartData" :options="barOptions" />
          </div>
        </article>
      </div>

      <!-- Row 4: Alertas + Actividad reciente -->
      <div class="charts-row">
        <article class="chart-card alerts-card">
          <h4 class="chart-title alert-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            Alertas · Pedidos críticos
          </h4>
          <div class="alerts-list">
            <div v-if="data.alertas.length === 0" class="empty-state">
              <span>✓</span> Sin pedidos críticos pendientes
            </div>
            <div
              v-for="alerta in data.alertas"
              :key="alerta.id"
              class="alert-row"
              :class="alertClass(alerta.prioridad)"
            >
              <div class="alert-badge" :style="{ background: prioridadColor(alerta.prioridad) }">
                {{ alerta.prioridad.toUpperCase().slice(0, 3) }}
              </div>
              <div class="alert-meta">
                <p class="alert-code">{{ alerta.codigo }}</p>
                <p class="alert-titulo">{{ alerta.titulo }}</p>
                <p class="alert-detail">{{ alerta.cliente_nombre }} · {{ alerta.zona }}</p>
              </div>
              <div class="alert-time">{{ timeAgo(alerta.created_at) }}</div>
            </div>
          </div>
        </article>

        <article class="chart-card timeline-card">
          <h4 class="chart-title">Actividad reciente</h4>
          <div class="timeline">
            <div v-if="data.actividad_reciente.length === 0" class="empty-state">
              Sin actividad reciente
            </div>
            <div
              v-for="(act, idx) in data.actividad_reciente.slice(0, 8)"
              :key="idx"
              class="timeline-item"
            >
              <div class="tl-dot"></div>
              <div class="tl-body">
                <p class="tl-main">
                  <strong>{{ act.codigo }}</strong> · {{ act.evento }}
                </p>
                <p class="tl-detail">{{ act.detalle }}</p>
                <p class="tl-meta">{{ act.usuario }} · {{ timeAgo(act.at) }}</p>
              </div>
            </div>
          </div>
        </article>
      </div>

      <!-- Row 5: Costs -->
      <article class="costs-card">
        <div class="costs-header">
          <h4 class="chart-title">Costos del mes</h4>
          <span class="costs-total">Total: <strong>S/ {{ fmt(data.costos_mes.total) }}</strong></span>
        </div>
        <div class="costs-grid">
          <div class="cost-item">
            <div class="cost-icon" style="background:#dbeafe; color:#1d4ed8;">🦺</div>
            <div>
              <p class="cost-label">EPPs</p>
              <p class="cost-value">S/ {{ fmt(data.costos_mes.total_epps) }}</p>
            </div>
          </div>
          <div class="cost-item">
            <div class="cost-icon" style="background:#fef3c7; color:#d97706;">🔧</div>
            <div>
              <p class="cost-label">Materiales</p>
              <p class="cost-value">S/ {{ fmt(data.costos_mes.total_materiales) }}</p>
            </div>
          </div>
          <div class="cost-item cost-item-total">
            <div class="cost-icon" style="background:#dcfce7; color:#16a34a;">💰</div>
            <div>
              <p class="cost-label">Total acumulado</p>
              <p class="cost-value cost-total-val">S/ {{ fmt(data.costos_mes.total) }}</p>
            </div>
          </div>
        </div>
      </article>
    </template>
  </div>
</template>

<script setup lang="ts">
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  type ChartOptions,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
} from 'chart.js';
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { Bar, Doughnut, Line } from 'vue-chartjs';
import * as L from 'leaflet';
import { getDashboard, type DashboardData } from '../api/dashboard';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  LineElement,
  PointElement,
  Filler,
  Title,
  Tooltip,
  Legend,
);

// ── State ─────────────────────────────────────────────────────────────────────
const data = ref<DashboardData | null>(null);
const loading = ref(false);
const error = ref('');
const lastUpdated = ref<Date | null>(null);
let refreshTimer: ReturnType<typeof setInterval> | null = null;
let leafletMap: L.Map | null = null;
let markerLayer: L.LayerGroup | null = null;

// ── Helpers ──────────────────────────────────────────────────────────────────
function fmt(n: number): string {
  return n.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'ahora';
  if (m < 60) return `hace ${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `hace ${h}h`;
  return `hace ${Math.floor(h / 24)}d`;
}

const lastUpdatedLabel = computed(() => {
  if (!lastUpdated.value) return '';
  return timeAgo(lastUpdated.value.toISOString());
});

function prioridadColor(p: string): string {
  return { critica: '#dc2626', alta: '#f97316', media: '#3b82f6', baja: '#22c55e' }[p] ?? '#6b7280';
}

function alertClass(p: string): string {
  return { critica: 'alert-critica', alta: 'alert-alta', media: 'alert-media', baja: 'alert-baja' }[p] ?? '';
}

// ── Data loading ──────────────────────────────────────────────────────────────
async function load() {
  loading.value = true;
  error.value = '';
  try {
    data.value = await getDashboard();
    lastUpdated.value = new Date();
    await updateMap();
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error al cargar el dashboard.';
  } finally {
    loading.value = false;
  }
}

// ── Leaflet map ───────────────────────────────────────────────────────────────
function makeIcon(color: string): L.DivIcon {
  return L.divIcon({
    className: '',
    html: `<div style="
      width:14px;height:14px;border-radius:50%;
      background:${color};border:2.5px solid #fff;
      box-shadow:0 1px 4px rgba(0,0,0,0.35);
    "></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

async function initMap() {
  await new Promise<void>((r) => setTimeout(r, 100));
  const el = document.getElementById('prointel-map');
  if (!el || leafletMap) return;

  leafletMap = L.map(el, { zoomControl: true, scrollWheelZoom: true }).setView([-12.05, -77.03], 11);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(leafletMap);
  markerLayer = L.layerGroup().addTo(leafletMap);
}

async function updateMap() {
  if (!leafletMap) await initMap();
  if (!leafletMap || !markerLayer || !data.value) return;
  markerLayer.clearLayers();

  const pedidos = data.value.pedidos_mapa.filter((p) => p.lat && p.lon);
  pedidos.forEach((p) => {
    const color = prioridadColor(p.prioridad);
    const marker = L.marker([p.lat, p.lon], { icon: makeIcon(color) });
    marker.bindPopup(`
      <div style="min-width:180px;font-family:inherit;">
        <p style="margin:0 0 4px;font-weight:700;font-size:0.85rem;">${p.codigo}</p>
        <p style="margin:0 0 2px;font-size:0.8rem;">${p.titulo}</p>
        <p style="margin:0 0 2px;font-size:0.75rem;color:#6b7280;">${p.cliente}</p>
        <p style="margin:0;font-size:0.75rem;">
          <span style="background:${color};color:#fff;padding:1px 6px;border-radius:999px;font-size:0.7rem;">${p.prioridad}</span>
          · ${p.estado}
        </p>
        ${p.tecnico ? `<p style="margin:4px 0 0;font-size:0.75rem;color:#374151;">👷 ${p.tecnico}</p>` : ''}
      </div>
    `);
    markerLayer!.addLayer(marker);
  });

  if (pedidos.length > 0) {
    const group = L.featureGroup(markerLayer.getLayers() as L.Layer[]);
    leafletMap.fitBounds(group.getBounds().pad(0.15));
  }
}

// ── Chart data ────────────────────────────────────────────────────────────────
const ESTADO_COLORS: Record<string, string> = {
  'por-confirmar': '#f59e0b',
  'confirmado':    '#3b82f6',
  'rechazado':     '#ef4444',
  'en-labor':      '#8b5cf6',
  'cierre-tecnico':'#06b6d4',
  'completado':    '#22c55e',
  'dado-de-baja':  '#6b7280',
};

const estadoChartData = computed(() => {
  const items = data.value?.por_estado ?? [];
  return {
    labels: items.map((e) => e.estado.replace(/-/g, ' ')),
    datasets: [{
      data: items.map((e) => e.total),
      backgroundColor: items.map((e) => ESTADO_COLORS[e.estado] ?? '#94a3b8'),
      borderColor: '#ffffff',
      borderWidth: 2,
      hoverOffset: 6,
    }],
  };
});

const doughnutOptions: ChartOptions<'doughnut'> = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '62%',
  plugins: {
    legend: {
      position: 'bottom',
      labels: { color: '#374151', boxWidth: 11, boxHeight: 11, padding: 10, font: { size: 11 } },
    },
    tooltip: { bodyFont: { size: 12 } },
  },
};

const tendenciaChartData = computed(() => {
  const items = data.value?.tendencia_7d ?? [];
  return {
    labels: items.map((t) => {
      const d = new Date(t.fecha);
      return d.toLocaleDateString('es-PE', { weekday: 'short', day: 'numeric' });
    }),
    datasets: [
      {
        label: 'Creados',
        data: items.map((t) => t.creados),
        borderColor: '#1d4ed8',
        backgroundColor: 'rgba(29,78,216,0.10)',
        fill: true,
        tension: 0.42,
        pointBackgroundColor: '#1d4ed8',
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Cerrados',
        data: items.map((t) => t.cerrados),
        borderColor: '#16a34a',
        backgroundColor: 'rgba(22,163,74,0.10)',
        fill: true,
        tension: 0.42,
        pointBackgroundColor: '#16a34a',
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  };
});

const lineOptions: ChartOptions<'line'> = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: {
      position: 'top',
      labels: { color: '#374151', boxWidth: 12, boxHeight: 12, padding: 12, font: { size: 11.5 } },
    },
  },
  scales: {
    x: {
      ticks: { color: '#6b7280', font: { size: 11 } },
      grid: { display: false },
    },
    y: {
      beginAtZero: true,
      ticks: { color: '#6b7280', font: { size: 11 }, stepSize: 1 },
      grid: { color: 'rgba(0,0,0,0.05)' },
    },
  },
};

const tecnicoChartData = computed(() => {
  const items = (data.value?.por_tecnico ?? []).slice(0, 10);
  return {
    labels: items.map((t) => {
      const parts = t.tecnico_nombre.split(' ');
      return parts.length >= 2 ? `${parts[0]} ${parts[1].charAt(0)}.` : t.tecnico_nombre;
    }),
    datasets: [{
      label: 'Pedidos activos',
      data: items.map((t) => t.pedidos_activos),
      backgroundColor: items.map((_, i) => [
        '#1d4ed8','#2563eb','#3b82f6','#60a5fa','#93c5fd',
        '#1e40af','#1e3a8a','#172554','#0ea5e9','#0284c7',
      ][i % 10]),
      borderRadius: 6,
      borderSkipped: false,
    }],
  };
});

const barOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y',
  plugins: {
    legend: { display: false },
    tooltip: { bodyFont: { size: 12 } },
  },
  scales: {
    x: {
      beginAtZero: true,
      ticks: { color: '#6b7280', font: { size: 11 }, stepSize: 1 },
      grid: { color: 'rgba(0,0,0,0.05)' },
    },
    y: {
      ticks: { color: '#374151', font: { size: 11 } },
      grid: { display: false },
    },
  },
};

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(async () => {
  await load();
  refreshTimer = setInterval(load, 30_000);
});

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer);
  if (leafletMap) {
    leafletMap.remove();
    leafletMap = null;
  }
});
</script>

<style scoped>
/* ── Root layout ─────────────────────────────────────────────────────────── */
.dash-root {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 24px;
}

/* ── Header ──────────────────────────────────────────────────────────────── */
.dash-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.dash-title {
  margin: 0;
  font-size: 1.45rem;
  font-weight: 800;
  color: #1e3a8a;
  letter-spacing: -0.01em;
}

.dash-sub {
  margin: 3px 0 0;
  font-size: 0.82rem;
  color: #6b7280;
}

.dash-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.refresh-tag {
  font-size: 0.78rem;
  color: #9ca3af;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  padding: 4px 10px;
  border-radius: 999px;
}

.btn-refresh {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 0.83rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.btn-refresh:hover:not(:disabled) {
  background: #dbeafe;
  border-color: #93c5fd;
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Error banner ────────────────────────────────────────────────────────── */
.error-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff1f2;
  border: 1px solid #fecdd3;
  color: #be123c;
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 0.88rem;
  font-weight: 500;
}

.error-banner button {
  margin-left: auto;
  border: 1px solid #fda4af;
  background: #fff;
  color: #be123c;
  border-radius: 6px;
  padding: 4px 12px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.82rem;
}

/* ── KPI grid ────────────────────────────────────────────────────────────── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.kpi-card {
  position: relative;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 18px 18px 18px 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  overflow: hidden;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.09);
}

.kpi-icon {
  font-size: 1.6rem;
  line-height: 1;
  flex-shrink: 0;
}

.kpi-body {
  flex: 1;
  min-width: 0;
}

.kpi-label {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #6b7280;
}

.kpi-value {
  margin: 4px 0 0;
  font-size: 1.9rem;
  font-weight: 800;
  color: #111827;
  line-height: 1;
}

.kpi-value.kpi-danger { color: #dc2626; }
.kpi-value.kpi-warning { color: #d97706; }
.kpi-value.kpi-success { color: #16a34a; }

.kpi-sub {
  margin: 4px 0 0;
  font-size: 0.75rem;
  color: #9ca3af;
}

.kpi-accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 5px;
  border-radius: 14px 0 0 14px;
}
.kpi-accent.blue  { background: #1d4ed8; }
.kpi-accent.red   { background: #dc2626; }
.kpi-accent.amber { background: #d97706; }
.kpi-accent.green { background: #16a34a; }

/* ── Skeleton ────────────────────────────────────────────────────────────── */
@keyframes shimmer {
  0%   { background-position: -600px 0; }
  100% { background-position: 600px 0; }
}

.skeleton-kpi,
.skeleton-chart {
  border-radius: 14px;
  background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
  background-size: 600px 100%;
  animation: shimmer 1.4s infinite;
}

.skeleton-kpi {
  height: 96px;
}

.skeleton-chart {
  height: 280px;
  flex: 1;
}

.skeleton-chart.tall {
  height: 340px;
}

/* ── Charts row ──────────────────────────────────────────────────────────── */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

/* ── Chart card ──────────────────────────────────────────────────────────── */
.chart-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chart-title {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 700;
  color: #1e3a8a;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.chart-wrap {
  position: relative;
  height: 240px;
  flex: 1;
}

.pie-wrap {
  height: 220px;
}

/* ── Map ─────────────────────────────────────────────────────────────────── */
.map-card {
  min-height: 360px;
}

.leaflet-container {
  flex: 1;
  border-radius: 10px;
  min-height: 300px;
  z-index: 0;
}

.legend-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

/* ── Alerts ──────────────────────────────────────────────────────────────── */
.alerts-card,
.timeline-card {
  min-height: 320px;
  max-height: 400px;
}

.alert-title {
  color: #991b1b;
}

.alerts-list,
.timeline {
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 310px;
}

.alert-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #fee2e2;
  background: #fff5f5;
  transition: background 0.15s;
}

.alert-row:hover { background: #fff1f1; }

.alert-critica { border-color: #fca5a5; background: #fff5f5; }
.alert-alta    { border-color: #fdba74; background: #fff7ed; }
.alert-media   { border-color: #93c5fd; background: #eff6ff; }
.alert-baja    { border-color: #86efac; background: #f0fdf4; }

.alert-badge {
  color: #fff;
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  padding: 3px 7px;
  border-radius: 5px;
  flex-shrink: 0;
  margin-top: 2px;
}

.alert-meta { flex: 1; min-width: 0; }

.alert-code {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 700;
  color: #374151;
  text-transform: uppercase;
}

.alert-titulo {
  margin: 2px 0 0;
  font-size: 0.82rem;
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.alert-detail {
  margin: 2px 0 0;
  font-size: 0.75rem;
  color: #9ca3af;
}

.alert-time {
  font-size: 0.72rem;
  color: #9ca3af;
  flex-shrink: 0;
  margin-top: 2px;
  white-space: nowrap;
}

/* ── Timeline ────────────────────────────────────────────────────────────── */
.timeline-item {
  display: flex;
  gap: 12px;
  position: relative;
  padding-bottom: 12px;
}

.timeline-item:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 6px;
  top: 16px;
  bottom: 0;
  width: 1px;
  background: #e5e7eb;
}

.tl-dot {
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: #1d4ed8;
  border: 2.5px solid #fff;
  box-shadow: 0 0 0 2px #bfdbfe;
  flex-shrink: 0;
  margin-top: 3px;
}

.tl-body { flex: 1; min-width: 0; }

.tl-main {
  margin: 0;
  font-size: 0.82rem;
  color: #111827;
}

.tl-detail {
  margin: 2px 0 0;
  font-size: 0.78rem;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tl-meta {
  margin: 2px 0 0;
  font-size: 0.72rem;
  color: #9ca3af;
}

/* ── Empty state ─────────────────────────────────────────────────────────── */
.empty-state {
  color: #9ca3af;
  font-size: 0.85rem;
  text-align: center;
  padding: 24px 0;
}

/* ── Costs ───────────────────────────────────────────────────────────────── */
.costs-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.costs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.costs-total {
  font-size: 0.88rem;
  color: #374151;
}

.costs-total strong {
  color: #1e3a8a;
  font-size: 1rem;
}

.costs-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.cost-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 14px;
}

.cost-item-total {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.cost-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-size: 1.3rem;
  flex-shrink: 0;
}

.cost-label {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #6b7280;
}

.cost-value {
  margin: 4px 0 0;
  font-size: 1.15rem;
  font-weight: 800;
  color: #111827;
}

.cost-total-val { color: #1d4ed8; }

/* ── Responsive ──────────────────────────────────────────────────────────── */
@media (max-width: 1200px) {
  .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 900px) {
  .charts-row { grid-template-columns: 1fr; }
  .costs-grid { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 600px) {
  .kpi-grid { grid-template-columns: 1fr 1fr; }
  .costs-grid { grid-template-columns: 1fr; }
}

@media (max-width: 420px) {
  .kpi-grid { grid-template-columns: 1fr; }
}
</style>
