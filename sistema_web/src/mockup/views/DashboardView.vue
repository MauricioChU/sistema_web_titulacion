<template>
  <section class="dashboard">
    <header class="head">
      <div>
        <h2>Dashboard</h2>
        <p>Resumen operativo de PROINTEL</p>
      </div>
      <span class="badge">UI Mockup</span>
    </header>

    <div class="kpis">
      <article class="kpi">
        <h3>Costo total</h3>
        <p>S/ 128,400</p>
        <small class="trend up">▲ +12.4% vs mes anterior</small>
      </article>
      <article class="kpi">
        <h3>Tecnicos trabajando</h3>
        <p>26</p>
        <small class="trend up">▲ +3 tecnicos hoy</small>
      </article>
      <article class="kpi">
        <h3>Tecnicos en ruta</h3>
        <p>11</p>
        <small class="trend down">▼ -2 en la ultima hora</small>
      </article>
      <article class="kpi">
        <h3>Numero de pedidos</h3>
        <p>73</p>
        <small class="trend up">▲ +8% esta semana</small>
      </article>
    </div>

    <div class="charts-grid">
      <article class="card">
        <h4>Barras de costo semanal</h4>
        <div class="chart-box">
          <Bar :data="costData" :options="barOptions" />
        </div>
      </article>

      <article class="card">
        <h4>Tecnicos por estado</h4>
        <div class="chart-box">
          <Bar :data="techData" :options="barOptions" />
        </div>
      </article>

      <article class="card wide">
        <h4>Servicios mas trabajados</h4>
        <div class="chart-box">
          <Bar :data="serviceData" :options="barOptions" />
        </div>
      </article>

      <article class="card">
        <h4>Distribucion de pedidos</h4>
        <div class="chart-box pie-box">
          <Doughnut :data="requestSplitData" :options="pieOptions" />
        </div>
      </article>

      <article class="card">
        <h4>Costos por categoria</h4>
        <div class="chart-box pie-box">
          <Pie :data="costCategoryData" :options="pieOptions" />
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Bar, Doughnut, Pie } from 'vue-chartjs';
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Title,
  Tooltip,
  type ChartOptions,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

const barOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
  },
  scales: {
    x: {
      ticks: { color: '#94a3b8' },
      grid: { display: false },
    },
    y: {
      ticks: { color: '#94a3b8' },
      grid: { color: 'rgba(255,255,255,0.08)' },
    },
  },
};

const pieOptions: ChartOptions<'doughnut' | 'pie'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        color: '#c7d5e4',
        boxWidth: 12,
        boxHeight: 12,
      },
    },
  },
};

const costData = {
  labels: ['S1', 'S2', 'S3', 'S4'],
  datasets: [
    {
      data: [24100, 31800, 27900, 44600],
      backgroundColor: ['#f59e0b', '#fb923c', '#fbbf24', '#f97316'],
      borderRadius: 7,
    },
  ],
};

const techData = {
  labels: ['Trabajando', 'En ruta', 'Disponibles'],
  datasets: [
    {
      data: [26, 11, 8],
      backgroundColor: ['#2563eb', '#0ea5e9', '#38bdf8'],
      borderRadius: 7,
    },
  ],
};

const serviceData = {
  labels: ['Remodelacion', 'Pintura', 'Cableado', 'Mantenimiento', 'Instalacion'],
  datasets: [
    {
      data: [21, 27, 31, 29, 17],
      backgroundColor: ['#10b981', '#22c55e', '#14b8a6', '#4ade80', '#65a30d'],
      borderRadius: 7,
    },
  ],
};

const requestSplitData = {
  labels: ['Atendidos', 'En proceso', 'Pendientes'],
  datasets: [
    {
      data: [42, 20, 11],
      backgroundColor: ['#22c55e', '#f59e0b', '#ef4444'],
      borderColor: '#0f1c2b',
      borderWidth: 2,
    },
  ],
};

const costCategoryData = {
  labels: ['Materiales', 'Mano de obra', 'Movilidad', 'Otros'],
  datasets: [
    {
      data: [44, 36, 12, 8],
      backgroundColor: ['#3b82f6', '#14b8a6', '#8b5cf6', '#f97316'],
      borderColor: '#0f1c2b',
      borderWidth: 2,
    },
  ],
};
</script>

<style scoped>
.dashboard {
  display: grid;
  gap: 12px;
  max-height: calc(100dvh - 24px);
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

h2 {
  margin: 0;
  color: #e6edf7;
}

.head p {
  margin: 3px 0 0;
  color: #96abc2;
}

.badge {
  border: 1px solid rgba(245, 158, 11, 0.45);
  color: #fbbf24;
  background: rgba(245, 158, 11, 0.17);
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
}

.kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.kpi {
  background: #0f1c2b;
  border: 1px solid #21364d;
  border-radius: 12px;
  padding: 10px;
}

.kpi h3 {
  margin: 0;
  color: #95a8be;
  font-size: 0.78rem;
}

.kpi p {
  margin: 6px 0 0;
  color: #f8fafc;
  font-size: 1.06rem;
  font-weight: 700;
}

.trend {
  display: block;
  margin-top: 5px;
  font-size: 0.75rem;
}

.trend.up {
  color: #4ade80;
}

.trend.down {
  color: #fca5a5;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  min-height: 0;
}

.card {
  height: 280px;
  max-height: 280px;
  background: #0f1c2b;
  border: 1px solid #21364d;
  border-radius: 12px;
  padding: 10px;
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 0;
}

.card h4 {
  margin: 0 0 8px;
  color: #e7eef8;
  font-size: 0.9rem;
}

.chart-box {
  position: relative;
  min-height: 0;
  height: 100%;
}

.pie-box {
  max-height: 220px;
}

.wide {
  grid-column: 1 / -1;
  height: 300px;
  max-height: 300px;
}

@media (max-width: 1100px) {
  .kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .card,
  .wide {
    height: 260px;
    max-height: 260px;
  }
}

@media (max-width: 560px) {
  .kpis {
    grid-template-columns: 1fr;
  }

  .card,
  .wide {
    height: 240px;
    max-height: 240px;
  }
}
</style>
