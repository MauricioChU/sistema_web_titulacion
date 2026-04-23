<template>
  <div class="login-shell">
    <div class="login-card">
      <header class="brand">
        <div class="brand-mark" aria-hidden="true">P</div>
        <div class="brand-meta">
          <h1>PROINTEL</h1>
          <p>Panel operativo</p>
        </div>
      </header>

      <h2>Iniciar sesion</h2>
      <p class="hint">Usa tus credenciales corporativas para acceder.</p>

      <form class="form" @submit.prevent="submit">
        <label class="field">
          <span>Usuario</span>
          <input
            v-model.trim="user"
            type="text"
            autocomplete="username"
            :disabled="isSubmitting"
            placeholder="usuario.apellido"
          />
        </label>
        <label class="field">
          <span>Contrasena</span>
          <input
            v-model="pass"
            type="password"
            autocomplete="current-password"
            :disabled="isSubmitting"
            placeholder="********"
          />
        </label>

        <button type="submit" class="submit" :disabled="isSubmitting">
          {{ isSubmitting ? 'Validando...' : 'Entrar' }}
        </button>

        <p v-if="error" role="alert" class="error">{{ error }}</p>
      </form>

      <footer class="foot">
        <span>PROINTEL &copy; {{ new Date().getFullYear() }}</span>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { login } from '../api';
import type { SessionUser } from '../stores/sessionStore';

const emit = defineEmits<(e: 'login-ok', user: SessionUser) => void>();
const user = ref('');
const pass = ref('');
const error = ref('');
const isSubmitting = ref(false);

async function submit() {
  if (!user.value.trim() || !pass.value) {
    error.value = 'Completa usuario y contrasena.';
    return;
  }

  isSubmitting.value = true;
  try {
    const authUser = await login(user.value.trim(), pass.value);
    error.value = '';
    emit('login-ok', authUser);
  } catch (err) {
    error.value =
      err instanceof Error ? err.message : 'No se pudo iniciar sesion.';
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<style scoped>
.login-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at 18% 14%, rgba(110, 231, 183, 0.38), transparent 38%),
    radial-gradient(circle at 82% 88%, rgba(52, 211, 153, 0.28), transparent 40%),
    linear-gradient(180deg, #f0fbf4 0%, #e1f4ea 100%);
}

.login-card {
  width: min(440px, 100%);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  padding: 32px 28px 22px;
  color: var(--color-text);
  box-shadow: var(--shadow-lg);
  display: grid;
  gap: 16px;
}

.brand {
  display: flex;
  gap: 12px;
  align-items: center;
}

.brand-mark {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  font-weight: 800;
  font-size: 1.1rem;
  color: var(--color-text-invert);
  background: linear-gradient(135deg, var(--color-primary-600), var(--color-primary-400));
  box-shadow: var(--shadow-sm);
}

.brand-meta h1 {
  margin: 0;
  font-size: 1.05rem;
  color: var(--color-primary-800);
  letter-spacing: 0.04em;
}

.brand-meta p {
  margin: 2px 0 0;
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

h2 {
  margin: 4px 0 0;
  font-size: 1.35rem;
  color: var(--color-text);
}

.hint {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.form {
  display: grid;
  gap: 12px;
  margin-top: 4px;
}

.field {
  display: grid;
  gap: 6px;
  font-size: 0.9rem;
  color: var(--color-text-soft);
  font-weight: 500;
}

.field input {
  border: 1px solid var(--color-border-strong);
  background: var(--color-surface-2);
  color: var(--color-text);
  border-radius: var(--radius-md);
  padding: 11px 12px;
  font-size: 0.95rem;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.field input::placeholder {
  color: var(--color-text-muted);
}

.field input:focus {
  outline: 0;
  border-color: var(--color-primary-500);
  background: var(--color-surface);
  box-shadow: 0 0 0 4px var(--color-primary-100);
}

.field input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.submit {
  margin-top: 6px;
  border: 0;
  border-radius: var(--radius-md);
  padding: 12px;
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--color-text-invert);
  background: linear-gradient(135deg, var(--color-primary-600), var(--color-primary-400));
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.18s ease, filter 0.18s ease;
  box-shadow: var(--shadow-md);
}

.submit:hover:not(:disabled) {
  filter: brightness(1.05);
  transform: translateY(-1px);
}

.submit:active:not(:disabled) {
  transform: translateY(0);
}

.submit:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.error {
  margin: 0;
  color: var(--color-danger);
  background: #fff1f1;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md);
  padding: 8px 10px;
  font-size: 0.85rem;
}

.foot {
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.78rem;
  padding-top: 6px;
  border-top: 1px solid var(--color-border);
}
</style>
