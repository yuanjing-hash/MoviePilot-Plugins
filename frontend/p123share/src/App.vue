<template>
  <div id="app">
    <Config v-if="showConfig" 
            :api="api" 
            :initialConfig="initialConfig" 
            @close="showConfig = false" 
            @switch="showConfig = false" />
    <Page v-else 
          :api="api" 
          :initialConfig="initialConfig" 
          @close="$emit('close')" 
          @switch="showConfig = true" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Config from './components/Config.vue'
import Page from './components/Page.vue'

const props = defineProps({
  api: {
    type: [Object, Function],
    required: true
  },
  initialConfig: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close'])

const showConfig = ref(false)

onMounted(() => {
  // 默认显示主页面
  showConfig.value = false
})
</script>

<style>
#app {
  font-family: 'Roboto', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}
</style>
