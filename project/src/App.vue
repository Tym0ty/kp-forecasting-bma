<template>
  <div id="app">
    <TimeSeriesForecast />
  </div>
</template>

<script>
import TimeSeriesForecast from './components/Forecast.vue';

export default {
  name: 'App',
  components: {
    TimeSeriesForecast
  }
};
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
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 2rem;
}
</style>
