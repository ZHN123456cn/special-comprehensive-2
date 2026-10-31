import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/RegisterView.vue'),
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/workspace/:id',
    name: 'Workspace',
    component: () => import('../views/GameWorkspaceView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局前置守卫：未登录只能访问登录/注册页
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!token && to.name !== 'Login' && to.name !== 'Register') {
    return { name: 'Login' }
  }
})

export default router
