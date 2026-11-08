<!--<template>-->
<!--  <div class="app">-->
<!--    <h1>AI Programming Tutor</h1>-->

<!--    <p>-->
<!--      在线编程学习平台 V0.1-->
<!--    </p>-->

<!--    <button @click="checkBackend">-->
<!--      检查后端-->
<!--    </button>-->

<!--    <p v-if="backendStatus">-->
<!--      {{ backendStatus }}-->
<!--    </p>-->
<!--  </div>-->
<!--</template>-->

<!--<script setup lang="ts">-->
<!--import axios from 'axios'-->
<!--import { ref } from 'vue'-->

<!--const backendStatus = ref('')-->

<!--async function checkBackend() {-->
<!--  try {-->
<!--    const response = await axios.get('http://localhost:8080/health')-->

<!--    backendStatus.value = `后端状态：${response.data.status}`-->
<!--  } catch (error) {-->
<!--    console.error(error)-->
<!--    backendStatus.value = '后端连接失败'-->
<!--  }-->
<!--}-->
<!--</script>-->

<!--<style scoped>-->
<!--.app {-->
<!--  padding: 40px;-->
<!--}-->
<!--</style>-->


<template>
  <router-view />
</template>