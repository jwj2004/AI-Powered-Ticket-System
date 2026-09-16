<template>
  <div class="panel">
    <h2>知识缺口</h2>
    <p class="muted">D1 占位。D4 接榜单与补答案。</p>
    <ul v-if="gaps.length">
      <li v-for="g in gaps" :key="g.gap_id">
        #{{ g.gap_id }} {{ g.question }}（{{ g.username }} · {{ g.status }}）
      </li>
    </ul>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { listGaps } from '../../api/gaps'

const gaps = ref([])
const error = ref('')

onMounted(async () => {
  try {
    gaps.value = await listGaps()
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
ul { padding-left: 18px; }
.error { color: #d93025; }
</style>
