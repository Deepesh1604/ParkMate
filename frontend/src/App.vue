<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header>
    <div class="navbar">
      <div class="logo">
        <h1>🅿️ ParkMate</h1>
      </div>
      <nav>
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/login">Login</RouterLink>
        <RouterLink to="/register">Register</RouterLink>
      </nav>
    </div>
  </header>

  <main>
    <RouterView />
  </main>
</template>

<style scoped>
header {
  background-color: #2c3e50;
  color: white;
  padding: 1rem 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 100vw;
  margin: 0 auto;
  padding: 0 2rem;
}

.logo h1 {
  margin: 0;
  font-size: 1.8rem;
  color: #42b883;
}

nav {
  display: flex;
  gap: 2rem;
}

nav a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.3s;
}

nav a:hover {
  background-color: #34495e;
}

nav a.router-link-exact-active {
  background-color: #42b883;
  color: white;
}

main {
  min-height: calc(100vh - 80px);
  width: 100%;
  margin: 0;
  padding: 0;
}

@media (max-width: 768px) {
  .navbar {
    flex-direction: column;
    gap: 1rem;
  }
  
  nav {
    gap: 1rem;
  }
}
</style>
