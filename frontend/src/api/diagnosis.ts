import http from './http'

export interface Diagnosis {
    id: number
    submission_id: number
    user_id: number
    error_type: string
    root_cause: string
    concepts: string[]
    explanation: string
    hint: string
    feedback: FeedbackOut
    review: ReviewOut
    planning: PlanOut
    model_name: string
    model_tier: string
    latency_ms: number
    prompt_tokens: number
    completion_tokens: number
    cost_yuan: number
    created_at: string
}

export interface FeedbackOut {
    tutoring_style: string
    content: string
    guiding_questions: string[]
    code_example: string
}

export interface ReviewIssueOut {
    severity: string
    category: string
    message: string
    suggestion: string
}

export interface ReviewOut {
    overall_score: number
    strengths: string[]
    issues: ReviewIssueOut[]
    summary: string
}

export interface PlanStepOut {
    action: string
    detail: string
}

export interface PlanOut {
    summary: string
    steps: PlanStepOut[]
    next_problem_hint: string
}

// 兜底归一化：老数据（阶段1只存了诊断）或缺字段时保证前端可安全渲染
export function normalizeDiagnosis(d: Diagnosis): Diagnosis {
    return {
        ...d,
        concepts: d.concepts ?? [],
        feedback: d.feedback ?? {
            tutoring_style: '',
            content: '',
            guiding_questions: [],
            code_example: '',
        },
        review: d.review ?? {
            overall_score: 0,
            strengths: [],
            issues: [],
            summary: '',
        },
        planning: d.planning ?? {
            summary: '',
            steps: [],
            next_problem_hint: '',
        },
    }
}

// 诊断是 4 次 LLM 调用（诊断∥审查 → 反馈 → 规划），免费模型限流下全流程约 1-3 分钟
export async function diagnoseSubmission(
    submissionId: number,
): Promise<Diagnosis> {
    const response = await http.post<DiagnoseResponse>(
        `/submissions/${submissionId}/diagnose`,
        null,
        { timeout: 300000 },
    )
    return normalizeDiagnosis(response.data.diagnosis)
}

// 读取已保存的诊断结果（不触发 LLM 调用），无记录时返回 null
export async function getDiagnosis(
    submissionId: number,
): Promise<Diagnosis | null> {
    const response = await http.get<{ diagnosis: Diagnosis | null }>(
        `/submissions/${submissionId}/diagnosis`,
    )
    const d = response.data.diagnosis
    return d ? normalizeDiagnosis(d) : null
}

interface DiagnoseResponse {
    diagnosis: Diagnosis
}
