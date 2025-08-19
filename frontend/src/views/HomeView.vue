<template>
  <div class="home">
    <!-- Header -->
    <header class="header">
      <nav class="nav">
        <div class="logo">
          🚗 ParkMate
        </div>
        <div class="nav-links">
          <a href="#hero" class="nav-link" @click="scrollToSection">About</a>
          <a href="#features" class="nav-link" @click="scrollToSection">Features</a>
          <a href="#contact" class="nav-link" @click="scrollToSection">Contact</a>
          <router-link to="/login" class="sign-in-btn">Sign In</router-link>
        </div>
      </nav>
    </header>

    <!-- Hero Section -->
    <section class="hero" id="hero">
      <div class="hero-container">
        <div class="hero-content">
          <h1>Smart Parking Solution</h1>
          <p class="subtitle">Find, reserve, and pay for parking spots instantly. Transform your parking experience with our intelligent platform.</p>
          <div class="hero-buttons">
            <router-link to="/register" class="btn-primary">Get Started</router-link>
            <a href="#" class="btn-secondary" @click="watchDemo">Watch Demo</a>
          </div>
        </div>
        <div class="hero-visual">
          <div class="parking-3d" ref="parking3d">
            <div class="parking-status">● Available: {{ availableSpots }}</div>
            <div class="parking-garage">
              <div class="parking-level" v-for="level in 4" :key="level">
                <div 
                  v-for="spot in 5" 
                  :key="`${level}-${spot}`"
                  class="car"
                  :class="getSpotStatus(level, spot)"
                ></div>
              </div>
            </div>
            <div class="occupied-status">● Occupied: {{ occupiedSpots }}</div>
            <div class="real-time-indicator">🕒 Real-time</div>
          </div>
        </div>
      </div>

      <!-- Stats -->
      <div class="stats">
        <div class="stats-container">
          <div class="stat-item" v-for="stat in stats" :key="stat.label">
            <div class="stat-number">{{ stat.number }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features" id="features">
      <div class="features-container">
        <h2>Why Choose ParkMate?</h2>
        <p>Experience the future of parking with our comprehensive suite of smart features designed to make your life easier.</p>
        
        <div class="features-grid">
          <div 
            v-for="(feature, index) in features" 
            :key="index"
            class="feature-card"
            ref="featureCards"
          >
            <div class="feature-icon">{{ feature.icon }}</div>
            <h3>{{ feature.title }}</h3>
            <p>{{ feature.description }}</p>
          </div>
        </div>

        <div class="features-grid-2">
          <div 
            v-for="(feature, index) in additionalFeatures" 
            :key="index"
            class="feature-card"
            ref="additionalFeatureCards"
          >
            <div class="feature-icon">{{ feature.icon }}</div>
            <h3>{{ feature.title }}</h3>
            <p>{{ feature.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- How It Works Section -->
    <section class="how-it-works">
      <div class="how-it-works-container">
        <h2>How It Works</h2>
        <p class="subtitle">Get started in three simple steps</p>
        
        <div class="steps">
          <div 
            v-for="(step, index) in steps" 
            :key="index"
            class="step"
            ref="stepCards"
          >
            <div class="step-number">{{ index + 1 }}</div>
            <h3>{{ step.title }}</h3>
            <p>{{ step.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Contact Section -->
    <section class="contact" id="contact">
      <div class="contact-container">
        <div class="contact-content">
          <div class="contact-info">
            <h2>Get in Touch</h2>
            <p class="contact-subtitle">Have questions? We'd love to hear from you. Send us a message and we'll respond as soon as possible.</p>
            
            <div class="contact-details">
              <div class="contact-item">
                <div class="contact-icon">📧</div>
                <div class="contact-text">
                  <h4>Email</h4>
                  <p>support@parkmate.com</p>
                </div>
              </div>
              
              <div class="contact-item">
                <div class="contact-icon">📞</div>
                <div class="contact-text">
                  <h4>Phone</h4>
                  <p>+1 (555) 123-4567</p>
                </div>
              </div>
              
              <div class="contact-item">
                <div class="contact-icon">📍</div>
                <div class="contact-text">
                  <h4>Address</h4>
                  <p>123 Smart Parking Ave<br>Tech City, TC 12345</p>
                </div>
              </div>
              
              <div class="contact-item">
                <div class="contact-icon">🕒</div>
                <div class="contact-text">
                  <h4>Business Hours</h4>
                  <p>Mon - Fri: 9:00 AM - 6:00 PM<br>Sat - Sun: 10:00 AM - 4:00 PM</p>
                </div>
              </div>
            </div>
          </div>
          
          <div class="contact-form-wrapper">
            <form @submit.prevent="handleContactSubmit" class="contact-form">
              <h3>Send us a Message</h3>
              
              <div class="form-row">
                <div class="form-group">
                  <label for="firstName">First Name</label>
                  <input 
                    type="text" 
                    id="firstName" 
                    v-model="contactForm.firstName" 
                    required 
                    class="form-input"
                    placeholder="Your first name"
                  />
                </div>
                
                <div class="form-group">
                  <label for="lastName">Last Name</label>
                  <input 
                    type="text" 
                    id="lastName" 
                    v-model="contactForm.lastName" 
                    required 
                    class="form-input"
                    placeholder="Your last name"
                  />
                </div>
              </div>
              
              <div class="form-group">
                <label for="email">Email</label>
                <input 
                  type="email" 
                  id="email" 
                  v-model="contactForm.email" 
                  required 
                  class="form-input"
                  placeholder="your.email@example.com"
                />
              </div>
              
              <div class="form-group">
                <label for="subject">Subject</label>
                <input 
                  type="text" 
                  id="subject" 
                  v-model="contactForm.subject" 
                  required 
                  class="form-input"
                  placeholder="What is this about?"
                />
              </div>
              
              <div class="form-group">
                <label for="message">Message</label>
                <textarea 
                  id="message" 
                  v-model="contactForm.message" 
                  required 
                  class="form-textarea"
                  placeholder="Tell us more about your inquiry..."
                  rows="5"
                ></textarea>
              </div>
              
              <button type="submit" class="contact-btn" :disabled="isSubmitting">
                {{ isSubmitting ? 'Sending...' : 'Send Message' }}
              </button>
              
              <div v-if="contactMessage" class="contact-message" :class="contactMessageType">
                {{ contactMessage }}
              </div>
            </form>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'

// Reactive data
const availableSpots = ref(23)
const occupiedSpots = ref(17)

// Contact form data
const contactForm = reactive({
  firstName: '',
  lastName: '',
  email: '',
  subject: '',
  message: ''
})

const isSubmitting = ref(false)
const contactMessage = ref('')
const contactMessageType = ref('')

const stats = [
  { number: '5000+', label: 'Parking Spots' },
  { number: '50K+', label: 'Happy Users' },
  { number: '100+', label: 'Cities' }
]

const features = [
  {
    icon: '📍',
    title: 'Real-time Availability',
    description: 'See available parking spots in real-time with live updates and accurate information.'
  },
  {
    icon: '⏰',
    title: 'Instant Reservations',
    description: 'Reserve your parking spot instantly and get guaranteed availability when you arrive.'
  },
  {
    icon: '💳',
    title: 'Seamless Payments',
    description: 'Pay securely through the app with multiple payment options and automatic billing.'
  },
  {
    icon: '🛡️',
    title: 'Secure Parking',
    description: 'All parking locations are verified and monitored for your safety and security.'
  }
]

const additionalFeatures = [
  {
    icon: '📱',
    title: 'Mobile First',
    description: 'Designed for mobile with an intuitive interface that makes parking effortless.'
  },
  {
    icon: '🗺️',
    title: 'Smart Navigation',
    description: 'Get turn-by-turn directions to your reserved parking spot with optimal routing.'
  },
  {
    icon: '🔔',
    title: 'Smart Notifications',
    description: 'Receive timely notifications about your parking session and important updates.'
  },
  {
    icon: '📊',
    title: 'Usage Analytics',
    description: 'Track your parking habits and expenses with detailed analytics and insights.'
  }
]

const steps = [
  {
    title: 'Find Parking',
    description: 'Search for available parking spots near your destination using our interactive map.'
  },
  {
    title: 'Reserve & Pay',
    description: 'Select your preferred spot, choose your duration, and pay securely through the app.'
  },
  {
    title: 'Park with Confidence',
    description: 'Follow GPS navigation to your spot and enjoy stress-free parking with guaranteed availability.'
  }
]

// Parking spot status logic
const parkingSpots = reactive([
  ['available', 'occupied', 'available', 'reserved', 'available'],
  ['occupied', 'available', 'available', 'occupied', 'available'],
  ['available', 'available', 'occupied', 'available', 'reserved'],
  ['reserved', 'available', 'occupied', 'available', 'available']
])

const getSpotStatus = (level, spot) => {
  return parkingSpots[level - 1][spot - 1]
}

// Methods
const watchDemo = () => {
  // Implement demo functionality
  alert('Demo coming soon!')
}

const scrollToSection = (event) => {
  event.preventDefault()
  const targetId = event.target.getAttribute('href').substring(1)
  const targetElement = document.getElementById(targetId)
  
  if (targetElement) {
    const headerHeight = 80 // Account for fixed header
    const targetPosition = targetElement.offsetTop - headerHeight
    
    window.scrollTo({
      top: targetPosition,
      behavior: 'smooth'
    })
  }
}

const handleContactSubmit = async () => {
  isSubmitting.value = true
  contactMessage.value = ''
  
  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // Reset form
    Object.assign(contactForm, {
      firstName: '',
      lastName: '',
      email: '',
      subject: '',
      message: ''
    })
    
    contactMessage.value = 'Thank you for your message! We\'ll get back to you soon.'
    contactMessageType.value = 'success'
    
    // Clear message after 5 seconds
    setTimeout(() => {
      contactMessage.value = ''
    }, 5000)
    
  } catch {
    contactMessage.value = 'Sorry, there was an error sending your message. Please try again.'
    contactMessageType.value = 'error'
  } finally {
    isSubmitting.value = false
  }
}

// Component references
const parking3d = ref(null)
const featureCards = ref([])
const additionalFeatureCards = ref([])
const stepCards = ref([])

onMounted(() => {
  // Add scroll effect to header
  const header = document.querySelector('.header')
  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      header.style.background = 'rgba(139, 43, 218, 0.95)'
    } else {
      header.style.background = 'rgba(138, 43, 226, 0.95)'
    }
  })

  // Animate feature cards on scroll
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1'
        entry.target.style.transform = 'translateY(0)'
      }
    })
  }, observerOptions)

  // Observe all animated elements
  const allCards = [
    ...featureCards.value,
    ...additionalFeatureCards.value,
    ...stepCards.value
  ]

  allCards.forEach((el, index) => {
    if (el) {
      el.style.opacity = '0'
      el.style.transform = 'translateY(30px)'
      el.style.transition = `all 0.6s ease ${index * 0.1}s`
      observer.observe(el)
    }
  })

  // Add random car movements
  setInterval(() => {
    const cars = document.querySelectorAll('.car')
    cars.forEach(car => {
      if (Math.random() > 0.7) {
        car.style.animation = 'none'
        car.offsetHeight // Trigger reflow
        car.style.animation = 'carPulse 2s ease-in-out infinite'
      }
    })
  }, 3000)

  // Update parking stats occasionally
  setInterval(() => {
    if (Math.random() > 0.8) {
      availableSpots.value = Math.max(20, Math.min(30, availableSpots.value + (Math.random() > 0.5 ? 1 : -1)))
      occupiedSpots.value = 40 - availableSpots.value
    }
  }, 5000)
})
</script>

<style scoped>
/* CSS Variables for consistent theming */
:root {
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  --accent-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  --glass-bg: rgba(255, 255, 255, 0.1);
  --glass-border: rgba(255, 255, 255, 0.2);
  --text-primary: #2c3e50;
  --text-secondary: #7f8c8d;
  --shadow-soft: 0 8px 32px rgba(31, 38, 135, 0.15);
  --shadow-hover: 0 15px 35px rgba(31, 38, 135, 0.25);
}

html {
  scroll-behavior: smooth;
}

.home {
  min-height: 100vh;
  overflow-x: hidden;
}

/* Header */
.header {
  position: fixed;
  top: 0;
  width: 100%;
  background: rgba(138, 43, 226, 0.95);
  backdrop-filter: blur(10px);
  z-index: 1000;
  padding: 1rem 2rem;
}

.nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: white;
  font-size: 1.5rem;
  font-weight: bold;
}

.nav-links {
  display: flex;
  gap: 2rem;
  align-items: center;
}

.nav-link {
  color: white;
  text-decoration: none;
  transition: opacity 0.3s ease;
}

.nav-link:hover {
  opacity: 0.8;
}

.sign-in-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 20px;
  text-decoration: none;
  transition: all 0.3s ease;
}

.sign-in-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

/* Hero Section */
.hero {
  background: linear-gradient(135deg, #8B2BDA 0%, #6A1B9A 50%, #4A148C 100%);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 6rem 2rem 4rem;
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 100px;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1440 320'%3E%3Cpath fill='%23ffffff' fill-opacity='1' d='M0,96L48,112C96,128,192,160,288,160C384,160,480,128,576,122.7C672,117,768,139,864,138.7C960,139,1056,117,1152,122.7C1248,128,1344,160,1392,176L1440,192L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z'%3E%3C/path%3E%3C/svg%3E") no-repeat;
  background-size: cover;
}

.hero-container {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
  flex: 1;
}

.hero-content h1 {
  font-size: 4rem;
  font-weight: 700;
  color: white;
  margin-bottom: 1.5rem;
  line-height: 1.1;
}

.hero-content .subtitle {
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 2.5rem;
  line-height: 1.6;
}

.hero-buttons {
  display: flex;
  gap: 1rem;
}

.btn-primary {
  background: white;
  color: #8B2BDA;
  padding: 1rem 2rem;
  border: none;
  border-radius: 25px;
  font-size: 1.1rem;
  font-weight: 600;
  text-decoration: none;
  display: inline-block;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(255, 255, 255, 0.3);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 255, 255, 0.4);
}

.btn-secondary {
  background: transparent;
  color: white;
  border: 2px solid white;
  padding: 1rem 2rem;
  border-radius: 25px;
  font-size: 1.1rem;
  font-weight: 600;
  text-decoration: none;
  display: inline-block;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: white;
  color: #8B2BDA;
  transform: translateY(-2px);
}

/* 3D Parking Visualization */
.hero-visual {
  display: flex;
  justify-content: center;
  align-items: center;
  perspective: 1000px;
}

.parking-3d {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 2rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  transform: rotateX(10deg) rotateY(-10deg);
  transition: all 0.5s ease;
  position: relative;
}

.parking-3d:hover {
  transform: rotateX(0deg) rotateY(0deg);
}

.parking-status {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(0, 255, 136, 0.9);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 15px;
  font-size: 0.9rem;
  font-weight: 600;
}

.parking-garage {
  width: 400px;
  height: 300px;
  background: linear-gradient(135deg, #2C3E50 0%, #34495E 100%);
  border-radius: 10px;
  position: relative;
  overflow: hidden;
  margin: 1rem 0;
}

.parking-level {
  position: absolute;
  width: 100%;
  height: 60px;
  background: rgba(255, 255, 255, 0.1);
  border-bottom: 2px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 0 1rem;
}

.parking-level:nth-child(1) { top: 0; }
.parking-level:nth-child(2) { top: 60px; }
.parking-level:nth-child(3) { top: 120px; }
.parking-level:nth-child(4) { top: 180px; }

.car {
  width: 30px;
  height: 15px;
  border-radius: 5px;
  animation: carPulse 2s ease-in-out infinite;
}

.car.available { background: #00ff88; }
.car.occupied { background: #ff4757; }
.car.reserved { background: #ffa726; }

@keyframes carPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.1); }
}

.occupied-status {
  position: absolute;
  bottom: 1rem;
  right: 1rem;
  background: rgba(255, 71, 87, 0.9);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 15px;
  font-size: 0.9rem;
  font-weight: 600;
}

.real-time-indicator {
  position: absolute;
  top: 50%;
  right: -50px;
  background: rgba(255, 255, 255, 0.9);
  color: #8B2BDA;
  padding: 0.5rem 1rem;
  border-radius: 15px;
  font-size: 0.8rem;
  font-weight: 600;
}

/* Stats Section */
.stats {
  background: #8B2BDA;
  padding: 2rem 0;
  color: white;
  margin-top: auto;
}

.stats-container {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  padding: 0 2rem;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 1rem;
  opacity: 0.9;
}

/* Features Section */
.features {
  background: #f8f9fa;
  padding: 6rem 2rem;
}

.features-container {
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
}

.features h2 {
  font-size: 2.5rem;
  color: #333;
  margin-bottom: 1rem;
}

.features p {
  font-size: 1.2rem;
  color: #666;
  margin-bottom: 4rem;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.features-grid,
.features-grid-2 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2rem;
  margin-bottom: 4rem;
}

.feature-card {
  background: white;
  padding: 2rem;
  border-radius: 15px;
  text-align: center;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
}

.feature-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 15px 40px rgba(139, 43, 218, 0.2);
}

.feature-icon {
  width: 60px;
  height: 60px;
  background: #8B2BDA;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
  color: white;
  font-size: 1.5rem;
}

.feature-card h3 {
  font-size: 1.2rem;
  color: #333;
  margin-bottom: 1rem;
}

.feature-card p {
  font-size: 0.9rem;
  color: #666;
  line-height: 1.5;
  margin: 0;
}

/* How It Works Section */
.how-it-works {
  background: white;
  padding: 6rem 2rem;
}

.how-it-works-container {
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
}

.how-it-works h2 {
  font-size: 2.5rem;
  color: #333;
  margin-bottom: 1rem;
}

.how-it-works .subtitle {
  font-size: 1.2rem;
  color: #666;
  margin-bottom: 4rem;
}

.steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 3rem;
}

.step {
  text-align: center;
}

.step-number {
  width: 80px;
  height: 80px;
  background: #8B2BDA;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 2rem;
  color: white;
  font-size: 2rem;
  font-weight: 700;
  box-shadow: 0 10px 25px rgba(139, 43, 218, 0.3);
}

.step h3 {
  font-size: 1.5rem;
  color: #333;
  margin-bottom: 1rem;
}

.step p {
  font-size: 1rem;
  color: #666;
  line-height: 1.6;
}

/* Contact Section */
.contact {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 6rem 2rem;
  color: white;
}

.contact-container {
  max-width: 1200px;
  margin: 0 auto;
}

.contact-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: start;
}

.contact-info h2 {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  color: white;
}

.contact-subtitle {
  font-size: 1.1rem;
  margin-bottom: 3rem;
  opacity: 0.9;
  line-height: 1.6;
}

.contact-details {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.contact-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.contact-icon {
  width: 50px;
  height: 50px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.contact-text h4 {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: white;
}

.contact-text p {
  margin: 0;
  opacity: 0.9;
  line-height: 1.5;
}

.contact-form-wrapper {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 2.5rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.contact-form h3 {
  font-size: 1.5rem;
  margin-bottom: 2rem;
  color: white;
  text-align: center;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.contact-form .form-group {
  margin-bottom: 1.5rem;
}

.contact-form label {
  display: block;
  margin-bottom: 0.5rem;
  color: white;
  font-weight: 500;
  font-size: 0.95rem;
}

.contact-form .form-input,
.form-textarea {
  width: 100%;
  padding: 0.875rem 1rem;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 10px;
  color: white;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.contact-form .form-input::placeholder,
.form-textarea::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.contact-form .form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.6);
  background: rgba(255, 255, 255, 0.2);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 120px;
  font-family: inherit;
}

.contact-btn {
  width: 100%;
  padding: 1rem 2rem;
  background: white;
  color: #667eea;
  border: none;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 1rem;
}

.contact-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 255, 255, 0.3);
}

.contact-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.contact-message {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  font-weight: 500;
  text-align: center;
}

.contact-message.success {
  background: rgba(0, 255, 136, 0.2);
  border: 1px solid rgba(0, 255, 136, 0.4);
  color: #00ff88;
}

.contact-message.error {
  background: rgba(255, 71, 87, 0.2);
  border: 1px solid rgba(255, 71, 87, 0.4);
  color: #ff4757;
}

/* Responsive Design */
@media (max-width: 768px) {
  .hero-container {
    grid-template-columns: 1fr;
    text-align: center;
  }

  .hero-content h1 {
    font-size: 2.5rem;
  }

  .parking-garage {
    width: 300px;
    height: 200px;
  }

  .features-grid,
  .features-grid-2 {
    grid-template-columns: repeat(2, 1fr);
  }

  .stats-container {
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
  }

  .steps {
    grid-template-columns: 1fr;
    gap: 2rem;
  }

  .nav-links {
    display: none;
  }

  .contact-content {
    grid-template-columns: 1fr;
    gap: 3rem;
  }

  .form-row {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .contact-form-wrapper {
    padding: 2rem;
  }
}

@media (max-width: 480px) {
  .hero {
    padding: 5rem 1rem 3rem;
  }

  .hero-content h1 {
    font-size: 2rem;
  }

  .features-grid,
  .features-grid-2 {
    grid-template-columns: 1fr;
  }

  .parking-garage {
    width: 250px;
    height: 150px;
  }

  .real-time-indicator {
    display: none;
  }
}
</style>