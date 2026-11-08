<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import {
  getSubmission,
  type Submission,
} from '../api/submission'
import { getDiagnosis, type Diagnosis } from '../api/diagnosis'
import DiagnosisPanel from '../components/DiagnosisPanel.vue'
import AppTopbar from '../components/AppTopbar.vue'
import { LANGUAGE_LABELS } from '../utils/languages'

const route = useRoute()
const router = useRouter()

// 从题目页点进来时返回题目页，直接访问时返回题库
function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/problems')
  }
}

const submission = ref<Submission | null>(null)

const loading = ref(true)

const error = ref('')

const diagnosis = ref<Diagnosis | null>(null)

async function loadSubmission() {
  try {
    const id = Number(route.params.id)

    if (!Number.isInteger(id) || id <= 0) {
      error.value = '提交记录 ID 无效'
      return
    }

    submission.value = await getSubmission(id)
    await loadDiagnosis()
  } catch (err) {
    console.error(err)
    error.value = '提交记录加载失败'
    ElMessage.error('提交记录加载失败')
  } finally {
    loading.value = false
  }
}

async function loadDiagnosis() {
  if (!submission.value) {
    return
  }

  try {
    diagnosis.value = await getDiagnosis(submission.value.id)
  } catch (err) {
    console.error('加载诊断记录失败:', err)
    diagnosis.value = null
  }
}

function statusType(status: string) {
  switch (status) {
    case 'ACCEPTED':
      return 'success'

    case 'WRONG_ANSWER':
      return 'warning'

    case 'TIME_LIMIT':
      return 'warning'

    case 'COMPILE_ERROR':
    case 'RUNTIME_ERROR':
      return 'danger'

    default:
      return 'info'
  }
}

onMounted(() => {
  loadSubmission()
})
</script>

<template>
  <div class="submission-layout-page">
    <AppTopbar />
    <div class="submission-page">
      <el-button text class="back-button" @click="goBack">← 返回</el-button>
    <!-- 加载 -->
    <div
        v-if="loading"
        class="loading"
    >
      正在加载提交记录...
    </div>

    <!-- 错误 -->
    <div
        v-else-if="error"
        class="error"
    >
      {{ error }}
    </div>

    <!-- 内容 -->
    <div
        v-else-if="submission"
        class="content"
    >
      <div class="header">
        <div>
          <h1>
            提交 #{{ submission.id }}
          </h1>

          <p class="time">
            {{ new Date(submission.created_at).toLocaleString() }}
          </p>
        </div>

        <el-tag
            size="large"
            :type="statusType(submission.status)"
        >
          {{ submission.status }}
        </el-tag>
      </div>

      <!-- 基本信息 -->
      <div class="info-card">
        <div class="info-item">
          <span class="label">
            题目
          </span>

          <span>
            #{{ submission.problem_id }}
          </span>
        </div>

        <div class="info-item">
          <span class="label">
            语言
          </span>

          <span>
            {{ LANGUAGE_LABELS[submission.language] || submission.language }}
          </span>
        </div>

        <div class="info-item">
          <span class="label">
            Exit Code
          </span>

          <span>
            {{ submission.exit_code }}
          </span>
        </div>

        <div class="info-item">
          <span class="label">
            执行时间
          </span>

          <span>
            {{ submission.execution_time_ms }} ms
          </span>
        </div>
      </div>

      <!-- 诊断辅导（多智能体协同结果） -->
      <section
          v-if="diagnosis"
          class="section"
      >
        <DiagnosisPanel
            :diagnosis="diagnosis"
            :loading="false"
        />
      </section>

      <!-- 代码 -->
      <section class="section">
        <h2>
          提交代码
          <el-tag size="small" effect="plain">
            {{ LANGUAGE_LABELS[submission.language] || submission.language }}
          </el-tag>
        </h2>

        <pre class="code">{{ submission.code }}</pre>
      </section>

      <!-- stdout -->
      <section
          v-if="submission.stdout"
          class="section"
      >
        <h2>标准输出</h2>

        <pre>{{ submission.stdout }}</pre>
      </section>

      <!-- stderr -->
      <section
          v-if="submission.stderr"
          class="section"
      >
        <h2>错误输出</h2>

        <pre class="stderr">{{ submission.stderr }}</pre>
      </section>
    </div>
    </div>
  </div>
</template>

<style scoped>
.submission-layout-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.submission-page {
  min-height: calc(100vh - 52px);
  padding: 30px;
  box-sizing: border-box;
}

.back-button {
  padding-left: 0;
  margin-bottom: 8px;
}

.loading,
.error {
  padding: 60px;
  text-align: center;
}

.content {
  max-width: 1000px;
  margin: 0 auto;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 25px;
}

.header h1 {
  margin: 0;
}

.time {
  margin-top: 8px;
  color: #999;
  font-size: 14px;
}

.info-card {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-bottom: 25px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #fafafa;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.label {
  color: #999;
  font-size: 13px;
}

.section {
  margin-bottom: 25px;
}

.section h2 {
  margin-bottom: 10px;
  font-size: 18px;
}

.section pre {
  margin: 0;
  padding: 15px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  border-radius: 8px;
  background: #f5f5f5;
  font-family: Consolas, Monaco, monospace;
  line-height: 1.6;
}

.section pre.code {
  min-height: 200px;
}

.section pre.stderr {
  background: #fff1f0;
}
</style>
