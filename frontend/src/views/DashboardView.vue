<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getMyLLMStats, getMyMastery, type LLMStat, type MasteryItem } from '../api/dashboard'
import { LANGUAGES, LANGUAGE_LABELS } from '../utils/languages'
import AppTopbar from '../components/AppTopbar.vue'

const mastery = ref<MasteryItem[]>([])
const stats = ref<LLMStat[]>([])
const loading = ref(true)
const error = ref('')

// 图表色板（浅色模式，已过 CVD/对比度校验：端侧=蓝，云端=橙）
const EDGE_COLOR = '#2a78d6'
const CLOUD_COLOR = '#eb6834'

const ROLE_LABELS: Record<string, string> = {
  diagnosis: '诊断',
  review: '审查',
  feedback: '反馈',
  planning: '规划',
}

const ROLE_ORDER = ['diagnosis', 'review', 'feedback', 'planning']

onMounted(async () => {
  try {
    const [m, s] = await Promise.all([getMyMastery(), getMyLLMStats()])
    mastery.value = m
    stats.value = s
  } catch (e: any) {
    error.value = e?.response?.data?.error || e?.message || '加载失败'
  } finally {
    loading.value = false
  }
})

const totalCalls = computed(() => stats.value.reduce((sum, s) => sum + Number(s.calls), 0))

const weightedAvg = (tier: string) => {
  const rows = stats.value.filter((s) => s.model_tier === tier && Number(s.calls) > 0)
  const calls = rows.reduce((sum, s) => sum + Number(s.calls), 0)
  if (!calls) return 0
  const total = rows.reduce((sum, s) => sum + Number(s.calls) * Number(s.avg_latency_ms), 0)
  return total / calls
}

const avgEdge = computed(() => weightedAvg('edge'))
const avgCloud = computed(() => weightedAvg('cloud'))

const edgeShare = computed(() => {
  if (!totalCalls.value) return 0
  const edgeCalls = stats.value
    .filter((s) => s.model_tier === 'edge')
    .reduce((sum, s) => sum + Number(s.calls), 0)
  return Math.round((edgeCalls / totalCalls.value) * 100)
})

// 各角色 × 模型层的延迟分组数据（缺该层则不渲染该条）
interface RoleGroup {
  role: string
  label: string
  edge?: number
  cloud?: number
}

const latencyGroups = computed<RoleGroup[]>(() => {
  const find = (role: string, tier: string) =>
    stats.value.find((s) => s.agent_role === role && s.model_tier === tier)

  return ROLE_ORDER.map((role) => ({
    role,
    label: ROLE_LABELS[role] || role,
    edge: find(role, 'edge')?.avg_latency_ms,
    cloud: find(role, 'cloud')?.avg_latency_ms,
  })).filter((g) => g.edge !== undefined || g.cloud !== undefined)
})

const latencyMax = computed(() => {
  const vals: number[] = []
  latencyGroups.value.forEach((g) => {
    vals.push(g.edge ?? 0, g.cloud ?? 0)
  })
  return Math.max(...vals, 1)
})

const fmtLatency = (ms?: number) => {
  if (!ms || ms <= 0) return '—'
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${Math.round(ms)}ms`
}

const fmtTokens = (n: number) => (n >= 1000 ? `${(n / 1000).toFixed(1)}k` : `${Math.round(n)}`)

// ===== 掌握度按语言过滤 =====
const masteryLanguage = ref('all')

const filteredMastery = computed(() =>
  masteryLanguage.value === 'all'
    ? mastery.value
    : mastery.value.filter((m) => m.language === masteryLanguage.value),
)

// 只展示学生实际有数据的语言，避免下拉里出现空选项
const masteryLanguages = computed(() => {
  const present = new Set(mastery.value.map((m) => m.language))
  return LANGUAGES.filter((l) => present.has(l.value))
})

const filteredWeakness = computed(
  () => filteredMastery.value.filter((m) => m.mastery < 0.4).length,
)
</script>

<template>
  <div class="dashboard-layout-page">
    <AppTopbar />
    <div class="dashboard">
      <div class="topbar">
        <h1>学习仪表盘</h1>
      </div>

    <el-alert v-if="error" :title="error" type="error" show-icon />
    <div v-else-if="loading" class="loading">正在加载...</div>

    <el-empty
      v-else-if="!mastery.length && !stats.length"
      description="还没有学情数据：先去题库做一道题并触发 AI 诊断"
    />

    <template v-else>
      <!-- KPI 行：推理成本-延迟总览（创新点③） -->
      <div class="kpi-row">
        <div class="stat-tile">
          <div class="stat-value">{{ totalCalls }}</div>
          <div class="stat-label">AI 调用总次数</div>
        </div>
        <div class="stat-tile">
          <div class="stat-value">
            {{ edgeShare }}<span class="stat-unit">%</span>
          </div>
          <div class="stat-label">端侧小模型调用占比</div>
        </div>
        <div class="stat-tile">
          <div class="stat-value">
            <span class="dot" :style="{ background: EDGE_COLOR }"></span>
            {{ fmtLatency(avgEdge) }}
          </div>
          <div class="stat-label">端侧平均延迟</div>
        </div>
        <div class="stat-tile">
          <div class="stat-value">
            <span class="dot" :style="{ background: CLOUD_COLOR }"></span>
            {{ fmtLatency(avgCloud) }}
          </div>
          <div class="stat-label">云端平均延迟</div>
        </div>
      </div>

      <!-- 掌握度：排名横向条形图（最薄弱在前） -->
      <el-card class="panel" shadow="never">
        <template #header>
          <div class="panel-title">
            知识点掌握度
            <span class="muted">（共 {{ filteredMastery.length }} 项，最薄弱在前）</span>
            <el-tag v-if="filteredWeakness" type="danger" size="small">
              薄弱 {{ filteredWeakness }} 项
            </el-tag>
            <el-select
              v-if="masteryLanguages.length > 1"
              v-model="masteryLanguage"
              size="small"
              style="width: 110px; margin-left: auto"
            >
              <el-option label="全部语言" value="all" />
              <el-option
                v-for="l in masteryLanguages"
                :key="l.value"
                :label="l.label"
                :value="l.value"
              />
            </el-select>
          </div>
        </template>
        <div class="bar-list" role="img" aria-label="各知识点掌握度条形图，最薄弱在前">
          <div
            v-for="m in filteredMastery"
            :key="m.language + ':' + m.concept_name"
            class="bar-row"
            :title="'掌握度 ' + m.mastery.toFixed(2) + ' · 练习 ' + m.attempts + ' 次 · 薄弱 ' + m.weakness_count + ' 次'"
          >
            <span class="bar-name">{{ m.concept_name }}</span>
            <div class="bar-track">
              <div class="bar-fill mastery" :style="{ width: Math.max(2, m.mastery * 100) + '%' }"></div>
            </div>
            <span class="bar-num">{{ m.mastery.toFixed(2) }}</span>
            <el-tag
              v-if="masteryLanguage === 'all'"
              size="small"
              effect="plain"
              class="weak-spacer"
            >
              {{ LANGUAGE_LABELS[m.language] || m.language }}
            </el-tag>
            <el-tag v-if="m.mastery < 0.4" type="danger" size="small" class="weak-tag">薄弱</el-tag>
            <span v-else class="weak-spacer"></span>
          </div>
        </div>
      </el-card>

      <!-- 延迟对比：分组条形图（按 Agent 角色 × 模型层） -->
      <el-card v-if="latencyGroups.length" class="panel" shadow="never">
        <template #header>
          <div class="panel-title">
            各 Agent 平均响应延迟：端侧 vs 云端
            <span class="legend">
              <span class="swatch" :style="{ background: EDGE_COLOR }"></span>端侧 qwen2.5:7b
              <span class="swatch" :style="{ background: CLOUD_COLOR }"></span>云端 glm-4.7-flash
            </span>
          </div>
        </template>
        <div class="latency-list" role="img" aria-label="按 Agent 角色分组的端侧与云端平均延迟条形图">
          <div v-for="g in latencyGroups" :key="g.role" class="latency-group">
            <div class="group-label">{{ g.label }}</div>
            <div class="group-bars">
              <div
                v-if="g.edge"
                class="lat-row"
                :title="'端侧平均延迟 ' + fmtLatency(g.edge) + '（' + g.label + '）'"
              >
                <div class="bar-track">
                  <div
                    class="bar-fill"
                    :style="{ width: Math.max(2, (g.edge / latencyMax) * 100) + '%', background: EDGE_COLOR }"
                  ></div>
                </div>
                <span class="bar-num">{{ fmtLatency(g.edge) }}</span>
              </div>
              <div
                v-if="g.cloud"
                class="lat-row"
                :title="'云端平均延迟 ' + fmtLatency(g.cloud) + '（' + g.label + '）'"
              >
                <div class="bar-track">
                  <div
                    class="bar-fill"
                    :style="{ width: Math.max(2, (g.cloud / latencyMax) * 100) + '%', background: CLOUD_COLOR }"
                  ></div>
                </div>
                <span class="bar-num">{{ fmtLatency(g.cloud) }}</span>
              </div>
            </div>
          </div>
        </div>
        <p class="footnote">端侧模型（本地 Ollama qwen2.5:7b）无 API 成本；云端为智谱 glm-4.7-flash（当前免费）。</p>
      </el-card>

      <!-- 明细表（表格视图） -->
      <el-card v-if="stats.length" class="panel" shadow="never">
        <template #header>调用明细（数据来源：llm_call_log）</template>
        <el-table :data="stats" size="small">
          <el-table-column label="Agent" width="90">
            <template #default="{ row }">{{ ROLE_LABELS[row.agent_role] || row.agent_role }}</template>
          </el-table-column>
          <el-table-column label="模型层" width="90">
            <template #default="{ row }">
              <el-tag :type="row.model_tier === 'edge' ? 'primary' : 'warning'" size="small" effect="plain">
                {{ row.model_tier === 'edge' ? '端侧' : '云端' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="calls" label="次数" width="80" />
          <el-table-column label="平均延迟" width="110">
            <template #default="{ row }">{{ fmtLatency(row.avg_latency_ms) }}</template>
          </el-table-column>
          <el-table-column label="平均输入 Tokens" width="140">
            <template #default="{ row }">{{ fmtTokens(row.avg_prompt_tokens) }}</template>
          </el-table-column>
          <el-table-column label="平均输出 Tokens" width="140">
            <template #default="{ row }">{{ fmtTokens(row.avg_completion_tokens) }}</template>
          </el-table-column>
          <el-table-column label="累计成本">
            <template #default="{ row }">¥{{ Number(row.total_cost_yuan).toFixed(4) }}</template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>
    </div>
  </div>
</template>

<style scoped>
.dashboard-layout-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.dashboard {
  /* 数据可视化色板（dataviz 校验通过） */
  --edge: #2a78d6;
  --cloud: #eb6834;
  --ink-1: #0b0b0b;
  --ink-2: #52514e;
  --ink-3: #898781;
  --track: #eceae4;

  max-width: 1000px;
  margin: 0 auto;
  padding: 40px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.loading {
  color: var(--ink-2);
}

/* ---- KPI 行 ---- */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-tile {
  background: #fcfcfb;
  border: 1px solid rgba(11, 11, 11, 0.1);
  border-radius: 8px;
  padding: 16px 20px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--ink-1);
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-unit {
  font-size: 16px;
  font-weight: 400;
  color: var(--ink-2);
}

.stat-label {
  margin-top: 4px;
  font-size: 13px;
  color: var(--ink-2);
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}

/* ---- 卡片 ---- */
.panel {
  margin-bottom: 24px;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.muted {
  font-weight: 400;
  font-size: 13px;
  color: var(--ink-3);
}

.footnote {
  margin: 12px 0 0;
  font-size: 12px;
  color: var(--ink-3);
}

/* ---- 条形图（细 mark、4px 圆角数据端、文本用文本色而非系列色） ---- */
.bar-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.bar-name {
  width: 120px;
  flex-shrink: 0;
  font-size: 13px;
  color: var(--ink-1);
  text-align: right;
}

.bar-track {
  flex: 1;
  height: 12px;
  background: var(--track);
  border-radius: 4px 0 0 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: var(--edge);
  border-radius: 0 4px 4px 0;
}

.bar-num {
  width: 52px;
  flex-shrink: 0;
  font-size: 12px;
  color: var(--ink-2);
  font-variant-numeric: tabular-nums;
}

.weak-tag {
  flex-shrink: 0;
}

.weak-spacer {
  width: 44px;
}

/* ---- 延迟分组条形图 ---- */
.latency-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.latency-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.group-label {
  width: 120px;
  flex-shrink: 0;
  font-size: 13px;
  color: var(--ink-2);
  text-align: right;
}

.group-bars {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.lat-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.legend {
  margin-left: auto;
  font-size: 12px;
  font-weight: 400;
  color: var(--ink-2);
  display: flex;
  align-items: center;
  gap: 6px;
}

.swatch {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  display: inline-block;
  margin-left: 8px;
}

@media (max-width: 768px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .bar-name,
  .group-label {
    width: 90px;
  }
}
</style>
