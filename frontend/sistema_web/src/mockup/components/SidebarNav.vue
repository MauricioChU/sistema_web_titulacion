<template>
  <aside class="sidebar" :class="{ open: openOnMobile }">
    <div class="header">
      <div class="logo">P</div>
      <div>
        <h2>PROINTEL</h2>
        <small>Mockup</small>
      </div>
    </div>

    <nav>
      <button
        v-for="item in items"
        :key="item.key"
        class="item"
        :class="{ active: item.key === active }"
        @click="$emit('select', item.key)"
      >
        {{ item.label }}
      </button>
    </nav>

    <button class="logout" @click="$emit('logout')">Cerrar sesion</button>
  </aside>
</template>

<script setup lang="ts">
import type { MenuItem, MockViewKey } from '../types';

defineProps<{
  items: MenuItem[];
  active: MockViewKey;
  openOnMobile: boolean;
}>();

defineEmits<{
  (e: 'select', key: MockViewKey): void;
  (e: 'logout'): void;
}>();
</script>

<style scoped>
.sidebar {
  width: 235px;
  border-right: 1px solid #203349;
  background: #0c1826;
  padding: 14px;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 12px;
  z-index: 40;
}

.header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-weight: 800;
  color: #0d1a29;
  background: linear-gradient(145deg, #f59e0b, #fb923c);
}

h2 {
  margin: 0;
  font-size: 0.95rem;
  color: #e6edf7;
}

small {
  color: #9ab0c8;
}

nav {
  display: grid;
  gap: 8px;
  align-content: start;
}

.item {
  text-align: left;
  border: 1px solid transparent;
  background: transparent;
  color: #c8d7e6;
  border-radius: 10px;
  padding: 9px 10px;
  font-size: 0.92rem;
  cursor: pointer;
}

.item.active {
  border-color: rgba(59, 130, 246, 0.5);
  background: rgba(59, 130, 246, 0.17);
  color: #dbeafe;
}

.logout {
  border: 1px solid #2a3f57;
  background: #0b1522;
  color: #e5edf6;
  border-radius: 10px;
  padding: 9px;
  cursor: pointer;
}

@media (max-width: 900px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    transform: translateX(-100%);
    transition: transform 0.24s ease;
  }

  .sidebar.open {
    transform: translateX(0);
  }
}
</style>
