import http from './http'

export interface RunCodeRequest {
    code: string
    language: string
}

export interface RunCodeResult {
    status: string
    stdout: string
    stderr: string
    exit_code: number
}

export async function runCode(
    data: RunCodeRequest,
): Promise<RunCodeResult> {
    const response = await http.post<RunCodeResult>(
        '/submissions/run',
        data,
    )

    return response.data
}

export interface SubmitCodeRequest {
    problem_id: number
    code: string
    language: string
}

export interface SubmitCodeResult {
    id: number
    status: string
    passed_tests: number
    total_tests: number
    stdout: string
    stderr: string
    exit_code: number
    execution_time_ms: number
}

export async function submitCode(
    data: SubmitCodeRequest,
): Promise<SubmitCodeResult> {
    const response = await http.post<SubmitCodeResult>(
        '/submissions/submit',
        data,
    )

    return response.data
}

export interface SubmissionSummary {
    id: number
    problem_id: number
    language: string
    status: string
    exit_code: number
    execution_time_ms: number
    has_diagnosis: boolean
    created_at: string
}

export interface Submission {
    id: number
    user_id: number
    problem_id: number
    language: string
    code: string
    status: string
    stdout: string
    stderr: string
    exit_code: number
    execution_time_ms: number
    created_at: string
}

export interface SubmissionListResponse {
    submissions: SubmissionSummary[]
}

export async function getSubmissions(): Promise<SubmissionListResponse> {
    const response = await http.get<SubmissionListResponse>(
        '/submissions',
    )

    return response.data
}

export async function getSubmission(
    id: number,
): Promise<Submission> {
    const response = await http.get<Submission>(
        `/submissions/${id}`,
    )

    return response.data
}