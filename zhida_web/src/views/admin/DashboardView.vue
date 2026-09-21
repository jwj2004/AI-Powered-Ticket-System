<template>
  <div class="panel">
    <div class="toolbar">
      <div>
        <h2>数据看板</h2>
        <p class="muted">今日概览与分布 · /api/dashboard</p>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="data" class="cards">
      <div class="card">
        <svg class="card-ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 6h14M5 12h14M5 18h8" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
        <div class="card-label">今日问答量</div>
        <div class="card-value">{{ data.total_today }}</div>
      </div>
      <div class="card">
        <svg class="card-ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l2.2 6.6H21l-5.4 4 2 6.4L12 16.8 6.4 20l2-6.4L3 9.6h6.8z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg>
        <div class="card-label">命中率</div>
        <div class="card-value">{{ hitRateText }}</div>
      </div>
      <div class="card">
        <svg class="card-ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h7l5 5v13H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M14 3v5h5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>
        <div class="card-label">文档总数</div>
        <div class="card-value">{{ data.doc_count }}</div>
      </div>
      <div class="card">
        <svg class="card-ico" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M12 8v5M12 16.5h.01" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
        <div class="card-label">待处理缺口</div>
        <div class="card-value warn">{{ data.pending_gaps }}</div>
      </div>
    </div>

    <div v-if="data || citeTop.length" class="charts">
      <div v-if="data" class="chart-box">
        <div class="chart-title">{{ data.chart_trend_title || '置信度分布' }}</div>
        <div ref="trendEl" class="chart"></div>
      </div>
      <div v-if="data" class="chart-box">
        <div class="chart-title">热门问题 Top 5</div>
        <div ref="topEl" class="chart"></div>
      </div>
      <div v-if="citeTop.length" class="chart-box cite-box">
        <div class="chart-title">文档引用 Top5</div>
        <div ref="citeEl" class="chart"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { getDashboard } from '../../api/dashboard'
import { getCitationTop } from '../../api/stats'

const data = ref(null)
const citeTop = ref([])
const error = ref('')
const trendEl = ref(null)
const topEl = ref(null)
const citeEl = ref(null)

let trendChart = null
let topChart = null
let citeChart = null

const hitRateText = computed(() => {
  if (!data.value) return '-'
  const rate = Number(data.value.hit_rate)
  if (Number.isNaN(rate)) return '-'
  return `${Math.round(rate * 100)}%`
})

function renderCharts() {
  if (data.value) {
  const trend = data.value.daily_trend || []
  const tops = (data.value.top_questions || []).slice(0, 5)

  if (trendEl.value) {
    if (!trendChart) trendChart = echarts.init(trendEl.value)
    trendChart.setOption({
      grid: { left: 40, right: 20, top: 30, bottom: 30 },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: trend.map((d) => d.date),
      },
      yAxis: { type: 'value', minInterval: 1 },
      series: [
        {
          name: '数量',
          type: 'bar',
          data: trend.map((d) => d.count),
          itemStyle: { color: '#667eea', borderRadius: [4, 4, 0, 0] },
          barWidth: 28,
        },
      ],
    })
  }

  if (topEl.value) {
    if (!topChart) topChart = echarts.init(topEl.value)
    const names = tops.map((t) => t.question).reverse()
    const values = tops.map((t) => t.count).reverse()
    topChart.setOption({
      grid: { left: 120, right: 30, top: 20, bottom: 20 },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'value', minInterval: 1 },
      yAxis: {
        type: 'category',
        data: names,
        axisLabel: { width: 100, overflow: 'truncate' },
      },
      series: [
        {
          name: '次数',
          type: 'bar',
          data: values,
          itemStyle: { color: '#764ba2', borderRadius: [0, 4, 4, 0] },
          barWidth: 16,
        },
      ],
    })
  }
  }

  if (citeEl.value) {
    if (!citeChart) citeChart = echarts.init(citeEl.value)
    const rows = [...citeTop.value].reverse()
    citeChart.setOption({
      grid: { left: 140, right: 30, top: 20, bottom: 20 },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'value', minInterval: 1 },
      yAxis: {
        type: 'category',
        data: rows.map((d) => d.title),
        axisLabel: { width: 120, overflow: 'truncate' },
      },
      series: [
        {
          name: '引用次数',
          type: 'bar',
          data: rows.map((d) => d.citation_count),
          itemStyle: { color: '#ca8a04', borderRadius: [0, 4, 4, 0] },
          barWidth: 16,
        },
      ],
    })
  }
}

function onResize() {
  trendChart?.resize()
  topChart?.resize()
  citeChart?.resize()
}

onMounted(async () => {
  try {
    const [dash, cites] = await Promise.all([
      getDashboard().catch((e) => {
        error.value = e.detail || e.message || '加载看板失败'
        return null
      }),
      getCitationTop(5),
    ])
    data.value = dash
    citeTop.value = cites
    await nextTick()
    renderCharts()
    window.addEventListener('resize', onResize)
  } catch (e) {
    error.value = e.detail || e.message || '加载看板失败'
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  trendChart?.dispose()
  topChart?.dispose()
  citeChart?.dispose()
  trendChart = null
  topChart = null
  citeChart = null
})
</script>

<style scoped>
.panel {
  background: transparent;
  padding: 0;
  border: none;
}
.toolbar { margin-bottom: 16px; }
h2 { margin: 0 0 4px; font-size: 18px; }
.muted { color: var(--color-text-secondary, #6b7280); margin: 0; font-size: 13px; }
.error { color: var(--color-danger, #dc2626); }

.cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}
.card {
  position: relative;
  overflow: hidden;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 12px;
  padding: 18px 20px 16px;
  box-shadow: var(--shadow);
}
.card::before {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 4px;
  background: var(--gradient);
}
.card-ico { width: 22px; height: 22px; color: #667eea; margin-bottom: 8px; }
.card-label {
  font-size: 14px;
  color: #94a3b8;
  font-weight: 500;
}
.card-value {
  margin-top: 10px;
  font-size: 32px;
  font-weight: 700;
  line-height: 1.1;
  color: var(--color-primary, #2563eb);
}
.card-value.warn { color: var(--color-warn, #b45309); }

.charts {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 14px;
}
.cite-box { grid-column: 1 / -1; }
.chart-box {
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: var(--shadow, 0 1px 3px rgba(15, 23, 42, 0.06));
}
.chart-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 8px;
}
.chart { height: 280px; width: 100%; }

@media (max-width: 720px) {
  .cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .charts { grid-template-columns: 1fr; }
}
</style>
