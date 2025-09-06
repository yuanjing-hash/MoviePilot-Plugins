<template>
  <div class="plugin-page">
    <v-card flat class="rounded border" style="display: flex; flex-direction: column; max-height: 85vh;">
      <!-- 标题区域 -->
      <v-card-title class="text-subtitle-1 d-flex align-center px-3 py-1 bg-primary-gradient">
        <v-icon icon="mdi-cloud-sync" class="mr-2" color="primary" size="small" />
        <span>123分享转存</span>
      </v-card-title>

      <!-- 主要内容区域 -->
      <v-card-text class="px-3 py-2" style="flex-grow: 1; overflow-y: auto;">
        <v-alert v-if="error" type="error" density="compact" class="mb-3" variant="tonal" closable>
          {{ error }}
        </v-alert>
        
        <v-alert v-if="successMessage" type="success" density="compact" class="mb-3" variant="tonal" closable>
          {{ successMessage }}
        </v-alert>

        <!-- 转存表单 -->
        <v-card flat class="rounded mb-3 border">
          <v-card-title class="text-subtitle-2 d-flex align-center px-3 py-1 bg-primary-gradient">
            <v-icon icon="mdi-content-save-move" class="mr-2" color="primary" size="small" />
            <span>转存分享链接</span>
          </v-card-title>
          
          <v-card-text class="pa-3">
            <v-form @submit.prevent="startTransfer">
              <v-row>
                <v-col cols="12">
                  <v-text-field
                    v-model="shareLink"
                    label="123云盘分享链接"
                    placeholder="https://www.123684.com/s/xxxxx?提取码:1234"
                    hint="请输入123云盘的分享链接，支持带提取码的链接"
                    persistent-hint
                    variant="outlined"
                    density="compact"
                    clearable
                    required
                  ></v-text-field>
                </v-col>
              </v-row>

              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="sharePassword"
                    label="提取码（可选）"
                    placeholder="1234"
                    hint="如果分享链接需要提取码，请在此输入"
                    persistent-hint
                    variant="outlined"
                    density="compact"
                    clearable
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="savePath"
                    label="保存路径"
                    placeholder="/我的资源/电影"
                    hint="文件将保存到此网盘路径下，留空使用默认路径"
                    persistent-hint
                    variant="outlined"
                    density="compact"
                    clearable
                  ></v-text-field>
                </v-col>
              </v-row>

              <v-row>
                <v-col cols="12" class="d-flex justify-end">
                  <v-btn
                    color="primary"
                    variant="elevated"
                    size="large"
                    :loading="transferring"
                    :disabled="!shareLink || !initialConfig.enabled"
                    @click="startTransfer"
                  >
                    <v-icon size="small" class="mr-2">mdi-cloud-download</v-icon>
                    开始转存
                  </v-btn>
                </v-col>
              </v-row>
            </v-form>
          </v-card-text>
        </v-card>

        <!-- 状态信息 -->
        <v-card flat class="rounded mb-3 border">
          <v-card-title class="text-subtitle-2 d-flex align-center px-3 py-1 bg-primary-gradient">
            <v-icon icon="mdi-information" class="mr-2" color="primary" size="small" />
            <span>插件状态</span>
          </v-card-title>
          
          <v-card-text class="pa-0">
            <v-list class="bg-transparent pa-0">
              <v-list-item class="px-3 py-1">
                <template v-slot:prepend>
                  <v-icon :color="initialConfig.enabled ? 'success' : 'grey'" icon="mdi-power" size="small" />
                </template>
                <v-list-item-title class="text-body-2">插件状态</v-list-item-title>
                <template v-slot:append>
                  <v-chip :color="initialConfig.enabled ? 'success' : 'grey'" size="x-small" variant="tonal">
                    {{ initialConfig.enabled ? '已启用' : '已禁用' }}
                  </v-chip>
                </template>
              </v-list-item>
              
              <v-divider class="my-0"></v-divider>
              
              <v-list-item class="px-3 py-1">
                <template v-slot:prepend>
                  <v-icon :color="hasValidConfig ? 'success' : 'error'" icon="mdi-account-check" size="small" />
                </template>
                <v-list-item-title class="text-body-2">123云盘配置</v-list-item-title>
                <template v-slot:append>
                  <v-chip :color="hasValidConfig ? 'success' : 'error'" size="x-small" variant="tonal">
                    {{ hasValidConfig ? '已配置' : '未配置' }}
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>

        <!-- 使用说明 -->
        <v-card flat class="rounded mb-3 border">
          <v-card-title class="text-subtitle-2 d-flex align-center px-3 py-1 bg-primary-gradient">
            <v-icon icon="mdi-help-circle" class="mr-2" color="primary" size="small" />
            <span>使用说明</span>
          </v-card-title>
          
          <v-card-text class="pa-3">
            <div class="text-body-2">
              <p class="mb-2"><strong>支持的使用方式：</strong></p>
              <ul class="mb-3">
                <li>网页操作：在上方输入分享链接和保存路径，点击开始转存</li>
                <li>消息命令：发送 <code>/123save &lt;分享链接&gt; [保存路径]</code></li>
              </ul>
              
              <p class="mb-2"><strong>支持的分享链接格式：</strong></p>
              <ul class="mb-3">
                <li><code>https://www.123684.com/s/xxxxx</code>（无密码）</li>
                <li><code>https://www.123684.com/s/xxxxx?提取码:1234</code>（带密码）</li>
              </ul>
              
              <v-alert type="warning" variant="tonal" density="compact">
                <strong>注意：</strong>使用前请先在配置页面中设置123云盘账号密码
              </v-alert>
            </div>
          </v-card-text>
        </v-card>
      </v-card-text>

      <!-- 底部按钮 -->
      <v-divider></v-divider>
      <v-card-actions class="px-3 py-1 d-flex justify-space-between">
        <v-btn color="info" @click="refreshStatus" :loading="refreshing" variant="text" size="small">
          <v-icon size="small" class="mr-1">mdi-refresh</v-icon>
          刷新状态
        </v-btn>
        
        <div class="d-flex align-center" style="gap: 8px;">
          <v-btn color="primary" @click="emit('switch')" variant="text" size="small">
            <v-icon size="small" class="mr-1">mdi-cog</v-icon>
            配置
          </v-btn>
          <v-btn color="error" @click="emit('close')" variant="flat" size="small">
            <v-icon size="small">mdi-close</v-icon>
          </v-btn>
        </div>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'

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
const shareLink = ref('')
const sharePassword = ref('')
const savePath = ref('')
const transferring = ref(false)
const refreshing = ref(false)
const error = ref(null)
const successMessage = ref(null)

// 计算属性
const hasValidConfig = computed(() => {
  return props.initialConfig.passport && props.initialConfig.password
})

// 开始转存
const startTransfer = async () => {
  if (!shareLink.value) {
    error.value = '请输入分享链接'
    return
  }

  if (!props.initialConfig.enabled) {
    error.value = '插件未启用，请先在配置页面启用插件'
    return
  }

  if (!hasValidConfig.value) {
    error.value = '请先在配置页面设置123云盘账号密码'
    return
  }

  transferring.value = true
  error.value = null
  successMessage.value = null

  try {
    const pluginId = "P123Share"
    const result = await props.api.post(`plugin/${pluginId}/transfer`, {
      shareLink: shareLink.value,
      sharePassword: sharePassword.value,
      savePath: savePath.value || props.initialConfig.transfer_save_path
    })

    if (result && result.success) {
      successMessage.value = result.message || '转存任务已启动'
      // 清空表单
      shareLink.value = ''
      sharePassword.value = ''
      savePath.value = ''
    } else {
      throw new Error(result?.message || '转存失败')
    }
  } catch (err) {
    error.value = `转存失败: ${err.message || '未知错误'}`
    console.error('转存失败:', err)
  } finally {
    transferring.value = false
  }
}

// 刷新状态
const refreshStatus = async () => {
  refreshing.value = true
  error.value = null
  
  try {
    const pluginId = "P123Share"
    const result = await props.api.get(`plugin/${pluginId}/get_config`)
    
    if (result) {
      Object.assign(props.initialConfig, result)
      successMessage.value = '状态已刷新'
    }
  } catch (err) {
    error.value = `刷新状态失败: ${err.message || '未知错误'}`
    console.error('刷新状态失败:', err)
  } finally {
    refreshing.value = false
  }
}

// 初始化
onMounted(() => {
  // 设置默认保存路径
  if (props.initialConfig.transfer_save_path) {
    savePath.value = props.initialConfig.transfer_save_path
  }
})
</script>

<style scoped>
.plugin-page {
  font-family: 'Roboto', sans-serif;
}

.bg-primary-gradient {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.1), rgba(var(--v-theme-primary), 0.05)) !important;
}

code {
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  padding: 2px 4px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.85em;
}

ul {
  padding-left: 1.2em;
}

li {
  margin-bottom: 0.3em;
}
</style>
