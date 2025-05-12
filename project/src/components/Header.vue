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