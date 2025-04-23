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
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router 