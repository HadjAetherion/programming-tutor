<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getProblems, type Problem } from '../api/problem'
import AppTopbar from '../components/AppTopbar.vue'

const router = useRouter()

const problems = ref<Problem[]>([])
const loading = ref(true)
const error = ref('')

async function loadProblems() {
  try {
    problems.value = await getProblems()
  } catch (err) {
    console.error(err)
    error.value = '题目加载失败'
  } finally {
    loading.value = false
  }
}

function openProblem(id: number) {
  router.push(`/problems/${id}`)
}

onMounted(() => {
  loadProblems()
})
</script>

<template>
  <div class="problem-list-page">
    <AppTopbar />
    <div class="problem-list">
      <h1>编程题库</h1>

    <div v-if="loading">
      正在加载...
    </div>

    <el-alert
        v-else-if="error"
        :title="error"
        type="error"
    />

    <div v-else class="problems">
      <el-card
          v-for="problem in problems"
          :key="problem.id"
          class="problem-card"
          shadow="hover"
          @click="openProblem(problem.id)"
      >
        <div class="problem-header">
          <h2>{{ problem.id }}. {{ problem.title }}</h2>

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

        <p>
          {{ problem.description }}
        </p>
      </el-card>
    </div>
    </div>
  </div>
</template>

<style scoped>
.problem-list-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.problem-list {
  max-width: 1000px;
  margin: 0 auto;
  padding: 40px;
}

.problems {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.problem-card {
  cursor: pointer;
}

.problem-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.problem-header h2 {
  margin: 0;
}

.problem-card p {
  color: #666;
}
</style>