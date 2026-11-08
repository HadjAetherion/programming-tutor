<script setup lang="ts">
import { ref } from 'vue'

import type { Diagnosis } from '../api/diagnosis'

defineProps<{
  diagnosis: Diagnosis | null
  loading: boolean
}>()

const diagnosisTab = ref('diagnosis')

function styleText(style: string): string {
  switch (style) {
    case 'direct_hint':
      return '直接提示'
    case 'socratic':
      return '苏格拉底式提问'
    case 'scaffold':
      return '分步引导'
    default:
      return style || '自适应辅导'
  }
}

function styleTagType(style: string): string {
  switch (style) {
    case 'direct_hint':
      return 'info'
    case 'socratic':
      return 'success'
    case 'scaffold':
      return 'warning'
    default:
      return 'info'
  }
}

function severityTagType(severity: string): string {
  switch (severity) {
    case 'high':
      return 'danger'
    case 'medium':
      return 'warning'
    case 'low':
      return 'info'
    default:
      return 'info'
  }
}
</script>

<template>
  <div class="diagnosis-panel">
    <div class="diagnosis-header">
      <span class="result-title">AI 诊断辅导</span>
      <el-tag v-if="diagnosis" size="small" type="success">
        {{ diagnosis.model_name }} · 全流程 {{ diagnosis.latency_ms }}ms
      </el-tag>
    </div>

    <div v-if="loading" class="diagnosis-empty">
      智能体协同中：诊断 ∥ 审查 → 反馈 → 规划
      <br />
      免费模型限流下约需 1-3 分钟，请耐心等待...
    </div>

    <el-tabs v-else-if="diagnosis" v-model="diagnosisTab">
      <el-tab-pane label="诊断分析" name="diagnosis">
        <div class="diagnosis-row">
          <span class="diagnosis-label">错误类型：</span>
          <el-tag size="small" type="warning">
            {{ diagnosis.error_type }}
          </el-tag>
        </div>

        <div v-if="diagnosis.root_cause" class="diagnosis-row">
          <span class="diagnosis-label">根因：</span>
          <span>{{ diagnosis.root_cause }}</span>
        </div>

        <div v-if="diagnosis.concepts.length" class="diagnosis-row">
          <span class="diagnosis-label">涉及知识点：</span>
          <el-tag
            v-for="c in diagnosis.concepts"
            :key="c"
            size="small"
            class="concept-tag"
          >
            {{ c }}
          </el-tag>
        </div>

        <div v-if="diagnosis.explanation" class="diagnosis-section">
          <div class="diagnosis-title">讲解</div>
          <p class="diagnosis-text">{{ diagnosis.explanation }}</p>
        </div>

        <div v-if="diagnosis.hint" class="diagnosis-section">
          <div class="diagnosis-title">下一步提示</div>
          <p class="diagnosis-text">{{ diagnosis.hint }}</p>
        </div>
      </el-tab-pane>
      <el-tab-pane label="辅导反馈" name="feedback">
        <div class="diagnosis-row">
          <span class="diagnosis-label">干预策略：</span>
          <el-tag
            size="small"
            :type="styleTagType(diagnosis.feedback.tutoring_style)"
          >
            {{ styleText(diagnosis.feedback.tutoring_style) }}
          </el-tag>
        </div>

        <p class="diagnosis-text">{{ diagnosis.feedback.content }}</p>

        <div
          v-if="diagnosis.feedback.guiding_questions.length"
          class="diagnosis-section"
        >
          <div class="diagnosis-title">引导思考</div>
          <ul class="question-list">
            <li
              v-for="(q, i) in diagnosis.feedback.guiding_questions"
              :key="i"
            >
              {{ q }}
            </li>
          </ul>
        </div>

        <div v-if="diagnosis.feedback.code_example" class="diagnosis-section">
          <div class="diagnosis-title">示例片段</div>
          <pre class="example-code">{{ diagnosis.feedback.code_example }}</pre>
        </div>
      </el-tab-pane>

      <el-tab-pane label="代码审查" name="review">
        <div class="review-score-row">
          <span class="diagnosis-label">代码质量评分：</span>
          <el-progress
            type="dashboard"
            :percentage="diagnosis.review.overall_score"
            :width="72"
          />
        </div>

        <div v-if="diagnosis.review.summary" class="diagnosis-section">
          <div class="diagnosis-title">总体评价</div>
          <p class="diagnosis-text">{{ diagnosis.review.summary }}</p>
        </div>

        <div v-if="diagnosis.review.strengths.length" class="diagnosis-section">
          <div class="diagnosis-title">亮点</div>
          <ul class="question-list">
            <li v-for="(s, i) in diagnosis.review.strengths" :key="i">
              {{ s }}
            </li>
          </ul>
        </div>

        <div v-if="diagnosis.review.issues.length" class="diagnosis-section">
          <div class="diagnosis-title">改进建议</div>
          <div
            v-for="(issue, i) in diagnosis.review.issues"
            :key="i"
            class="review-issue"
          >
            <el-tag size="small" :type="severityTagType(issue.severity)">
              {{ issue.severity }}
            </el-tag>
            <span class="issue-category">{{ issue.category }}</span>
            <span class="issue-message">{{ issue.message }}</span>
            <div v-if="issue.suggestion" class="issue-suggestion">
              建议：{{ issue.suggestion }}
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="学习规划" name="planning">
        <p class="diagnosis-text">{{ diagnosis.planning.summary }}</p>

        <div v-if="diagnosis.planning.steps.length" class="diagnosis-section">
          <div class="diagnosis-title">行动步骤</div>
          <div
            v-for="(step, i) in diagnosis.planning.steps"
            :key="i"
            class="plan-step"
          >
            <el-tag size="small" type="info">
              {{ i + 1 }}. {{ step.action }}
            </el-tag>
            <span class="step-detail">{{ step.detail }}</span>
          </div>
        </div>

        <div
          v-if="diagnosis.planning.next_problem_hint"
          class="diagnosis-section"
        >
          <div class="diagnosis-title">下一步练习建议</div>
          <p class="diagnosis-text">
            {{ diagnosis.planning.next_problem_hint }}
          </p>
        </div>
      </el-tab-pane>
    </el-tabs>

    <div v-else class="diagnosis-empty">
      提交错误代码后将自动给出多智能体协同辅导
    </div>
  </div>
</template>

<style scoped>
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

.result-title {
  font-size: 16px;
  font-weight: 600;
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
  line-height: 1.8;
}

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
