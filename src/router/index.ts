import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/pages/HomePage.vue'
import ComparePage from '@/pages/ComparePage.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomePage,
  },
  {
    path: '/compare',
    name: 'compare',
    component: ComparePage,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
