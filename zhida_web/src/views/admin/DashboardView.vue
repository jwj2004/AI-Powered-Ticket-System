<template>
  <div class="panel">
    <h2>数据看板</h2>
    <p class="muted">D1 占位。D5 接 ECharts。</p>
    <div v-if="data" class="stats">
      <div>今日问答：{{ data.total_today }}</div>
      <div>命中率：{{ data.hit_rate }}</div>
      <div>文档数：{{ data.doc_count }}</div>
      <div>待处理缺口：{{ data.pending_gaps }}</div>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getDashboard } from '../../api/dashboard'

const data = ref(null)
const error = ref('')

onMounted(async () => {
  try {
    data.value = await getDashboard()
  } catch (e) {
    error.value = e.detail || e.message
  }
})
</script>

<style scoped>
.panel {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #e8e8e8;
}
h2 { margin: 0 0 8px; }
.muted { color: #888; margin-top: 0; }
.stats { display: grid; gap: 8px; }
.error { color: #d93025; }
</style>
