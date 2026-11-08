<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)

const form = reactive({
  email: '',
  password: '',
})

async function handleLogin() {
  if (!form.email || !form.password) {
    ElMessage.warning('请输入邮箱和密码')
    return
  }

  loading.value = true

  try {
    await authStore.login(
        form.email,
        form.password,
    )

    ElMessage.success('登录成功')

    await router.push('/problems')
  } catch (error: any) {
    console.error(error)

    if (error.response?.status === 401) {
      ElMessage.error('邮箱或密码错误')
    } else {
      ElMessage.error('登录失败，请检查服务器是否正常运行')
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <el-card class="login-card">
      <div class="login-header">
        <h1>Programming Tutor</h1>
        <p>在线编程学习平台</p>
      </div>

      <el-form
          :model="form"
          @submit.prevent="handleLogin"
      >
        <el-form-item label="邮箱">
          <el-input
              v-model="form.email"
              type="email"
              placeholder="请输入邮箱"
              size="large"
          />
        </el-form-item>

        <el-form-item label="密码">
          <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              show-password
              @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
        >
          登录
        </el-button>

        <div class="login-switch">
          还没有账号？
          <el-link type="primary" @click="$router.push('/register')">立即注册</el-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f7fa;
}

.login-card {
  width: 420px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  margin-bottom: 10px;
}

.login-header p {
  color: #909399;
}

.login-button {
  width: 100%;
  margin-top: 10px;
}

.login-switch {
  margin-top: 16px;
  text-align: center;
  font-size: 14px;
  color: #909399;
}
</style>