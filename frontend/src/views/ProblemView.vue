<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { getProblem, type Problem } from '../api/problem'
import {
  getSubmissions,
  runCode,
  submitCode,
  type RunCodeResult,
  type SubmissionSummary,
} from '../api/submission'

import {
  diagnoseSubmission,
  normalizeDiagnosis,
  type Diagnosis,
} from '../api/diagnosis'

import CodeEditor from '../components/CodeEditor.vue'
import DiagnosisPanel from '../components/DiagnosisPanel.vue'
import AppTopbar from '../components/AppTopbar.vue'
import { LANGUAGES, LANGUAGE_LABELS, findLanguage } from '../utils/languages'

const route = useRoute()
const router = useRouter()
// ==================== 题目 ====================

const problem = ref<Problem | null>(null)

const loading = ref(true)

const error = ref('')

// ==================== 代码 ====================

const language = ref('go')

const code = ref(findLanguage('go').template)

const monacoLanguage = computed(() => findLanguage(language.value).monacoId)

// 切换语言：替换为对应模板（提示会覆盖当前代码）
function handleLanguageChange(next: string) {
  if (next === language.value) {
    return
  }

  const hasCustomCode = code.value.trim() !== findLanguage(language.value).template.trim()
  if (hasCustomCode) {
    ElMessage.warning('切换语言会重置编辑器内容')
  }

  language.value = next
  code.value = findLanguage(next).template
}

// ==================== 运行代码 ====================

const running = ref(false)

const result = ref<RunCodeResult | null>(null)

async function handleRunCode() {
  if (running.value) {
    return
  }

  running.value = true
  result.value = null

  try {
    const data = await runCode({
      code: code.value,
      language: language.value,
    })

    result.value = data

    if (data.status === 'FINISHED') {
      ElMessage.success('代码运行完成')
    } else if (data.status === 'TIME_LIMIT') {
      ElMessage.warning('代码运行超时')
    } else {
      ElMessage.error('代码运行失败')
    }
  } catch (err) {
    console.error(err)
    ElMessage.error('代码运行请求失败')
  } finally {
    running.value = false
  }
}

// 运行结果文字
const statusText = computed(() => {
  if (!result.value) {
    return ''
  }

  switch (result.value.status) {
    case 'FINISHED':
      return '运行完成'

    case 'TIME_LIMIT':
      return '运行超时'

    case 'COMPILE_ERROR':
      return '编译错误'

    case 'RUNTIME_ERROR':
      return '运行错误'

    default:
      return result.value.status
  }
})

// 运行结果标签类型
const statusType = computed(() => {
  if (!result.value) {
    return 'info'
  }

  switch (result.value.status) {
    case 'FINISHED':
      return 'success'

    case 'TIME_LIMIT':
      return 'warning'

    case 'COMPILE_ERROR':
    case 'RUNTIME_ERROR':
      return 'danger'

    default:
      return 'info'
  }
})

// ==================== 提交代码 ====================

const submitting = ref(false)

const submitResult = ref<{
  id: number
  status: string
  passed_tests: number
  total_tests: number
  stdout: string
  stderr: string
  exit_code: number
  execution_time_ms: number
} | null>(null)

async function handleSubmit() {
  if (!problem.value) {
    return
  }

  if (submitting.value) {
    return
  }

  submitting.value = true
  submitResult.value = null
  diagnosis.value = null

  try {
    const data = await submitCode({
      problem_id: problem.value.id,
      code: code.value,
      language: language.value,
    })

    submitResult.value = data

    if (data.status === 'ACCEPTED') {
      ElMessage.success('提交通过')
    } else if (data.status === 'WRONG_ANSWER') {
      ElMessage.warning('答案错误')
    } else if (data.status === 'COMPILE_ERROR') {
      ElMessage.error('编译错误')
    } else if (data.status === 'RUNTIME_ERROR') {
      ElMessage.error('运行错误')
    } else if (data.status === 'TIME_LIMIT') {
      ElMessage.warning('运行超时')
    }

    // 未通过时触发诊断辅导（异步，不阻塞提交结果展示）
    if (data.status !== 'ACCEPTED' && data.id) {
      loadDiagnosis(data.id)
    }

    // 提交成功后刷新提交记录
    await loadSubmissions()
  } catch (err) {
    console.error('提交代码失败:', err)
    ElMessage.error('提交代码请求失败')
  } finally {
    submitting.value = false
  }
}

// ==================== 诊断辅导（多智能体） ====================

const diagnosis = ref<Diagnosis | null>(null)
const diagnosing = ref(false)

async function loadDiagnosis(submissionId: number) {
  if (diagnosing.value) {
    return
  }

  diagnosing.value = true
  diagnosis.value = null

  try {
    const data = await diagnoseSubmission(submissionId)
    diagnosis.value = normalizeDiagnosis(data)
  } catch (err) {
    console.error('诊断失败:', err)
    const detail =
      (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail
    ElMessage.error(
      detail ? `诊断辅导获取失败: ${detail}` : '诊断辅导获取失败',
    )
  } finally {
    diagnosing.value = false
  }
}

// ==================== 提交历史 ====================

const submissions = ref<SubmissionSummary[]>([])

const loadingSubmissions = ref(false)

async function loadSubmissions() {
  loadingSubmissions.value = true

  try {
    const data = await getSubmissions()
    submissions.value = data.submissions
  } catch (err) {
    console.error('加载提交记录失败:', err)
  } finally {
    loadingSubmissions.value = false
  }
}

// 只显示当前题目的提交记录
const problemSubmissions = computed(() => {
  if (!problem.value) {
    return []
  }

  return submissions.value.filter(
      (submission) => submission.problem_id === problem.value?.id,
  )
})

// ==================== 加载题目 ====================

async function loadProblem() {
  try {
    const id = Number(route.params.id)

    if (!Number.isInteger(id) || id <= 0) {
      error.value = '题目 ID 无效'
      return
    }

    problem.value = await getProblem(id)
  } catch (err) {
    console.error(err)
    error.value = '题目加载失败'
  } finally {
    loading.value = false
  }
}
//点击函数
function goToSubmission(id: number) {
  router.push(`/submissions/${id}`)
}

// ==================== 页面初始化 ====================

onMounted(async () => {
  await loadProblem()
  await loadSubmissions()
})
</script>

<template>
  <div class="problem-layout-page">
    <AppTopbar />
    <div class="problem-page">
      <!-- 加载中 -->
      <div v-if="loading" class="loading">
        正在加载题目...
      </div>

      <!-- 加载失败 -->
      <div v-else-if="error" class="error">
        {{ error }}
      </div>

      <!-- 页面主体 -->
      <div v-else-if="problem" class="content">
        <!-- ==================== 左侧：题目 ==================== -->
        <section class="problem-panel">
          <el-button text @click="router.push('/problems')" class="back-button">
            ← 返回题库
          </el-button>

          <h1>{{ problem.title }}</h1>

        <div class="difficulty">
          难度：

          <el-tag
              :type="
              problem.difficulty === 'easy'
                ? 'success'
                : problem.difficulty === 'medium'
                  ? 'warning'
                  : 'danger'
            "
          >
            {{ problem.difficulty }}
          </el-tag>
        </div>

        <div class="description">
          <h2>题目描述</h2>
          <p>{{ problem.description }}</p>

          <h2>输入</h2>
          <p>{{ problem.input_description }}</p>

          <h2>输出</h2>
          <p>{{ problem.output_description }}</p>

          <h2>约束</h2>
          <p>{{ problem.constraints }}</p>

          <h2>示例输入</h2>
          <pre>{{ problem.sample_input }}</pre>

          <h2>示例输出</h2>
          <pre>{{ problem.sample_output }}</pre>
        </div>
      </section>

      <!-- ==================== 右侧：代码 ==================== -->
      <section class="editor-panel">
        <!-- Monaco 编辑器 -->
        <div class="editor-container">
          <CodeEditor
              v-model="code"
              :language="monacoLanguage"
          />
        </div>

        <!-- ==================== 操作栏 ==================== -->
        <div class="editor-actions">
          <el-select
              :model-value="language"
              size="default"
              style="width: 120px"
              @update:model-value="handleLanguageChange"
          >
            <el-option
                v-for="item in LANGUAGES"
                :key="item.value"
                :label="item.label"
                :value="item.value"
            />
          </el-select>

          <el-button
              :loading="running"
              @click="handleRunCode"
          >
            {{ running ? '运行中...' : '运行代码' }}
          </el-button>

          <el-button
              type="primary"
              :loading="submitting"
              @click="handleSubmit"
          >
            {{ submitting ? '提交中...' : '提交代码' }}
          </el-button>
        </div>

        <!-- ==================== 提交结果 ==================== -->
        <div
            v-if="submitResult"
            class="submit-result"
        >
          <div class="submit-result-header">
            <span class="result-title">
              提交结果
            </span>

            <el-tag
                :type="
                submitResult.status === 'ACCEPTED'
                  ? 'success'
                  : submitResult.status === 'WRONG_ANSWER'
                    ? 'warning'
                    : 'danger'
              "
            >
              {{ submitResult.status }}
            </el-tag>
          </div>

          <div class="submit-info">
            <span>
              测试用例：
              <strong>
                {{ submitResult.passed_tests }}
                /
                {{ submitResult.total_tests }}
              </strong>
            </span>

            <span>
              执行时间：
              <strong>
                {{ submitResult.execution_time_ms }} ms
              </strong>
            </span>

            <span>
              Exit Code：
              <strong>
                {{ submitResult.exit_code }}
              </strong>
            </span>
          </div>

          <!-- 提交 stdout -->
          <div
              v-if="submitResult.stdout"
              class="output-section"
          >
            <div class="output-title">
              标准输出
            </div>

            <pre>{{ submitResult.stdout }}</pre>
          </div>

          <!-- 提交 stderr -->
          <div
              v-if="submitResult.stderr"
              class="output-section"
          >
            <div class="output-title">
              错误输出
            </div>

            <pre class="stderr">{{ submitResult.stderr }}</pre>
          </div>
        </div>

        <!-- ==================== 诊断辅导（多智能体协同） ==================== -->
        <DiagnosisPanel
            :diagnosis="diagnosis"
            :loading="diagnosing"
        />

        <!-- ==================== 运行结果 ==================== -->
        <div
            v-if="result"
            class="result-panel"
        >
          <div class="result-header">
            <span class="result-title">
              执行结果
            </span>

            <el-tag :type="statusType">
              {{ statusText }}
            </el-tag>
          </div>

          <!-- stdout -->
          <div
              v-if="result.stdout"
              class="output-section"
          >
            <div class="output-title">
              标准输出
            </div>

            <pre>{{ result.stdout }}</pre>
          </div>

          <!-- stderr -->
          <div
              v-if="result.stderr"
              class="output-section"
          >
            <div class="output-title">
              错误输出
            </div>

            <pre class="stderr">{{ result.stderr }}</pre>
          </div>

          <!-- exit code -->
          <div class="exit-code">
            Exit Code：
            {{ result.exit_code }}
          </div>
        </div>

        <!-- ==================== 提交历史 ==================== -->
        <div class="submission-history">
          <div class="history-header">
            <span class="result-title">
              提交记录
            </span>

            <span class="history-count">
              共 {{ problemSubmissions.length }} 次
            </span>
          </div>

          <!-- 加载 -->
          <div
              v-if="loadingSubmissions"
              class="history-empty"
          >
            正在加载...
          </div>

          <!-- 没有记录 -->
          <div
              v-else-if="problemSubmissions.length === 0"
              class="history-empty"
          >
            暂无提交记录
          </div>

          <!-- 提交记录 -->
          <div
              v-else
              class="submission-list"
          >
            <div
                v-for="submission in problemSubmissions"
                :key="submission.id"
                class="submission-item"
                @click="goToSubmission(submission.id)"
            >
              <span class="submission-id">
                #{{ submission.id }}
              </span>

              <el-tag size="small" effect="plain">
                {{ LANGUAGE_LABELS[submission.language] || submission.language }}
              </el-tag>

              <el-tag
                  size="small"
                  :type="
                  submission.status === 'ACCEPTED'
                    ? 'success'
                    : submission.status === 'WRONG_ANSWER'
                      ? 'warning'
                      : 'danger'
                "
              >
                {{ submission.status }}
              </el-tag>

              <el-tag
                  v-if="submission.has_diagnosis"
                  size="small"
                  type="success"
              >
                已诊断
              </el-tag>

              <span class="submission-time">
                {{ submission.execution_time_ms }} ms
              </span>

              <span class="submission-date">
                {{
                  new Date(
                      submission.created_at,
                  ).toLocaleString()
                }}
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>
    </div>
  </div>
</template>

<style scoped>
.problem-layout-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.problem-page {
  flex: 1;
  min-height: 0;
  padding: 20px;
  box-sizing: border-box;
}

.back-button {
  margin-bottom: 8px;
  padding-left: 0;
}

.loading,
.error {
  padding: 40px;
  text-align: center;
}

.content {
  display: flex;
  gap: 20px;
  height: 100%;
  min-height: 0;
}

/* ==================== 左侧题目 ==================== */

.problem-panel {
  width: 40%;
  overflow-y: auto;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-sizing: border-box;
}

.problem-panel h1 {
  margin-top: 0;
}

.difficulty {
  margin: 15px 0 25px;
}

.description {
  line-height: 1.8;
}

.description h2 {
  margin-top: 24px;
}

.description pre {
  padding: 12px;
  background: #f5f5f5;
  border-radius: 6px;
  overflow-x: auto;
}

/* ==================== 右侧编辑器 ==================== */

.editor-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.editor-container {
  height: 60vh;
  min-height: 400px;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

/* ==================== 操作栏 ==================== */

.editor-actions {
  padding: 12px 0;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* ==================== 提交结果 ==================== */

.submit-result {
  margin-bottom: 15px;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #fafafa;
}

.submit-result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 15px;
}

.submit-info {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  color: #666;
  font-size: 14px;
}

/* ==================== 运行结果 ==================== */

.result-panel {
  margin-bottom: 15px;
  max-height: 260px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  background: #fafafa;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 15px;
}

.result-title {
  font-size: 16px;
  font-weight: 600;
}

/* ==================== 输出 ==================== */

.output-section {
  margin-top: 12px;
}

.output-title {
  margin-bottom: 6px;
  font-weight: 600;
}

.output-section pre {
  margin: 0;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-word;
}

.output-section pre.stderr {
  background: #fff1f0;
}

.exit-code {
  margin-top: 12px;
  color: #666;
  font-size: 13px;
}

/* ==================== 提交历史 ==================== */

.submission-history {
  margin-bottom: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  background: #fff;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.history-count {
  color: #999;
  font-size: 13px;
}

.history-empty {
  padding: 20px;
  text-align: center;
  color: #999;
}

.submission-list {
  display: flex;
  flex-direction: column;
}

.submission-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px 8px;
  border-top: 1px solid #eee;
  font-size: 13px;
  cursor: pointer;
}

.submission-item:first-child {
  border-top: none;
}

.submission-id {
  width: 50px;
  color: #666;
}

.submission-time {
  width: 80px;
  color: #666;
}

.submission-date {
  margin-left: auto;
  color: #999;
}
/* ==================== 诊断辅导 ==================== */

.diagnosis-panel {
  margin-bottom: 15px;
  padding: 15px;
  border: 1px solid #d3e8ff;
  border-radius: 8px;
  background: #f6fbff;
}

.diagnosis-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.diagnosis-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 14px;
}

.diagnosis-label {
  color: #666;
}

.concept-tag {
  margin-right: 4px;
}

.diagnosis-section {
  margin-top: 10px;
}

.diagnosis-title {
  font-weight: 600;
  margin-bottom: 6px;
}

.diagnosis-text {
  margin: 0;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.diagnosis-empty {
  padding: 16px;
  text-align: center;
  color: #999;
}

/* ===== 多智能体协同面板 ===== */

.question-list {
  margin: 0;
  padding-left: 20px;
  line-height: 1.9;
}

.example-code {
  margin: 0;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: Consolas, Monaco, monospace;
}

.review-score-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.review-issue {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px dashed #eee;
  font-size: 14px;
}

.review-issue:last-child {
  border-bottom: none;
}

.issue-category {
  color: #666;
  font-weight: 600;
}

.issue-message {
  color: #333;
}

.issue-suggestion {
  width: 100%;
  padding-left: 2px;
  color: #888;
  font-size: 13px;
}

.plan-step {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 6px 0;
}

.step-detail {
  color: #444;
  font-size: 14px;
}

</style>
