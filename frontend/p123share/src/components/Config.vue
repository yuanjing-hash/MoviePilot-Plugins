<template>
  <div class="config-page">
    <div class="card">
      <!-- 标题区域 -->
      <div class="card-header">
        <span class="icon">⚙️</span>
        <span>123分享转存 - 配置</span>
      </div>

      <!-- 配置表单 -->
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

        <form @submit.prevent="saveConfig">
          <div class="form-group">
            <label class="checkbox-label">
              <input
                v-model="config.enabled"
                type="checkbox"
              />
              <span class="checkmark"></span>
              启用插件
            </label>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="passport">123云盘账号</label>
              <input
                id="passport"
                v-model="config.passport"
                type="text"
                placeholder="手机号或邮箱"
                required
              />
              <small>123云盘登录账号（手机号/邮箱）</small>
            </div>
            
            <div class="form-group">
              <label for="password">123云盘密码</label>
              <input
                id="password"
                v-model="config.password"
                type="password"
                placeholder="登录密码"
                required
              />
              <small>123云盘登录密码</small>
            </div>
          </div>

          <div class="form-group">
            <label for="transfer_save_path">默认保存路径</label>
            <input
              id="transfer_save_path"
              v-model="config.transfer_save_path"
              type="text"
              placeholder="/我的资源"
            />
            <small>消息或WebUI触发转存时的默认网盘保存路径</small>
          </div>

          <div class="alert alert-info">
            <div class="help-content">
              <strong>使用说明：</strong><br>
              1. 配置123云盘账号密码后，插件会自动登录<br>
              2. 支持消息命令：/123save &lt;分享链接&gt; [保存路径]<br>
              3. 支持Web界面操作转存<br>
              4. 支持带提取码的分享链接自动识别
            </div>
          </div>
        </form>
      </div>

      <!-- 底部按钮 -->
      <div class="card-footer">
        <button @click="testConnection" :disabled="testing" class="btn btn-secondary">
          {{ testing ? '测试中...' : '测试连接' }}
        </button>
        
        <div class="footer-actions">
          <button @click="saveConfig" :disabled="saving" class="btn btn-primary">
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
          <button @click="$emit('close')" class="btn btn-secondary">返回</button>
        </div>
      </div>
    </div>
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
  max-width: 600px;
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

.form-group input[type="text"],
.form-group input[type="password"] {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input[type="text"]:focus,
.form-group input[type="password"]:focus {
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

/* 复选框样式 */
.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-weight: 500;
  color: #333;
}

.checkbox-label input[type="checkbox"] {
  display: none;
}

.checkmark {
  width: 20px;
  height: 20px;
  border: 2px solid #ddd;
  border-radius: 4px;
  margin-right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.checkbox-label input[type="checkbox"]:checked + .checkmark {
  background: #1976d2;
  border-color: #1976d2;
}

.checkbox-label input[type="checkbox"]:checked + .checkmark::after {
  content: '✓';
  color: white;
  font-size: 14px;
  font-weight: bold;
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

.alert-info {
  background: #e3f2fd;
  color: #1565c0;
  border: 1px solid #bbdefb;
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

.help-content {
  font-size: 14px;
  line-height: 1.5;
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