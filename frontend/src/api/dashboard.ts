import http from './http'

export interface MasteryItem {
    language: string
    concept_name: string
    mastery: number
    attempts: number
    weakness_count: number
    updated_at: string
}

export interface LLMStat {
    agent_role: string
    model_tier: string
    calls: number
    avg_latency_ms: number
    avg_prompt_tokens: number
    avg_completion_tokens: number
    total_cost_yuan: number
}

export async function getMyMastery(): Promise<MasteryItem[]> {
    const res = await http.get('/me/mastery')
    return res.data?.mastery ?? []
}

export async function getMyLLMStats(): Promise<LLMStat[]> {
    const res = await http.get('/me/llm-stats')
    return res.data?.stats ?? []
}
