<template>
  <div class="plugin-page">
    <div class="card">
      <!-- 标题区域 -->
      <div class="card-header">
        <span class="icon">☁️</span>
        <span>123分享转存</span>
      </div>

      <!-- 主要内容区域 -->
      <div class="card-content">
        <!-- 错误提示 -->
        <div v-if="error" class="alert alert-error">
          {{ error }}
          <button @click="error = null" class="alert-close">×</button>
        </div>
        
        <!-- 成功提示 -->
        <div v-if="successMessage" class="alert alert-success">
          {{ successMessage }}
          <button @click="successMessage = null" class="alert-close">×</button>
        </div>

        <!-- 转存表单 -->
        <div class="form-section">
          <h3>转存分享链接</h3>
          
          <form @submit.prevent="startTransfer">
            <div class="form-group">
              <label for="shareLink">123云盘分享链接</label>
              <input
                id="shareLink"
                v-model="shareLink"
                type="text"
                placeholder="https://www.123684.com/s/xxxxx?提取码:1234"
                required
              />
              <small>请输入123云盘的分享链接，支持带提取码的链接</small>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="sharePassword">提取码（可选）</label>
                <input
                  id="sharePassword"
                  v-model="sharePassword"
                  type="text"
                  placeholder="1234"
                />
                <small>如果分享链接需要提取码，请在此输入</small>
              </div>
              
              <div class="form-group">
                <label for="savePath">保存路径</label>
                <input
                  id="savePath"
                  v-model="savePath"
                  type="text"
                  placeholder="/我的资源/电影"
                />
                <small>文件将保存到此网盘路径下，留空使用默认路径</small>
              </div>
            </div>

            <div class="form-actions">
              <button
                type="submit"
                class="btn btn-primary"
                :disabled="!shareLink || !initialConfig.enabled || transferring"
              >
                <span v-if="transferring">转存中...</span>
                <span v-else>开始转存</span>
              </button>
            </div>
          </form>
        </div>

        <!-- 状态信息 -->
        <div class="status-section">
          <h3>插件状态</h3>
          
          <div class="status-item">
            <span class="status-label">插件状态:</span>
            <span :class="['status-badge', initialConfig.enabled ? 'status-success' : 'status-grey']">
              {{ initialConfig.enabled ? '已启用' : '已禁用' }}
            </span>
          </div>
          
          <div class="status-item">
            <span class="status-label">123云盘配置:</span>
            <span :class="['status-badge', hasValidConfig ? 'status-success' : 'status-error']">
              {{ hasValidConfig ? '已配置' : '未配置' }}
            </span>
          </div>
        </div>

        <!-- 使用说明 -->
        <div class="help-section">
          <h3>使用说明</h3>
          
          <div class="help-content">
            <p><strong>支持的使用方式：</strong></p>
            <ul>
              <li>网页操作：在上方输入分享链接和保存路径，点击开始转存</li>
              <li>消息命令：发送 <code>/123save &lt;分享链接&gt; [保存路径]</code></li>
            </ul>
            
            <p><strong>支持的分享链接格式：</strong></p>
            <ul>
              <li><code>https://www.123684.com/s/xxxxx</code>（无密码）</li>
              <li><code>https://www.123684.com/s/xxxxx?提取码:1234</code>（带密码）</li>
            </ul>
            
            <div class="alert alert-warning">
              <strong>注意：</strong>使用前请先在配置页面中设置123云盘账号密码
            </div>
          </div>
        </div>
      </div>

      <!-- 底部按钮 -->
      <div class="card-footer">
        <button @click="refreshStatus" :disabled="refreshing" class="btn btn-secondary">
          {{ refreshing ? '刷新中...' : '刷新状态' }}
        </button>
        
        <div class="footer-actions">
          <button @click="$emit('switch')" class="btn btn-primary">配置</button>
          <button @click="$emit('close')" class="btn btn-danger">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

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
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  background: linear-gradient(135deg, #1976d2, #1565c0);
  color: white;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 500;
}

.icon {
  font-size: 20px;
}

.card-content {
  padding: 20px;
}

.card-footer {
  background: #f5f5f5;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #e0e0e0;
}

.footer-actions {
  display: flex;
  gap: 8px;
}

/* 表单样式 */
.form-section, .status-section, .help-section {
  margin-bottom: 24px;
}

.form-section h3, .status-section h3, .help-section h3 {
  color: #1976d2;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 500;
}

.form-group {
  margin-bottom: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
  color: #333;
}

.form-group input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #1976d2;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
}

.form-group small {
  display: block;
  margin-top: 4px;
  color: #666;
  font-size: 12px;
}

.form-actions {
  text-align: right;
}

/* 按钮样式 */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #1976d2;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1565c0;
}

.btn-secondary {
  background: #757575;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #616161;
}

.btn-danger {
  background: #d32f2f;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #c62828;
}

/* 状态样式 */
.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.status-item:last-child {
  border-bottom: none;
}

.status-label {
  font-weight: 500;
  color: #333;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-success {
  background: #e8f5e8;
  color: #2e7d32;
}

.status-error {
  background: #ffebee;
  color: #c62828;
}

.status-grey {
  background: #f5f5f5;
  color: #757575;
}

/* 提示框样式 */
.alert {
  padding: 12px 16px;
  border-radius: 4px;
  margin-bottom: 16px;
  position: relative;
}

.alert-error {
  background: #ffebee;
  color: #c62828;
  border: 1px solid #ffcdd2;
}

.alert-success {
  background: #e8f5e8;
  color: #2e7d32;
  border: 1px solid #c8e6c9;
}

.alert-warning {
  background: #fff3e0;
  color: #ef6c00;
  border: 1px solid #ffcc02;
}

.alert-close {
  position: absolute;
  top: 8px;
  right: 12px;
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: inherit;
  opacity: 0.7;
}

.alert-close:hover {
  opacity: 1;
}

/* 帮助内容样式 */
.help-content ul {
  margin: 8px 0;
  padding-left: 20px;
}

.help-content li {
  margin-bottom: 4px;
}

.help-content code {
  background: #f5f5f5;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .card-footer {
    flex-direction: column;
    gap: 12px;
  }
  
  .footer-actions {
    width: 100%;
    justify-content: center;
  }
}
</style>