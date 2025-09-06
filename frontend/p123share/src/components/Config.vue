<template>
  <div class="config-page">
    <v-card flat class="rounded border" style="display: flex; flex-direction: column; max-height: 85vh;">
      <!-- 标题区域 -->
      <v-card-title class="text-subtitle-1 d-flex align-center px-3 py-1 bg-primary-gradient">
        <v-icon icon="mdi-cog" class="mr-2" color="primary" size="small" />
        <span>123分享转存 - 配置</span>
      </v-card-title>

      <!-- 配置表单 -->
      <v-card-text class="px-3 py-2" style="flex-grow: 1; overflow-y: auto;">
        <v-alert v-if="error" type="error" density="compact" class="mb-3" variant="tonal" closable>
          {{ error }}
        </v-alert>
        
        <v-alert v-if="successMessage" type="success" density="compact" class="mb-3" variant="tonal" closable>
          {{ successMessage }}
        </v-alert>

        <v-form @submit.prevent="saveConfig">
          <v-row>
            <v-col cols="12">
              <v-switch
                v-model="config.enabled"
                label="启用插件"
                color="primary"
                density="compact"
              ></v-switch>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="config.passport"
                label="123云盘账号"
                hint="123云盘登录账号（手机号/邮箱）"
                persistent-hint
                variant="outlined"
                density="compact"
                required
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="config.password"
                label="123云盘密码"
                type="password"
                hint="123云盘登录密码"
                persistent-hint
                variant="outlined"
                density="compact"
                required
              ></v-text-field>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="config.transfer_save_path"
                label="默认保存路径"
                hint="消息或WebUI触发转存时的默认网盘保存路径"
                persistent-hint
                variant="outlined"
                density="compact"
                placeholder="/我的资源"
              ></v-text-field>
            </v-col>
          </v-row>

          <v-alert type="info" variant="tonal" density="compact" class="mt-3">
            <div class="text-body-2">
              <strong>使用说明：</strong><br>
              1. 配置123云盘账号密码后，插件会自动登录<br>
              2. 支持消息命令：/123save &lt;分享链接&gt; [保存路径]<br>
              3. 支持Web界面操作转存<br>
              4. 支持带提取码的分享链接自动识别
            </div>
          </v-alert>
        </v-form>
      </v-card-text>

      <!-- 底部按钮 -->
      <v-divider></v-divider>
      <v-card-actions class="px-3 py-1 d-flex justify-space-between">
        <v-btn color="info" @click="testConnection" :loading="testing" variant="text" size="small">
          <v-icon size="small" class="mr-1">mdi-connection</v-icon>
          测试连接
        </v-btn>
        
        <div class="d-flex align-center" style="gap: 8px;">
          <v-btn color="primary" @click="saveConfig" :loading="saving" variant="text" size="small">
            <v-icon size="small" class="mr-1">mdi-content-save</v-icon>
            保存配置
          </v-btn>
          <v-btn color="grey" @click="emit('close')" variant="text" size="small">
            <v-icon size="small" class="mr-1">mdi-arrow-left</v-icon>
            返回
          </v-btn>
        </div>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

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

const emit = defineEmits(['close', 'switch'])

// 响应式数据
const config = reactive({
  enabled: false,
  passport: '',
  password: '',
  transfer_save_path: '/'
})

const error = ref(null)
const successMessage = ref(null)
const saving = ref(false)
const testing = ref(false)

// 保存配置
const saveConfig = async () => {
  saving.value = true
  error.value = null
  successMessage.value = null

  try {
    if (!config.passport || !config.password) {
      throw new Error('请填写123云盘账号和密码')
    }

    const pluginId = "P123Share"
    const result = await props.api.post(`plugin/${pluginId}/save_config`, config)

    if (result && result.code === 0) {
      successMessage.value = '配置保存成功'
      // 更新初始配置
      Object.assign(props.initialConfig, config)
    } else {
      throw new Error(result?.msg || '保存配置失败')
    }
  } catch (err) {
    error.value = `保存失败: ${err.message || '未知错误'}`
    console.error('保存配置失败:', err)
  } finally {
    saving.value = false
  }
}

// 测试连接
const testConnection = async () => {
  testing.value = true
  error.value = null
  successMessage.value = null

  try {
    if (!config.passport || !config.password) {
      throw new Error('请先填写123云盘账号和密码')
    }

    const pluginId = "P123Share"
    const result = await props.api.post(`plugin/${pluginId}/test_connection`, {
      passport: config.passport,
      password: config.password
    })

    if (result && result.success) {
      successMessage.value = '连接测试成功'
    } else {
      throw new Error(result?.message || '连接测试失败')
    }
  } catch (err) {
    error.value = `连接测试失败: ${err.message || '未知错误'}`
    console.error('连接测试失败:', err)
  } finally {
    testing.value = false
  }
}

// 初始化配置
onMounted(() => {
  if (props.initialConfig) {
    Object.assign(config, {
      enabled: props.initialConfig.enabled || false,
      passport: props.initialConfig.passport || '',
      password: props.initialConfig.password || '',
      transfer_save_path: props.initialConfig.transfer_save_path || '/'
    })
  }
})
</script>

<style scoped>
.config-page {
  font-family: 'Roboto', sans-serif;
}

.bg-primary-gradient {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.1), rgba(var(--v-theme-primary), 0.05)) !important;
}
</style>
