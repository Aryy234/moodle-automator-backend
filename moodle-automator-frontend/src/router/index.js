import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: () => import('../views/Dashboard.vue'),
  },
  {
    path: '/customizer/:id',
    name: 'customizer',
    component: () => import('../views/Customizer.vue'),
    props: true,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
