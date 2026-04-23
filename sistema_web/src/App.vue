<template>
  <LoginView v-if="!isAuthenticated" @login-ok="handleLogin" />

  <div v-else class="app-shell">
    <SidebarNav
      :items="menuItems"
      :active="currentView"
      :open-on-mobile="sidebarOpen"
      @select="onSelectView"
      @logout="logout"
    />

    <button class="menu-btn" type="button" @click="sidebarOpen = !sidebarOpen">
      <span class="menu-icon" aria-hidden="true">≡</span>
      Menu
    </button>

    <main class="app-content" @click="sidebarOpen = false">
      <DashboardView v-if="currentView === 'dashboard'" />
      <PedidosView v-else-if="currentView === 'pedidos'" />
      <PedidosTecnicoView v-else-if="currentView === 'pedidos-tecnico'" />
      <BaseDatosView v-else />
    </main>

    <div v-if="sidebarOpen" class="app-overlay" @click="sidebarOpen = false"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { getCachedUser, logout as logoutAuth, restoreSession } from './api';
import SidebarNav from './components/layout/SidebarNav.vue';
import { usePedidosStore } from './stores/pedidosStore';
import type { SessionUser } from './stores/sessionStore';
import type { MenuItem, ViewKey } from './types/navigation';
import BaseDatosView from './views/BaseDatosView.vue';
import DashboardView from './views/DashboardView.vue';
import LoginView from './views/LoginView.vue';
import PedidosTecnicoView from './views/PedidosTecnicoView.vue';
import PedidosView from './views/PedidosView.vue';

const bridge = usePedidosStore();
const currentUser = ref<SessionUser | null>(getCachedUser());
const currentView = ref<ViewKey>('dashboard');
const sidebarOpen = ref(false);
const isAuthenticated = computed(() => Boolean(currentUser.value));

const role = computed(() => currentUser.value?.role || 'usuario');

const menuItems = computed<MenuItem[]>(() => [
  ...(role.value === 'tecnico'
    ? [
        { key: 'dashboard' as const, label: 'Dashboard' },
        { key: 'pedidos' as const, label: 'Pedidos' },
        { key: 'pedidos-tecnico' as const, label: 'Mis Pedidos Tecnico' },
      ]
    : [
        { key: 'dashboard' as const, label: 'Dashboard' },
        { key: 'pedidos' as const, label: 'Pedidos Coordinador' },
        { key: 'pedidos-tecnico' as const, label: 'Mis Pedidos Tecnico' },
        { key: 'base-datos' as const, label: 'Base de datos' },
      ]),
]);

function defaultViewForRole(
  userRole: SessionUser['role'] | 'usuario',
): ViewKey {
  if (userRole === 'tecnico') return 'pedidos-tecnico';
  return 'dashboard';
}

function ensureCurrentViewAllowed() {
  const allowed = new Set(menuItems.value.map((item) => item.key));
  if (!allowed.has(currentView.value)) {
    currentView.value = defaultViewForRole(role.value as SessionUser['role']);
  }
}

function onSelectView(view: ViewKey) {
  currentView.value = view;
  sidebarOpen.value = false;
}

async function handleLogin(user: SessionUser) {
  currentUser.value = user;
  currentView.value = defaultViewForRole(user.role);
  sidebarOpen.value = false;

  try {
    await bridge.hydrateFromApi(true);
  } catch {
    // Las vistas tecnicas muestran mensajes de sincronizacion cuando la API falla.
  }
}

function logout() {
  logoutAuth();
  currentUser.value = null;
  currentView.value = 'dashboard';
  sidebarOpen.value = false;
}

onMounted(async () => {
  const restored = await restoreSession();
  if (!restored) return;

  currentUser.value = restored;
  currentView.value = defaultViewForRole(restored.role);
  ensureCurrentViewAllowed();

  try {
    await bridge.hydrateFromApi();
  } catch {
    // Las vistas comunican las fallas de sincronizacion al usuario.
  }
});
</script>

<style scoped>
.app-shell {
  height: 100dvh;
  max-height: 100dvh;
  display: grid;
  grid-template-columns: 248px 1fr;
  background: var(--color-bg);
  overflow: hidden;
}

.app-content {
  padding: 16px 18px;
  height: 100%;
  max-height: 100dvh;
  overflow-y: auto;
  overflow-x: hidden;
  background: var(--color-bg);
}

.menu-btn,
.app-overlay {
  display: none;
}

.menu-icon {
  margin-right: 6px;
  font-size: 1.1rem;
  line-height: 1;
}

@media (max-width: 960px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .menu-btn {
    display: inline-flex;
    align-items: center;
    position: fixed;
    top: 12px;
    left: 12px;
    z-index: 50;
    border: 1px solid var(--color-border);
    background: var(--color-surface);
    color: var(--color-text);
    border-radius: 10px;
    padding: 8px 12px;
    font-weight: 600;
    box-shadow: var(--shadow-sm);
  }

  .app-content {
    padding: 60px 12px 12px;
  }

  .app-overlay {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 30;
    background: rgba(6, 36, 24, 0.46);
    backdrop-filter: blur(2px);
  }
}
</style>
