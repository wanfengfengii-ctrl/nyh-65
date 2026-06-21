import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/pages/HomePage.vue'
import ComparePage from '@/pages/ComparePage.vue'
import DrainagePage from '@/pages/DrainagePage.vue'
import RestorationPage from '@/pages/RestorationPage.vue'

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
  {
    path: '/drainage',
    name: 'drainage',
    component: DrainagePage,
  },
  {
    path: '/restoration',
    name: 'restoration',
    component: RestorationPage,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
