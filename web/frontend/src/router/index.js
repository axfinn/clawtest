import { createRouter, createWebHistory } from 'vue-router'
import AutoDevTool from '../views/AutoDevTool.vue'

const routes = [
  {
    path: '/',
    redirect: '/autodev'
  },
  {
    path: '/autodev',
    name: 'AutoDev',
    component: AutoDevTool,
    meta: {
      title: 'AutoDev AI',
      icon: 'MagicStick'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
