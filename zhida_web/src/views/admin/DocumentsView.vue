<template>
  <div class="panel">
    <h2>文档管理</h2>
    <p class="muted">D1 占位。D3 接上传 / 列表 / 删除 / 空间分类。</p>
    <ul v-if="docs.length">
      <li v-for="d in docs" :key="d.id">
        {{ d.title }} · {{ d.space }} · v{{ d.version }}
      </li>
    </ul>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { listDocuments } from '../../api/documents'

const docs = ref([])
const error = ref('')

onMounted(async () => {
  try {
    docs.value = await listDocuments()
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
