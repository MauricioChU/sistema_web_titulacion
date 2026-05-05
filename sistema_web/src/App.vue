<template>
  <!-- ── Auth loading ───────────────────────────────────────────────────── -->
  <div v-if="sessionLoading" class="splash">
    <div class="splash-logo">P</div>
    <div class="splash-brand">PROINTEL</div>
    <div class="splash-spinner"></div>
  </div>

  <!-- ── Login ─────────────────────────────────────────────────────────── -->
  <LoginView v-else-if="!isAuthenticated" @login-ok="handleLogin" />

  <!-- ── App shell ──────────────────────────────────────────────────────── -->
  <div v-else class="app-shell" :class="{ 'sidebar-collapsed': sidebarOpen === false }">
    <!-- Sidebar -->
    <aside class="sidebar" :class="{ 'sidebar-open': sidebarOpen }">
      <!-- Brand -->
      <div class="sidebar-brand">
        <div class="brand-mark">P</div>
        <div class="brand-text">
          <span class="brand-name">PROINTEL</span>
          <span class="brand-tagline">Panel operativo</span>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="sidebar-nav" aria-label="Navegación principal">
        <button
          v-for="item in menuItems"
          :key="item.key"
          type="button"
          class="nav-item"
          :class="{ active: currentView === item.key }"
          @click="navigate(item.key)"
        >
          <span class="nav-icon" aria-hidden="true">
            <component :is="item.icon" :size="17" />
          </span>
          <span class="nav-label">{{ item.label }}</span>
          <span
            v-if="item.key === 'notificaciones' && unreadCount > 0"
            class="nav-badge"
          >{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
        </button>
      </nav>

      <!-- User info -->
      <div class="sidebar-user">
        <div class="user-avatar">{{ userInitials }}</div>
        <div class="user-meta">
          <p class="user-name">{{ currentUser?.nombre_completo || currentUser?.username }}</p>
          <span class="user-role-badge" :class="`role-${currentUser?.rol}`">
            {{ rolLabel }}
          </span>
        </div>
      </div>

      <!-- Logout -->
      <button type="button" class="btn-logout" @click="handleLogout">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
          <polyline points="16 17 21 12 16 7"/>
          <line x1="21" y1="12" x2="9" y2="12"/>
        </svg>
        Cerrar sesión
      </button>
    </aside>

    <!-- Mobile overlay -->
    <div
      v-if="sidebarOpen"
      class="sidebar-overlay"
      aria-hidden="true"
      @click="sidebarOpen = false"
    ></div>

    <!-- Main content -->
    <div class="main-wrapper">
      <!-- Mobile top bar -->
      <div class="topbar">
        <button
          type="button"
          class="hamburger"
          :aria-label="sidebarOpen ? 'Cerrar menú' : 'Abrir menú'"
          @click="sidebarOpen = !sidebarOpen"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>
        <span class="topbar-title">PROINTEL</span>
        <button
          v-if="unreadCount > 0"
          type="button"
          class="topbar-notif-btn"
          @click="navigate('notificaciones')"
        >
          <Bell :size="20" />
          <span class="topbar-badge">{{ unreadCount }}</span>
        </button>
      </div>

      <main class="main-content" @click="closeSidebarOnMobile">
        <DashboardView      v-if="currentView === 'dashboard'" />
        <PedidosView        v-else-if="currentView === 'pedidos'" />
        <PedidosTecnicoView v-else-if="currentView === 'pedidos-tecnico'" />
        <BaseDatosView      v-else-if="currentView === 'base-datos'" />
        <NotificacionesView v-else-if="currentView === 'notificaciones'" />
        <BaseDatosView      v-else-if="currentView === 'usuarios'" />
      </main>
    </div>

    <!-- Toast notifications -->
    <Transition name="toast">
      <div v-if="toast.visible" class="toast" :class="`toast-${toast.type}`" role="alert">
        <Bell :size="15" class="toast-icon" />
        <span class="toast-msg">{{ toast.message }}</span>
        <button type="button" class="toast-close" @click="toast.visible = false">✕</button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch, type Component } from 'vue';
import {
  LayoutDashboard, ClipboardList, Wrench, Database, Bell, Users,
} from 'lucide-vue-next';
import { restoreSession, logout as apiLogout } from './api/auth';
import { getPendientes } from './api/notificaciones';
import { listNotificaciones } from './api/notificaciones';
import { type SessionUser } from './stores/sessionStore';
import { getCachedUser } from './api/auth';
import type { ViewKey } from './types/navigation';
import BaseDatosView from './views/BaseDatosView.vue';
import DashboardView from './views/DashboardView.vue';
import LoginView from './views/LoginView.vue';
import NotificacionesView from './views/NotificacionesView.vue';
import PedidosTecnicoView from './views/PedidosTecnicoView.vue';
import PedidosView from './views/PedidosView.vue';

// ── State ─────────────────────────────────────────────────────────────────────
const currentUser   = ref<SessionUser | null>(null);
const currentView   = ref<ViewKey>('dashboard');
const sidebarOpen   = ref(false);
const sessionLoading= ref(true);
const unreadCount   = ref(0);

const toast = ref({
  visible: false,
  message: '',
  type: 'info' as 'info' | 'warning',
});

let pollTimer: ReturnType<typeof setInterval> | null = null;
let toastTimer: ReturnType<typeof setTimeout> | null = null;

// ── Computed ──────────────────────────────────────────────────────────────────
const isAuthenticated = computed(() => Boolean(currentUser.value));

const rolLabel = computed(() => {
  const rol = currentUser.value?.rol;
  if (!rol) return '';
  return { admin: 'Administrador', coordinador: 'Coordinador', tecnico: 'Técnico' }[rol] ?? '';
});

const userInitials = computed(() => {
  const name = currentUser.value?.nombre_completo || currentUser.value?.username || '?';
  return name.split(' ').slice(0, 2).map((w) => w[0]).join('').toUpperCase();
});

interface NavItem {
  key: ViewKey;
  label: string;
  icon: Component;
}

const menuItems = computed<NavItem[]>(() => {
  const rol = currentUser.value?.rol;

  const allItems: Record<ViewKey, NavItem> = {
    'dashboard':        { key: 'dashboard',        label: 'Dashboard',      icon: LayoutDashboard },
    'pedidos':          { key: 'pedidos',           label: 'Pedidos',        icon: ClipboardList },
    'pedidos-tecnico':  { key: 'pedidos-tecnico',   label: 'Mis Pedidos',    icon: Wrench },
    'base-datos':       { key: 'base-datos',        label: 'Base de Datos',  icon: Database },
    'notificaciones':   { key: 'notificaciones',    label: 'Notificaciones', icon: Bell },
    'usuarios':         { key: 'usuarios',          label: 'Usuarios',       icon: Users },
  };

  if (rol === 'admin') {
    return ['dashboard', 'pedidos', 'pedidos-tecnico', 'base-datos', 'notificaciones', 'usuarios'].map(
      (k) => allItems[k as ViewKey],
    );
  }
  if (rol === 'coordinador') {
    return ['dashboard', 'pedidos', 'base-datos', 'notificaciones'].map(
      (k) => allItems[k as ViewKey],
    );
  }
  return ['dashboard', 'pedidos-tecnico', 'notificaciones'].map(
    (k) => allItems[k as ViewKey],
  );
});

// ── Navigation ────────────────────────────────────────────────────────────────
function navigate(key: ViewKey) {
  currentView.value = key;
  sidebarOpen.value = false;
}

function closeSidebarOnMobile() {
  if (window.innerWidth < 960) sidebarOpen.value = false;
}

function defaultView(rol: SessionUser['rol']): ViewKey {
  return rol === 'tecnico' ? 'pedidos-tecnico' : 'dashboard';
}

function ensureViewAllowed() {
  const allowed = new Set(menuItems.value.map((i) => i.key));
  if (!allowed.has(currentView.value)) {
    currentView.value = defaultView(currentUser.value?.rol ?? 'tecnico');
  }
}

// ── Toast ─────────────────────────────────────────────────────────────────────
function showToast(message: string, type: 'info' | 'warning' = 'info') {
  if (toastTimer) clearTimeout(toastTimer);
  toast.value = { visible: true, message, type };
  toastTimer = setTimeout(() => { toast.value.visible = false; }, 5000);
}

// ── Polling ───────────────────────────────────────────────────────────────────
async function pollNotifications() {
  if (!currentUser.value) return;
  try {
    const pendientes = await getPendientes();
    const rol = currentUser.value.rol;

    if (rol === 'tecnico') {
      if (pendientes.pedidos_pendientes.length > 0) {
        showToast(
          `Tienes ${pendientes.pedidos_pendientes.length} pedido(s) pendiente(s) de confirmar`,
          'warning',
        );
      }
    } else {
      if (pendientes.pedidos_rechazados.length > 0) {
        showToast(
          `${pendientes.pedidos_rechazados.length} pedido(s) rechazado(s) requieren reasignación`,
          'warning',
        );
      }
    }
    unreadCount.value = pendientes.no_leidas;
  } catch {
    // silent fail
  }
}

async function loadUnreadCount() {
  try {
    const notifs = await listNotificaciones(true);
    unreadCount.value = notifs.length;
  } catch { /* ignore */ }
}

function startPolling() {
  pollNotifications();
  pollTimer = setInterval(pollNotifications, 60_000);
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

// ── Auth actions ──────────────────────────────────────────────────────────────
async function handleLogin(user: SessionUser) {
  currentUser.value = user;
  currentView.value = defaultView(user.rol);
  sidebarOpen.value = false;
  await loadUnreadCount();
  startPolling();
}

async function handleLogout() {
  stopPolling();
  await apiLogout();
  currentUser.value = null;
  currentView.value = 'dashboard';
  sidebarOpen.value = false;
  unreadCount.value = 0;
  toast.value.visible = false;
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(async () => {
  const cached = getCachedUser();
  if (cached) currentUser.value = cached;

  sessionLoading.value = true;
  try {
    const restored = await restoreSession();
    currentUser.value = restored;
    if (restored) {
      currentView.value = defaultView(restored.rol);
      ensureViewAllowed();
      await loadUnreadCount();
      startPolling();
    }
  } catch {
    currentUser.value = null;
  } finally {
    sessionLoading.value = false;
  }
});

onBeforeUnmount(() => {
  stopPolling();
  if (toastTimer) clearTimeout(toastTimer);
});

watch(currentUser, () => { ensureViewAllowed(); });
</script>

<style scoped>
/* ── Splash ───────────────────────────────────────────────────────────────── */
.splash {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: #0d1117;
}

.splash-logo {
  width: 52px;
  height: 52px;
  background: #3fb950;
  color: #fff;
  font-size: 1.4rem;
  font-weight: 900;
  display: grid;
  place-items: center;
}

.splash-brand {
  font-size: 1.2rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  color: #e6edf3;
}

.splash-spinner {
  width: 22px;
  height: 22px;
  border: 2px solid #30363d;
  border-top-color: #3fb950;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* ── App shell ────────────────────────────────────────────────────────────── */
.app-shell {
  height: 100dvh;
  max-height: 100dvh;
  display: flex;
  overflow: hidden;
  background: #0d1117;
}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
.sidebar {
  width: 200px;
  flex-shrink: 0;
  background: #161b22;
  border-right: 1px solid #30363d;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  z-index: 40;
  transition: transform 0.24s ease;
}

/* ── Brand block ─────────────────────────────────────────────────────────── */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 16px 16px;
  border-bottom: 1px solid #30363d;
}

.brand-mark {
  width: 36px;
  height: 36px;
  background: #3fb950;
  color: #fff;
  font-size: 1rem;
  font-weight: 900;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-name {
  font-size: 0.9rem;
  font-weight: 800;
  color: #e6edf3;
  letter-spacing: 0.1em;
}

.brand-tagline {
  font-size: 0.7rem;
  color: #636c76;
  margin-top: 1px;
}

/* ── Navigation ───────────────────────────────────────────────────────────── */
.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 12px 8px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  text-align: left;
  border: 1px solid transparent;
  border-left: 2px solid transparent;
  background: transparent;
  color: #636c76;
  padding: 9px 10px;
  font-size: 0.84rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
  position: relative;
}

.nav-item:hover {
  background: rgba(63,185,80,0.07);
  color: #9198a1;
  border-left-color: #30363d;
}

.nav-item.active {
  background: rgba(63,185,80,0.12);
  border-left-color: #3fb950;
  border-color: transparent;
  border-left-color: #3fb950;
  color: #3fb950;
  font-weight: 700;
}

.nav-icon {
  flex-shrink: 0;
  width: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-label { flex: 1; }

.nav-badge {
  background: #f85149;
  color: #fff;
  font-size: 0.65rem;
  font-weight: 800;
  padding: 1px 6px;
  min-width: 18px;
  text-align: center;
  line-height: 1.6;
  flex-shrink: 0;
}

/* ── User info ────────────────────────────────────────────────────────────── */
.sidebar-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-top: 1px solid #30363d;
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: #21262d;
  border: 1px solid #3fb950;
  color: #3fb950;
  font-size: 0.8rem;
  font-weight: 800;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.user-meta { min-width: 0; }

.user-name {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 600;
  color: #e6edf3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role-badge {
  display: inline-block;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 6px;
  margin-top: 3px;
  letter-spacing: 0.04em;
}

.role-admin       { background: rgba(210,153,34,0.15); color: #d29922; border: 1px solid rgba(210,153,34,0.35); }
.role-coordinador { background: rgba(88,166,255,0.12); color: #58a6ff; border: 1px solid rgba(88,166,255,0.3); }
.role-tecnico     { background: rgba(63,185,80,0.12);  color: #3fb950; border: 1px solid rgba(63,185,80,0.3); }

/* ── Logout button ────────────────────────────────────────────────────────── */
.btn-logout {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 0 10px 16px;
  padding: 9px;
  border: 1px solid #30363d;
  background: transparent;
  color: #636c76;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
}

.btn-logout:hover {
  background: rgba(248,81,73,0.1);
  border-color: rgba(248,81,73,0.4);
  color: #f85149;
}

/* ── Mobile overlay ───────────────────────────────────────────────────────── */
.sidebar-overlay {
  position: fixed;
  inset: 0;
  z-index: 35;
  background: rgba(0,0,0,0.6);
}

/* ── Main wrapper ─────────────────────────────────────────────────────────── */
.main-wrapper {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Topbar (mobile) ──────────────────────────────────────────────────────── */
.topbar {
  display: none;
  align-items: center;
  gap: 12px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
  padding: 10px 16px;
  flex-shrink: 0;
}

.hamburger {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  width: 32px;
  height: 32px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
}

.hamburger span {
  display: block;
  height: 2px;
  background: #9198a1;
  transition: transform 0.2s;
}

.topbar-title {
  font-size: 0.95rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  color: #e6edf3;
  flex: 1;
}

.topbar-notif-btn {
  position: relative;
  background: none;
  border: none;
  color: #9198a1;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
}

.topbar-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: #f85149;
  color: #fff;
  font-size: 0.6rem;
  font-weight: 800;
  width: 15px;
  height: 15px;
  display: grid;
  place-items: center;
}

/* ── Main content ─────────────────────────────────────────────────────────── */
.main-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0;
  background: #0d1117;
}

/* ── Toast ────────────────────────────────────────────────────────────────── */
.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border: 1px solid #30363d;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
  font-size: 0.85rem;
  font-weight: 500;
  max-width: 360px;
  background: #161b22;
  color: #e6edf3;
  font-family: 'Segoe UI', system-ui, sans-serif;
}

.toast-warning {
  border-color: rgba(210,153,34,0.5);
  background: rgba(210,153,34,0.08);
  color: #d29922;
}

.toast-info {
  border-color: rgba(88,166,255,0.3);
  background: rgba(88,166,255,0.08);
  color: #58a6ff;
}

.toast-icon { flex-shrink: 0; }
.toast-msg  { flex: 1; line-height: 1.4; }

.toast-close {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 0.8rem;
  opacity: 0.6;
  padding: 2px 4px;
  flex-shrink: 0;
}

.toast-close:hover { opacity: 1; }

/* ── Toast transitions ────────────────────────────────────────────────────── */
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.97);
}

/* ── Mobile breakpoint ────────────────────────────────────────────────────── */
@media (max-width: 960px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    transform: translateX(-100%);
  }

  .sidebar.sidebar-open {
    transform: translateX(0);
  }

  .topbar {
    display: flex;
  }
}

@media (max-width: 480px) {
  .toast {
    bottom: 16px;
    right: 16px;
    left: 16px;
    max-width: none;
  }
}
</style>
