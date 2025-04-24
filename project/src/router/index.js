import Vue from 'vue'
import VueRouter from 'vue-router'
import GraphPage from '../pages/GraphPage.vue'
import UploadPage from '../pages/UploadPage.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Graph',
    component: GraphPage
  },
  {
    path: '/upload',
    name: 'Upload',
    component: UploadPage
  },
  {
    path: '/forecast-history',
    name: 'ForecastHistory',
    component: () => import('../pages/ForecastHistoryPage.vue')
  },
  {
    path: '/forecast',
    name: 'Forecast',
    component: () => import('../pages/ForecastPage.vue')
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router 