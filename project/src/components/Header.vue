<template>
  <header class="header">
    <div class="header-content">
      <div class="brand">Forecasting BMA</div>
      <nav>
        <router-link to="/" class="nav-link" exact>Graph</router-link>
        <router-link to="/upload" class="nav-link">Upload</router-link>
        <router-link to="/forecast" class="nav-link">Forecast</router-link>
        <router-link to="/forecast-history" class="nav-link">History</router-link>
      </nav>
    </div>
  </header>
</template>

<script>
export default {
  name: 'AppHeader'
}
</script>

<style scoped>
.header {
  background-color: #2F3B4B;
  width: 100%;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1000;
}

.header-content {
  display: flex;
  align-items: center;
  padding: 0.75rem 1.5rem;
}

.brand {
  color: white;
  font-size: 1.25rem;
  font-weight: 500;
  margin-right: 2rem;
}

nav {
  display: flex;
  gap: 0.5rem;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-weight: 400;
  transition: background-color 0.2s;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.router-link-active {
  background-color: #4CAF50;
}

@media (max-width: 768px) {
  .header-content {
    padding: 0.75rem 1rem;
  }

  .brand {
    font-size: 1.1rem;
    margin-right: 1rem;
  }

  .nav-link {
    padding: 0.4rem 0.8rem;
  }
}
</style> 