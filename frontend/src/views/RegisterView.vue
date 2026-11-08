<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirm: '',
})

function validate(): string | null {
  if (!form.username.trim()) return '请输入用户名'
  if (form.username.trim().length < 3) return '用户名至少 3 个字符'
  if (!form.email.trim()) return '请输入邮箱'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) return '邮箱格式不正确'
  if (form.password.length < 6) return '密码至少 6 位'
  if (form.password !== form.confirm) return '两次输入的密码不一致'
  return null
}

async function handleRegister() {
  const err = validate()
  if (err) {
    ElMessage.warning(err)
    return
  }

  loading.value = true

  try {
    await authStore.register(form.username.trim(), form.email.trim(), form.password)
    ElMessage.success('注册成功，已自动登录')
    await router.push('/problems')
  } catch (error: any) {
    if (error.response?.status === 409) {
      ElMessage.error('该邮箱已被注册')
    } else if (error.response?.status === 400) {
      ElMessage.error(error.response?.data?.error || '注册信息不合法')
    } else {
      ElMessage.error('注册失败，请检查服务器是否正常运行')
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <div class="auth-header">
        <h1>Programming Tutor</h1>
        <p>创建账号，开始你的编程学习</p>
      </div>

      <el-form :model="form" @submit.prevent="handleRegister">
        <el-form-item label="用户名">
          <el-input
            v-model="form.username"
            placeholder="3-50 个字符"
            size="large"
            maxlength="50"
          />
        </el-form-item>

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
            placeholder="至少 6 位"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item label="确认密码">
          <el-input
            v-model="form.confirm"
            type="password"
            placeholder="请再次输入密码"
            size="large"
            show-password
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          :loading="loading"
          class="auth-button"
          @click="handleRegister"
        >
          注册
        </el-button>

        <div class="auth-switch">
          已有账号？
          <el-link type="primary" @click="$router.push('/login')">返回登录</el-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f7fa;
}

.auth-card {
  width: 420px;
}

.auth-header {
  text-align: center;
  margin-bottom: 30px;
}

.auth-header h1 {
  margin-bottom: 10px;
}

.auth-header p {
  color: #909399;
}

.auth-button {
  width: 100%;
  margin-top: 10px;
}

.auth-switch {
  margin-top: 16px;
  text-align: center;
  font-size: 14px;
  color: #909399;
}
</style>
