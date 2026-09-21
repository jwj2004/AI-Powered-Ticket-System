import { ref } from 'vue'
import { getRole } from './authStorage'
import { listPendingUsers } from './users'

/** admin 登录后拉一次，供侧栏「用户管理」红点使用 */
export const pendingUserCount = ref(0)

export async function loadPendingUserCount() {
  if (getRole() !== 'admin') {
    pendingUserCount.value = 0
    return 0
  }
  const list = await listPendingUsers()
  pendingUserCount.value = list.length
  return pendingUserCount.value
}

export function clearPendingUserCount() {
  pendingUserCount.value = 0
}
