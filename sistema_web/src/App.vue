<template>
  <LoginView v-if="!isAuthenticated" @login-ok="handleLogin" />

  <div v-else class="shell">
    <SidebarNav
      :items="menuItems"
      :active="currentView"
      :open-on-mobile="sidebarOpen"
      @select="onSelectView"
      @logout="logout"
    />

    <button class="menu-btn" @click="sidebarOpen = !sidebarOpen">Menu</button>

    <main class="content" @click="sidebarOpen = false">
      <DashboardView v-if="currentView === 'dashboard'" />
      <PedidosView v-else-if="currentView === 'pedidos'" />
      <PedidosTecnicoView v-else-if="currentView === 'pedidos-tecnico'" />
      <BaseDatosView v-else />
    </main>

    <div v-if="sidebarOpen" class="overlay" @click="sidebarOpen = false"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import SidebarNav from './mockup/components/SidebarNav.vue';
import { useTecnicoBridgeStore } from './mockup/stores/tecnicoBridgeStore';
import type { MenuItem, MockViewKey } from './mockup/types';
import BaseDatosView from './mockup/views/BaseDatosView.vue';
import DashboardView from './mockup/views/DashboardView.vue';
import LoginView from './mockup/views/LoginView.vue';
import PedidosView from './mockup/views/PedidosView.vue';
import PedidosTecnicoView from './mockup/views/PedidosTecnicoView.vue';
import { getCachedUser, logout as logoutAuth, restoreSession } from './services/authService';
import type { SessionUser } from './services/session';

const bridge = useTecnicoBridgeStore();
const currentUser = ref<SessionUser | null>(getCachedUser());
const currentView = ref<MockViewKey>('dashboard');
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

function defaultViewForRole(userRole: SessionUser['role'] | 'usuario'): MockViewKey {
  if (userRole === 'tecnico') return 'pedidos-tecnico';
  return 'dashboard';
}

function ensureCurrentViewAllowed() {
  const allowed = new Set(menuItems.value.map((item) => item.key));
  if (!allowed.has(currentView.value)) {
    currentView.value = defaultViewForRole(role.value as SessionUser['role']);
  }
}

function onSelectView(view: MockViewKey) {
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
    // The technical views already show sync-state messages when API fails.
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
    // The views will communicate sync failures to the user.
  }
});
</script>

<style scoped>
.shell {
  height: 100dvh;
  max-height: 100dvh;
  display: grid;
  grid-template-columns: 235px 1fr;
  background: #071321;
  overflow: hidden;
}

.content {
  padding: 12px;
  height: 100%;
  max-height: 100dvh;
  overflow-y: auto;
  overflow-x: hidden;
}

.menu-btn,
.overlay {
  display: none;
}

@media (max-width: 900px) {
  .shell {
    height: 100dvh;
    max-height: 100dvh;
    grid-template-columns: 1fr;
  }

  .menu-btn {
    display: inline-flex;
    position: fixed;
    top: 10px;
    left: 10px;
    z-index: 50;
    border: 1px solid #2d4159;
    background: #0e1b2b;
    color: #dbe7f3;
    border-radius: 8px;
    padding: 8px 10px;
  }

  .content {
    padding: 56px 10px 10px;
    max-height: 100dvh;
  }

  .overlay {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 30;
    background: rgba(2, 8, 18, 0.52);
  }
}
</style>
