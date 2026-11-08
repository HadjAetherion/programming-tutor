import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
    history: createWebHistory(),

    routes: [
        {
            path: '/',
            redirect: '/problems',
        },

        {
            path: '/login',
            component: () => import('../views/LoginView.vue'),
            meta: {
                requiresGuest: true,
            },
        },

        {
            path: '/register',
            component: () => import('../views/RegisterView.vue'),
            // 不加 requiresGuest：已登录用户也能打开（用于切换/新建账号），
            // 否则访问 /register 会被弹回 /problems，看起来像"页面不存在"。
        },

        {
            path: '/problems',
            component: () => import('../views/ProblemListView.vue'),
            meta: {
                requiresAuth: true,
            },
        },

        {
            path: '/problems/:id',
            component: () => import('../views/ProblemView.vue'),
            meta: {
                requiresAuth: true,
            },
        },

        {
            path: '/submissions/:id',
            component: () => import('../views/SubmissionView.vue'),
            meta: {
                requiresAuth: true,
            },
        },

        {
            path: '/dashboard',
            component: () => import('../views/DashboardView.vue'),
            meta: {
                requiresAuth: true,
            },
        },
    ],
})

router.beforeEach((to) => {
    const authStore = useAuthStore()

    if (to.meta.requiresAuth && !authStore.isLoggedIn) {
        return '/login'
    }

    if (to.meta.requiresGuest && authStore.isLoggedIn) {
        return '/problems'
    }

    return true
})

export default router