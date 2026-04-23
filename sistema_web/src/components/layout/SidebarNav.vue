<template>
  <aside class="sidebar" :class="{ open: openOnMobile }">
    <header class="sidebar-header">
      <div class="logo" aria-hidden="true">P</div>
      <div class="brand-block">
        <h2>PROINTEL</h2>
        <small>Panel operativo</small>
      </div>
    </header>

    <nav class="sidebar-nav" aria-label="Navegacion principal">
      <button
        v-for="item in items"
        :key="item.key"
        type="button"
        class="nav-item"
        :class="{ active: item.key === active }"
        @click="$emit('select', item.key)"
      >
        <span class="nav-dot" aria-hidden="true"></span>
        <span class="nav-label">{{ item.label }}</span>
      </button>
    </nav>

    <button type="button" class="logout" @click="$emit('logout')">
      Cerrar sesion
    </button>
  </aside>
</template>

<script setup lang="ts">
import type { MenuItem, ViewKey } from '../../types/navigation';

defineProps<{
  items: MenuItem[];
  active: ViewKey;
  openOnMobile: boolean;
}>();

defineEmits<{
  (e: 'select', key: ViewKey): void;
  (e: 'logout'): void;
}>();
</script>

<style scoped>
.sidebar {
  width: 248px;
  border-right: 1px solid var(--color-border);
  background: linear-gradient(180deg, #ffffff 0%, var(--color-surface-alt) 100%);
  padding: 20px 16px;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 18px;
  z-index: 40;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--color-border);
}

.logo {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-weight: 800;
  font-size: 1.05rem;
  color: var(--color-text-invert);
  background: linear-gradient(135deg, var(--color-primary-600), var(--color-primary-400));
  box-shadow: var(--shadow-sm);
}

.brand-block h2 {
  margin: 0;
  font-size: 1rem;
  letter-spacing: 0.04em;
  color: var(--color-primary-800);
}

.brand-block small {
  color: var(--color-text-muted);
  font-size: 0.78rem;
}

.sidebar-nav {
  display: grid;
  gap: 6px;
  align-content: start;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  text-align: left;
  border: 1px solid transparent;
  background: transparent;
  color: var(--color-text-soft);
  border-radius: var(--radius-md);
  padding: 10px 12px;
  font-size: 0.92rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.18s ease, color 0.18s ease, border-color 0.18s ease;
}

.nav-item:hover {
  background: var(--color-primary-50);
  color: var(--color-primary-700);
}

.nav-item.active {
  background: var(--color-primary-100);
  border-color: var(--color-primary-300);
  color: var(--color-primary-800);
  font-weight: 600;
  box-shadow: var(--shadow-sm);
}

.nav-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary-200);
  flex-shrink: 0;
  transition: background 0.18s ease, transform 0.18s ease;
}

.nav-item.active .nav-dot {
  background: var(--color-primary-500);
  transform: scale(1.15);
}

.logout {
  border: 1px solid var(--color-border-strong);
  background: var(--color-surface);
  color: var(--color-text);
  border-radius: var(--radius-md);
  padding: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.18s ease, color 0.18s ease, border-color 0.18s ease;
}

.logout:hover {
  background: var(--color-primary-50);
  color: var(--color-primary-700);
  border-color: var(--color-primary-300);
}

@media (max-width: 960px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    transform: translateX(-100%);
    transition: transform 0.24s ease;
    box-shadow: var(--shadow-lg);
  }

  .sidebar.open {
    transform: translateX(0);
  }
}
</style>
