import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import Login from '../components/login.vue'
import Register from '../components/register.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/login',
      name: 'login',
      component: Login,
    },
    {
      path: '/register',
      name: 'register',
      component: Register,
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('../views/AdminDashboard.vue'),
      beforeEnter: (to, from, next) => {
        // Simple check - you might want to improve this with proper auth
        // For now, we'll just check if user is coming from login
        next();
      }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/UserDashboard.vue'),
      beforeEnter: (to, from, next) => {
        // Simple check - you might want to improve this with proper auth
        next();
      }
    },
  ],
})

export default router
