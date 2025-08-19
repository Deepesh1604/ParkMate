<script setup>
import { RouterLink, RouterView } from 'vue-router'
import { ref, onMounted, onUnmounted } from 'vue'

// Mobile menu state
const isMenuOpen = ref(false)

// Toggle mobile menu
const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value
}

// Close mobile menu
const closeMenu = () => {
  isMenuOpen.value = false
}

// Close menu when clicking outside
const handleClickOutside = (event) => {
  if (!event.target.closest('.navbar') && isMenuOpen.value) {
    closeMenu()
  }
}

// Add scroll effect to navbar
const handleScroll = () => {
  const navbar = document.querySelector('.navbar')
  if (navbar) {
    if (window.scrollY > 50) {
      navbar.classList.add('scrolled')
    } else {
      navbar.classList.remove('scrolled')
    }
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <div id="app">
    <!-- Glass Morphism Navbar -->
    

    <!-- Main Content -->
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
/* CSS Variables */
:root {
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --accent-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  --glass-bg: rgba(255, 255, 255, 0.1);
  --glass-bg-dark: rgba(255, 255, 255, 0.15);
  --glass-border: rgba(255, 255, 255, 0.2);
  --shadow-soft: 0 8px 32px rgba(31, 38, 135, 0.15);
  --navbar-height: 80px;
  --transition-smooth: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Global App Styles */
#app {
  min-height: 100vh;
  position: relative;
}

/* Navbar Header */
.navbar-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: transparent;
  transition: var(--transition-smooth);
}

/* Glass Morphism Navbar */
.navbar {
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--glass-border);
  transition: var(--transition-smooth);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.navbar.scrolled {
  background: var(--glass-bg-dark);
  backdrop-filter: blur(25px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.navbar-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  height: var(--navbar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* Brand Logo */
.navbar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
  text-decoration: none;
  transition: var(--transition-smooth);
}

.navbar-brand:hover {
  transform: translateY(-1px);
  filter: drop-shadow(0 4px 8px rgba(255, 255, 255, 0.2));
}

.logo-icon {
  font-size: 2rem;
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.brand-text {
  background: linear-gradient(135deg, #fff 0%, #e0e0e0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

/* Navigation Menu */
.navbar-menu {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-link {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.5rem;
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.95rem;
  border-radius: 12px;
  transition: var(--transition-smooth);
  overflow: hidden;
  border: 1px solid transparent;
  backdrop-filter: blur(10px);
}

.nav-text {
  position: relative;
  z-index: 2;
}

.nav-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), transparent);
  transition: var(--transition-smooth);
  opacity: 0;
  z-index: 1;
}

.nav-link:hover {
  color: white;
  transform: translateY(-1px);
  border-color: var(--glass-border);
  box-shadow: 0 4px 15px rgba(255, 255, 255, 0.1);
}

.nav-link:hover .nav-glow {
  opacity: 1;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
}

/* Primary CTA Button */
.nav-link-primary {
  background: var(--accent-gradient);
  color: white !important;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 15px rgba(79, 172, 254, 0.2);
}

.nav-link-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(79, 172, 254, 0.3);
  border-color: rgba(255, 255, 255, 0.3);
}

.nav-link-primary .nav-glow {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent);
}

.nav-link-primary:hover .nav-glow {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
}

/* Active Link Styles */
.nav-link.router-link-exact-active:not(.nav-link-primary) {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border-color: var(--glass-border);
}

.nav-link.router-link-exact-active:not(.nav-link-primary) .nav-glow {
  opacity: 1;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.05));
}

/* User Section */
.user-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-left: 1rem;
  padding-left: 1rem;
  border-left: 1px solid rgba(255, 255, 255, 0.2);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #64b5f6 0%, #1976d2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 1rem;
  border: 2px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 15px rgba(100, 181, 246, 0.3);
}

.user-details {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.username {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  font-size: 0.9rem;
  line-height: 1.2;
}

.user-role {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Mobile Menu Toggle */
.mobile-toggle {
  display: none;
  flex-direction: column;
  gap: 4px;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: var(--transition-smooth);
}

.mobile-toggle:hover {
  background: rgba(255, 255, 255, 0.1);
}

.hamburger-line {
  width: 24px;
  height: 2px;
  background: white;
  border-radius: 1px;
  transition: var(--transition-smooth);
}

.mobile-toggle.active .hamburger-line:nth-child(1) {
  transform: rotate(45deg) translate(6px, 6px);
}

.mobile-toggle.active .hamburger-line:nth-child(2) {
  opacity: 0;
}

.mobile-toggle.active .hamburger-line:nth-child(3) {
  transform: rotate(-45deg) translate(6px, -6px);
}

/* Main Content */
.main-content {
  margin-top: var(--navbar-height);
  min-height: calc(100vh - var(--navbar-height));
  width: 100%;
}

/* Responsive Design */
@media (max-width: 768px) {
  .navbar-container {
    padding: 0 1rem;
  }

  .mobile-toggle {
    display: flex;
  }

  .navbar-menu {
    position: fixed;
    top: var(--navbar-height);
    left: 0;
    right: 0;
    background: var(--glass-bg-dark);
    backdrop-filter: blur(25px);
    border-bottom: 1px solid var(--glass-border);
    flex-direction: column;
    gap: 0;
    padding: 1rem;
    transform: translateY(-100%);
    opacity: 0;
    visibility: hidden;
    transition: var(--transition-smooth);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  }

  .navbar-menu.active {
    transform: translateY(0);
    opacity: 1;
    visibility: visible;
  }

  .nav-link {
    width: 100%;
    padding: 1rem;
    text-align: center;
    border-radius: 8px;
    margin-bottom: 0.5rem;
  }

  .nav-link:last-child {
    margin-bottom: 0;
  }

  .user-section {
    flex-direction: column;
    width: 100%;
    margin-left: 0;
    padding-left: 0;
    border-left: none;
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    padding-top: 1rem;
    margin-top: 1rem;
    gap: 1rem;
  }

  .user-info {
    justify-content: center;
  }

  .user-details {
    align-items: center;
    text-align: center;
  }

  .brand-text {
    font-size: 1.2rem;
  }

  .logo-icon {
    font-size: 1.5rem;
  }
}

@media (max-width: 480px) {
  .navbar-container {
    padding: 0 1rem;
    height: 70px;
  }

  .main-content {
    margin-top: 70px;
    min-height: calc(100vh - 70px);
  }

  .navbar-menu {
    top: 70px;
  }

  .brand-text {
    font-size: 1.1rem;
  }

  .logo-icon {
    font-size: 1.3rem;
  }
}

/* Smooth scroll behavior */
html {
  scroll-behavior: smooth;
}

/* Body background for consistency */
body {
  margin: 0;
  padding: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  min-height: 100vh;
}
</style>
