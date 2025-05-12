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
