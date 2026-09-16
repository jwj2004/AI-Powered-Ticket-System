<template>
  <div class="panel">
    <div class="toolbar">
      <div>
        <h2>数据看板</h2>
        <p class="muted">今日概览与趋势 · mock /api/dashboard</p>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="data" class="cards">
      <div class="card">
        <div class="card-label">今日问答量</div>
        <div class="card-value">{{ data.total_today }}</div>
      </div>
      <div class="card">
        <div class="card-label">命中率</div>
        <div class="card-value">{{ hitRateText }}</div>
      </div>
      <div class="card">
        <div class="card-label">文档总数</div>
        <div class="card-value">{{ data.doc_count }}</div>
      </div>
      <div class="card">
        <div class="card-label">待处理缺口</div>
        <div class="card-value warn">{{ data.pending_gaps }}</div>
      </div>
    </div>

    <div v-if="data" class="charts">
      <div class="chart-box">
        <div class="chart-title">近 7 天问答量趋势</div>
        <div ref="trendEl" class="chart"></div>
      </div>
      <div class="chart-box">
        <div class="chart-title">热门问题 Top 5</div>
        <div ref="topEl" class="chart"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { getDashboard } from '../../api/dashboard'

const data = ref(null)
const error = ref('')
const trendEl = ref(null)
const topEl = ref(null)

let trendChart = null
let topChart = null

const hitRateText = computed(() => {
  if (!data.value) return '-'
  const rate = Number(data.value.hit_rate)
  if (Number.isNaN(rate)) return '-'
  return `${Math.round(rate * 100)}%`
})

function renderCharts() {
  if (!data.value) return

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
          name: '问答量',
          type: 'bar',
          data: trend.map((d) => d.count),
          itemStyle: { color: '#1a73e8', borderRadius: [4, 4, 0, 0] },
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
          itemStyle: { color: '#34a853', borderRadius: [0, 4, 4, 0] },
          barWidth: 16,
        },
      ],
    })
  }
}

function onResize() {
  trendChart?.resize()
  topChart?.resize()
}

onMounted(async () => {
  try {
    data.value = await getDashboard()
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
  trendChart = null
  topChart = null
})
</script>

<style scoped>
.panel {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #e8e8e8;
}
.toolbar { margin-bottom: 16px; }
h2 { margin: 0 0 4px; }
.muted { color: #888; margin: 0; font-size: 13px; }
.error { color: #d93025; }

.cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.card {
  background: #f8fafc;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 14px 16px;
}
.card-label { font-size: 13px; color: #666; }
.card-value {
  margin-top: 6px;
  font-size: 28px;
  font-weight: 700;
  color: #1a73e8;
}
.card-value.warn { color: #b26a00; }

.charts {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 12px;
}
.chart-box {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 12px;
}
.chart-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 8px;
}
.chart { height: 280px; width: 100%; }

@media (max-width: 960px) {
  .cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .charts { grid-template-columns: 1fr; }
}
</style>
