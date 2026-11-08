import http from './http'

export interface Problem {
    id: number
    title: string
    description: string
    difficulty: 'easy' | 'medium' | 'hard'
    input_description: string
    output_description: string
    constraints: string
    sample_input: string
    sample_output: string
    time_limit_ms: number
    memory_limit_mb: number
    created_at: string
    updated_at: string
}

export async function getProblems() {
    const response = await http.get('/problems')

    return response.data.problems as Problem[]
}

export async function getProblem(id: number) {
    const response = await http.get(`/problems/${id}`)

    return response.data.problem as Problem
}