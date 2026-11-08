<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = computed(() => authStore.user?.username || '')

const NAV = [
  { label: '题库', path: '/problems' },
  { label: '学习仪表盘', path: '/dashboard' },
]

function go(path: string) {
  router.push(path)
}

function handleLogout() {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<template>
  <header class="app-topbar">
    <span class="brand" @click="go('/problems')">Programming Tutor</span>

    <nav class="nav">
      <el-button
        v-for="item in NAV"
        :key="item.path"
        text
        :type="$route.path === item.path ? 'primary' : undefined"
        @click="go(item.path)"
      >
        {{ item.label }}
      </el-button>
    </nav>

    <div class="user-area">
      <span v-if="username" class="username">{{ username }}</span>
      <el-button text @click="handleLogout">退出登录</el-button>
    </div>
  </header>
</template>

<style scoped>
.app-topbar {
  display: flex;
  align-items: center;
  gap: 24px;
  height: 52px;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.brand {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
  cursor: pointer;
  white-space: nowrap;
}

.nav {
  display: flex;
  gap: 4px;
}

.user-area {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.username {
  font-size: 13px;
  color: #909399;
}
</style>
