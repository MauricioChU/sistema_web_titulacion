<template>
  <div class="notif-root">
    <!-- ── Header ──────────────────────────────────────────────────────── -->
    <header class="notif-header">
      <div class="notif-header-left">
        <h2 class="notif-title">Bandeja de Entrada</h2>
        <p class="notif-sub">
          {{ noLeidas }} no leída{{ noLeidas === 1 ? '' : 's' }} de {{ all.length }} notificacion{{ all.length === 1 ? '' : 'es' }}
        </p>
      </div>
      <button
        v-if="noLeidas > 0"
        type="button"
        class="btn-mark-all"
        :disabled="markingAll"
        @click="handleMarcarTodas"
      >
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        Marcar todas como leídas
      </button>
    </header>

    <!-- ── Error ───────────────────────────────────────────────────────── -->
    <div v-if="error" class="error-banner">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      {{ error }}
    </div>

    <!-- ── Filter tabs ─────────────────────────────────────────────────── -->
    <div class="filter-tabs" role="tablist">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        type="button"
        role="tab"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
        <span v-if="tab.count > 0" class="tab-badge">{{ tab.count }}</span>
      </button>
    </div>

    <!-- ── Loading skeleton ────────────────────────────────────────────── -->
    <template v-if="loading && all.length === 0">
      <div v-for="i in 5" :key="i" class="skeleton-notif"></div>
    </template>

    <!-- ── Notification list ───────────────────────────────────────────── -->
    <div v-else-if="filtered.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <p class="empty-title">Sin notificaciones</p>
      <p class="empty-sub">
        {{ activeTab === 'no-leidas' ? 'No tienes notificaciones sin leer.' : 'No hay notificaciones en esta categoría.' }}
      </p>
    </div>

    <div v-else class="notif-list">
      <div
        v-for="notif in filtered"
        :key="notif.id"
        class="notif-card"
        :class="[tipoClass(notif.tipo), { unread: !notif.leida }]"
        @click="handleClick(notif)"
      >
        <!-- Unread dot -->
        <span v-if="!notif.leida" class="unread-dot" aria-label="No leída"></span>

        <!-- Icon -->
        <div class="notif-icon-wrap" :style="{ background: tipoBg(notif.tipo) }">
          <span class="notif-icon">{{ tipoIcon(notif.tipo) }}</span>
        </div>

        <!-- Body -->
        <div class="notif-body">
          <div class="notif-top">
            <span class="notif-tipo-badge" :style="{ background: tipoBg(notif.tipo), color: tipoColor(notif.tipo) }">
              {{ tipoLabel(notif.tipo) }}
            </span>
            <span class="notif-time">{{ timeAgo(notif.created_at) }}</span>
          </div>
          <p class="notif-titulo">{{ notif.titulo }}</p>
          <p class="notif-msg">{{ notif.mensaje }}</p>

          <div v-if="notif.pedido_id" class="notif-pedido-link">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
            </svg>
            Ver pedido
          </div>
        </div>

        <!-- Mark read button -->
        <button
          v-if="!notif.leida"
          type="button"
          class="btn-mark-read"
          :disabled="markingId === notif.id"
          :title="'Marcar como leída'"
          @click.stop="handleMarcarLeida(notif)"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import {
  listNotificaciones,
  marcarLeida,
  marcarTodasLeidas,
  type ApiNotificacion,
} from '../api/notificaciones';

// ── State ─────────────────────────────────────────────────────────────────────
const all = ref<ApiNotificacion[]>([]);
const loading = ref(false);
const error = ref('');
const activeTab = ref<'todas' | 'no-leidas' | 'pedido_rechazado' | 'pedido_por_confirmar' | 'pedido_completado' | 'stock_bajo'>('todas');
const markingId = ref<string | null>(null);
const markingAll = ref(false);

// ── Computed ──────────────────────────────────────────────────────────────────
const noLeidas = computed(() => all.value.filter((n) => !n.leida).length);

const countByTipo = (tipo: ApiNotificacion['tipo']) =>
  all.value.filter((n) => n.tipo === tipo).length;

const tabs = computed(() => [
  { key: 'todas'               as const, label: 'Todas',              count: all.value.length },
  { key: 'no-leidas'           as const, label: 'No leídas',          count: noLeidas.value },
  { key: 'pedido_rechazado'    as const, label: 'Rechazados',         count: countByTipo('pedido_rechazado') },
  { key: 'pedido_por_confirmar'as const, label: 'Por confirmar',      count: countByTipo('pedido_por_confirmar') },
  { key: 'pedido_completado'   as const, label: 'Completados',        count: countByTipo('pedido_completado') },
  { key: 'stock_bajo'          as const, label: 'Stock bajo',         count: countByTipo('stock_bajo') },
]);

const filtered = computed(() => {
  if (activeTab.value === 'todas') return all.value;
  if (activeTab.value === 'no-leidas') return all.value.filter((n) => !n.leida);
  return all.value.filter((n) => n.tipo === activeTab.value);
});

// ── Helpers ───────────────────────────────────────────────────────────────────
function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'ahora mismo';
  if (m < 60) return `hace ${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `hace ${h}h`;
  const d = Math.floor(h / 24);
  if (d < 7) return `hace ${d}d`;
  return new Date(iso).toLocaleDateString('es-PE', { day: 'numeric', month: 'short' });
}

function tipoIcon(tipo: ApiNotificacion['tipo']): string {
  return {
    pedido_rechazado:     '❌',
    pedido_por_confirmar: '⏳',
    pedido_completado:    '✅',
    stock_bajo:           '📦',
    sistema:              'ℹ️',
  }[tipo] ?? '🔔';
}

function tipoLabel(tipo: ApiNotificacion['tipo']): string {
  return {
    pedido_rechazado:     'Rechazado',
    pedido_por_confirmar: 'Por confirmar',
    pedido_completado:    'Completado',
    stock_bajo:           'Stock bajo',
    sistema:              'Sistema',
  }[tipo] ?? tipo;
}

function tipoColor(tipo: ApiNotificacion['tipo']): string {
  return {
    pedido_rechazado:     '#b91c1c',
    pedido_por_confirmar: '#92400e',
    pedido_completado:    '#14532d',
    stock_bajo:           '#9a3412',
    sistema:              '#1e3a8a',
  }[tipo] ?? '#374151';
}

function tipoBg(tipo: ApiNotificacion['tipo']): string {
  return {
    pedido_rechazado:     '#fee2e2',
    pedido_por_confirmar: '#fef3c7',
    pedido_completado:    '#dcfce7',
    stock_bajo:           '#ffedd5',
    sistema:              '#dbeafe',
  }[tipo] ?? '#f3f4f6';
}

function tipoClass(tipo: ApiNotificacion['tipo']): string {
  return {
    pedido_rechazado:     'tipo-rechazado',
    pedido_por_confirmar: 'tipo-por-confirmar',
    pedido_completado:    'tipo-completado',
    stock_bajo:           'tipo-stock',
    sistema:              'tipo-sistema',
  }[tipo] ?? '';
}

// ── Actions ───────────────────────────────────────────────────────────────────
async function load() {
  loading.value = true;
  error.value = '';
  try {
    all.value = await listNotificaciones();
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error al cargar notificaciones.';
  } finally {
    loading.value = false;
  }
}

async function handleMarcarLeida(notif: ApiNotificacion) {
  markingId.value = notif.id;
  try {
    await marcarLeida(notif.id);
    const target = all.value.find((n) => n.id === notif.id);
    if (target) target.leida = true;
  } catch {
    // ignore
  } finally {
    markingId.value = null;
  }
}

async function handleMarcarTodas() {
  markingAll.value = true;
  try {
    await marcarTodasLeidas();
    all.value.forEach((n) => { n.leida = true; });
  } catch {
    // ignore
  } finally {
    markingAll.value = false;
  }
}

function handleClick(notif: ApiNotificacion) {
  if (!notif.leida) handleMarcarLeida(notif);
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(load);
</script>

<style scoped>
/* ── Root ────────────────────────────────────────────────────────────────── */
.notif-root {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 800px;
  margin: 0 auto;
  padding-bottom: 32px;
}

/* ── Header ──────────────────────────────────────────────────────────────── */
.notif-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.notif-title {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 800;
  color: #1e3a8a;
  letter-spacing: -0.01em;
}

.notif-sub {
  margin: 3px 0 0;
  font-size: 0.82rem;
  color: #6b7280;
}

.btn-mark-all {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid #bbf7d0;
  background: #f0fdf4;
  color: #15803d;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  white-space: nowrap;
}

.btn-mark-all:hover:not(:disabled) {
  background: #dcfce7;
  border-color: #86efac;
}

.btn-mark-all:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Error ───────────────────────────────────────────────────────────────── */
.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff1f2;
  border: 1px solid #fecdd3;
  color: #be123c;
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 0.87rem;
  font-weight: 500;
}

/* ── Filter tabs ─────────────────────────────────────────────────────────── */
.filter-tabs {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  background: #f3f4f6;
  border-radius: 12px;
  padding: 4px;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border: none;
  background: transparent;
  color: #6b7280;
  border-radius: 9px;
  font-size: 0.84rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
}

.tab-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

.tab-btn.active {
  background: #fff;
  color: #1e3a8a;
  font-weight: 700;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.tab-badge {
  background: #1d4ed8;
  color: #fff;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 999px;
  min-width: 18px;
  text-align: center;
  line-height: 1.5;
}

.tab-btn:not(.active) .tab-badge {
  background: #d1d5db;
  color: #374151;
}

/* ── Skeleton ────────────────────────────────────────────────────────────── */
@keyframes shimmer {
  0%   { background-position: -600px 0; }
  100% { background-position: 600px 0; }
}

.skeleton-notif {
  height: 88px;
  border-radius: 12px;
  background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
  background-size: 600px 100%;
  animation: shimmer 1.4s infinite;
}

/* ── Empty state ─────────────────────────────────────────────────────────── */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #9ca3af;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 12px;
}

.empty-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: #4b5563;
}

.empty-sub {
  margin: 6px 0 0;
  font-size: 0.85rem;
}

/* ── Notification list ───────────────────────────────────────────────────── */
.notif-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.notif-card {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 14px 16px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

.notif-card:hover {
  background: #f9fafb;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
}

.notif-card.unread {
  border-left: 4px solid #1d4ed8;
  background: #fafbff;
}

/* Type border accents */
.notif-card.tipo-rechazado.unread    { border-left-color: #dc2626; }
.notif-card.tipo-por-confirmar.unread{ border-left-color: #d97706; }
.notif-card.tipo-completado.unread   { border-left-color: #16a34a; }
.notif-card.tipo-stock.unread        { border-left-color: #ea580c; }
.notif-card.tipo-sistema.unread      { border-left-color: #2563eb; }

/* ── Unread dot ──────────────────────────────────────────────────────────── */
.unread-dot {
  position: absolute;
  top: 14px;
  right: 48px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #1d4ed8;
  flex-shrink: 0;
}

/* ── Icon ────────────────────────────────────────────────────────────────── */
.notif-icon-wrap {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.notif-icon {
  font-size: 1.3rem;
  line-height: 1;
}

/* ── Body ────────────────────────────────────────────────────────────────── */
.notif-body {
  flex: 1;
  min-width: 0;
}

.notif-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.notif-tipo-badge {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 999px;
}

.notif-time {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-left: auto;
  white-space: nowrap;
}

.notif-titulo {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 700;
  color: #111827;
  line-height: 1.3;
}

.notif-msg {
  margin: 4px 0 0;
  font-size: 0.82rem;
  color: #6b7280;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notif-pedido-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
  font-size: 0.78rem;
  font-weight: 600;
  color: #1d4ed8;
}

.notif-pedido-link:hover { text-decoration: underline; }

/* ── Mark read button ────────────────────────────────────────────────────── */
.btn-mark-read {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border: 1px solid #d1fae5;
  background: #f0fdf4;
  color: #16a34a;
  border-radius: 8px;
  cursor: pointer;
  flex-shrink: 0;
  align-self: center;
  transition: background 0.15s, border-color 0.15s;
}

.btn-mark-read:hover:not(:disabled) {
  background: #dcfce7;
  border-color: #86efac;
}

.btn-mark-read:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ── Responsive ──────────────────────────────────────────────────────────── */
@media (max-width: 600px) {
  .notif-root {
    max-width: 100%;
  }

  .filter-tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
    border-radius: 10px;
  }

  .tab-btn {
    white-space: nowrap;
  }
}
</style>
