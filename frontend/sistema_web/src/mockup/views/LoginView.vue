<template>
  <div class="login-shell">
    <div class="login-card">
      <div class="brand">
        <div class="brand-mark">P</div>
        <div>
          <h1>PROINTEL</h1>
          <p>Panel Mockup</p>
        </div>
      </div>

      <h2>Ingresar</h2>
      <p class="hint">Usuario: admin / Clave: admin123</p>

      <form @submit.prevent="submit" class="form">
        <label>
          Usuario
          <input v-model.trim="user" type="text" autocomplete="username" />
        </label>
        <label>
          Clave
          <input v-model="pass" type="password" autocomplete="current-password" />
        </label>
        <button type="submit">Entrar</button>
        <p v-if="error" class="error">{{ error }}</p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const emit = defineEmits<{ (e: 'login-ok'): void }>();
const user = ref('admin');
const pass = ref('admin123');
const error = ref('');

function submit() {
  if (user.value === 'admin' && pass.value === 'admin123') {
    localStorage.setItem('prointel_mock_auth', '1');
    localStorage.setItem('prointel_mock_user', user.value);
    error.value = '';
    emit('login-ok');
    return;
  }
  error.value = 'Credenciales invalidas';
}
</script>

<style scoped>
.login-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 20px;
  background:
    radial-gradient(circle at 14% 10%, rgba(245, 158, 11, 0.24), transparent 34%),
    radial-gradient(circle at 82% 16%, rgba(14, 165, 233, 0.22), transparent 33%),
    #071321;
}

.login-card {
  width: min(420px, 100%);
  border-radius: 16px;
  border: 1px solid #29405a;
  background: #0d1a29;
  padding: 22px;
  color: #e6edf7;
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.4);
}

.brand {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 14px;
}

.brand-mark {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-weight: 800;
  color: #0d1a29;
  background: linear-gradient(145deg, #f59e0b, #fb923c);
}

h1 {
  margin: 0;
  font-size: 1rem;
}

h2 {
  margin: 0;
  font-size: 1.2rem;
}

p {
  margin: 0;
}

.hint {
  margin-top: 6px;
  margin-bottom: 12px;
  color: #9eb2c7;
  font-size: 0.9rem;
}

.form {
  display: grid;
  gap: 10px;
}

label {
  display: grid;
  gap: 6px;
  font-size: 0.9rem;
}

input {
  border: 1px solid #2e4661;
  background: #091422;
  color: #e6edf7;
  border-radius: 10px;
  padding: 10px 11px;
}

input:focus {
  outline: 0;
  border-color: #f59e0b;
}

button {
  margin-top: 4px;
  border: 0;
  border-radius: 10px;
  padding: 10px;
  font-weight: 700;
  color: #08131f;
  background: linear-gradient(145deg, #f59e0b, #fb923c);
  cursor: pointer;
}

.error {
  color: #ffb4b4;
  font-size: 0.9rem;
}
</style>
