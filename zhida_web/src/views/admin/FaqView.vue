<template>
  <div class="panel">
    <h2>新手指南 FAQ</h2>
    <p class="muted">D1 占位。D4 接从缺口发布 FAQ。</p>
    <ul v-if="faq.length">
      <li v-for="f in faq" :key="f.id">
        <strong>{{ f.question }}</strong>
        <div>{{ f.answer }}</div>
      </li>
    </ul>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { listFaq } from '../../api/faq'

const faq = ref([])
const error = ref('')

onMounted(async () => {
  try {
    faq.value = await listFaq()
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
li { margin-bottom: 12px; }
.error { color: #d93025; }
</style>
