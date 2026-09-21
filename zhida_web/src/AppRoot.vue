<template>
  <div class="app-root">
    <div v-if="netErrorVisible" class="net-banner" role="alert">
      <span>网络异常，请检查后端服务</span>
      <button type="button" class="net-close" aria-label="关闭" @click="dismissNetError">×</button>
    </div>
    <RouterView v-slot="{ Component }">
      <Transition name="page" mode="out-in">
        <component :is="Component" />
      </Transition>
    </RouterView>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { onNetworkError } from './api/networkError'

// 根壳：路由 + 全局网络异常红条。旧工单副驾页仍在 App.vue，不挂路由。

const netErrorVisible = ref(false)
let hideTimer = null
let unsubscribe = null

function showNetError() {
  netErrorVisible.value = true
  if (hideTimer) clearTimeout(hideTimer)
  // 自动收起，避免一直挡内容；可手动点 × 关闭
  hideTimer = setTimeout(() => {
    netErrorVisible.value = false
  }, 6000)
}

function dismissNetError() {
  netErrorVisible.value = false
  if (hideTimer) clearTimeout(hideTimer)
}

onMounted(() => {
  unsubscribe = onNetworkError(showNetError)
})

onUnmounted(() => {
  if (unsubscribe) unsubscribe()
  if (hideTimer) clearTimeout(hideTimer)
})
</script>

<style scoped>
.app-root {
  min-height: 100vh;
}
.net-banner {
  position: sticky;
  top: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 10px 40px;
  background: #dc2626;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.35);
}
.net-close {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  border: none;
  background: transparent;
  color: #fff;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  padding: 4px 8px;
  opacity: 0.85;
}
.net-close:hover {
  opacity: 1;
}
</style>
