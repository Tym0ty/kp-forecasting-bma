<template>
  <div id="app">
    <AppHeader />
    <main class="main-content">
      <router-view></router-view>
    </main>
  </div>
</template>

<script>
import AppHeader from './components/Header.vue'

export default {
  name: 'App',
  components: {
    AppHeader
  }
}
</script>

<style>
/* Global styles */
* {
  box-sizing: border-box;
  font-family: 'Roboto', sans-serif;
}

html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
  background-color: #f9fafb;
}

#app {
  width: 100%;
  min-height: 100vh;
}

.main-content {
  padding: 4rem 2rem 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .main-content {
    padding: 4rem 1rem 1rem;
  }
}

#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
  background-color: #f8f9fa;
}

body {
  margin: 0;
  padding: 0;
}
</style>
