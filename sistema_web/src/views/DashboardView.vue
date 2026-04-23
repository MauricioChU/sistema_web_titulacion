<template>
  <section class="dashboard">
    <header class="head">
      <div>
        <h2>Dashboard</h2>
        <p>Resumen operativo de PROINTEL</p>
      </div>
      <span class="badge">Panel operativo</span>
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
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  type ChartOptions,
  Legend,
  LinearScale,
  Title,
  Tooltip,
} from 'chart.js';
import { Bar, Doughnut, Pie } from 'vue-chartjs';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
);

const GREEN_PALETTE = [
  '#059669',
  '#10b981',
  '#34d399',
  '#6ee7b7',
  '#a7f3d0',
  '#4ade80',
];
const INFO_COLOR = '#0ea5e9';
const WARNING_COLOR = '#f59e0b';
const DANGER_COLOR = '#dc2626';
const SURFACE_BORDER = '#ffffff';

const barOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
  },
  scales: {
    x: {
      ticks: { color: '#5f7b70' },
      grid: { display: false },
    },
    y: {
      ticks: { color: '#5f7b70' },
      grid: { color: 'rgba(16, 185, 129, 0.12)' },
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
        color: '#2f5c4a',
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
      backgroundColor: [
        GREEN_PALETTE[0],
        GREEN_PALETTE[1],
        GREEN_PALETTE[2],
        GREEN_PALETTE[5],
      ],
      borderRadius: 7,
    },
  ],
};

const techData = {
  labels: ['Trabajando', 'En ruta', 'Disponibles'],
  datasets: [
    {
      data: [26, 11, 8],
      backgroundColor: [GREEN_PALETTE[1], GREEN_PALETTE[2], GREEN_PALETTE[5]],
      borderRadius: 7,
    },
  ],
};

const serviceData = {
  labels: [
    'Remodelacion',
    'Pintura',
    'Cableado',
    'Mantenimiento',
    'Instalacion',
  ],
  datasets: [
    {
      data: [21, 27, 31, 29, 17],
      backgroundColor: GREEN_PALETTE.slice(0, 5),
      borderRadius: 7,
    },
  ],
};

const requestSplitData = {
  labels: ['Atendidos', 'En proceso', 'Pendientes'],
  datasets: [
    {
      data: [42, 20, 11],
      backgroundColor: [GREEN_PALETTE[1], WARNING_COLOR, DANGER_COLOR],
      borderColor: SURFACE_BORDER,
      borderWidth: 2,
    },
  ],
};

const costCategoryData = {
  labels: ['Materiales', 'Mano de obra', 'Movilidad', 'Otros'],
  datasets: [
    {
      data: [44, 36, 12, 8],
      backgroundColor: [
        GREEN_PALETTE[1],
        GREEN_PALETTE[3],
        INFO_COLOR,
        GREEN_PALETTE[5],
      ],
      borderColor: SURFACE_BORDER,
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
  color: var(--color-text);
}

.head p {
  margin: 3px 0 0;
  color: var(--color-text-muted);
}

.badge {
  border: 1px solid var(--color-primary-300);
  color: var(--color-primary-700);
  background: var(--color-primary-100);
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
}

.kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.kpi {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 14px;
  box-shadow: var(--shadow-sm);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.kpi:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.kpi h3 {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 0.78rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  font-weight: 600;
}

.kpi p {
  margin: 8px 0 0;
  color: var(--color-primary-800);
  font-size: 1.4rem;
  font-weight: 800;
}

.trend {
  display: block;
  margin-top: 6px;
  font-size: 0.78rem;
}

.trend.up {
  color: var(--color-primary-600);
}

.trend.down {
  color: var(--color-danger);
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  min-height: 0;
}

.card {
  height: 280px;
  max-height: 280px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 14px;
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 0;
  box-shadow: var(--shadow-sm);
}

.card h4 {
  margin: 0 0 10px;
  color: var(--color-primary-800);
  font-size: 0.92rem;
  font-weight: 700;
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
