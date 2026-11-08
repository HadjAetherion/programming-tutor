import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import http from '../api/http'

export interface User {
    id: number
    username: string
    email: string
    created_at: string
    updated_at: string
}

interface LoginResponse {
    token: string
    user: User
}

export const useAuthStore = defineStore('auth', () => {
    const token = ref<string | null>(
        localStorage.getItem('token'),
    )

    const user = ref<User | null>(
        JSON.parse(localStorage.getItem('user') || 'null'),
    )

    const isLoggedIn = computed(() => {
        return !!token.value
    })

    async function login(
        email: string,
        password: string,
    ) {
        const response = await http.post<LoginResponse>(
            '/auth/login',
            {
                email,
                password,
            },
        )

        token.value = response.data.token
        user.value = response.data.user

        localStorage.setItem(
            'token',
            response.data.token,
        )

        localStorage.setItem(
            'user',
            JSON.stringify(response.data.user),
        )
    }

    function logout() {
        token.value = null
        user.value = null

        localStorage.removeItem('token')
        localStorage.removeItem('user')
    }

    async function register(
        username: string,
        email: string,
        password: string,
    ) {
        await http.post('/auth/register', {
            username,
            email,
            password,
        })

        // 注册成功后直接登录，省掉一次手动输入
        await login(email, password)
    }

    async function fetchCurrentUser() {
        if (!token.value) {
            return
        }

        try {
            const response = await http.get('/me')

            user.value = response.data.user

            localStorage.setItem(
                'user',
                JSON.stringify(response.data.user),
            )
        } catch {
            logout()
        }
    }

    return {
        token,
        user,
        isLoggedIn,
        login,
        register,
        logout,
        fetchCurrentUser,
    }
})