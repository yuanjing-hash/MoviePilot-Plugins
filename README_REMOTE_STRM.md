# 远程STRM生成插件

## 项目概述

本项目实现了跨服务器的STRM生成功能，将下载服务器和STRM生成服务器分离，通过HTTP API进行通信。解决了单台服务器资源限制的问题，实现了更灵活的部署架构。

## 文件结构

```
MoviePilot-Plugins/
├── plugins.v2/
│   ├── p123disk_remote/          # 远程STRM通知的123云盘插件
│   │   ├── __init__.py
│   │   ├── p123_api.py
│   │   └── requirements.txt
│   └── p123strmhelper_remote/    # 远程STRM生成助手插件
│       ├── __init__.py
│       ├── tool.py
│       └── requirements.txt
├── docs/
│   └── remote_strm_setup.md      # 详细使用说明
├── config_example.json           # 配置示例
├── test_remote_strm.py           # API测试脚本
├── deploy_remote_plugins.sh      # 部署脚本
└── README_REMOTE_STRM.md         # 本文件
```

## 核心功能

### 1. p123disk_remote 插件
- **基础功能**：继承原有p123disk插件的所有功能
- **新增功能**：
  - 文件上传完成后自动发送HTTP通知到远程STRM服务器
  - 支持API密钥认证
  - 完整的错误处理和日志记录

### 2. p123strmhelper_remote 插件
- **基础功能**：继承原有p123strmhelper插件的所有功能
- **新增功能**：
  - 接收远程上传完成通知的API接口
  - 根据通知信息生成STRM文件
  - STRM生成完成后发送回调通知
  - API密钥验证和安全性保护

## 技术架构

### 通信流程
```
服务器A (下载) → 上传文件到123云盘 → 发送HTTP通知 → 服务器B (STRM生成)
     ↓                                                      ↓
触发通知事件                                           生成STRM文件
     ↓                                                      ↓
                                                     回调通知完成
```

### API接口
1. **上传完成通知**: `POST /api/v1/plugin/P123StrmHelperRemote/notify/upload_complete`
2. **STRM完成回调**: `POST /api/v1/plugin/P123StrmHelperRemote/callback/strm_complete`
3. **302跳转服务**: `GET /api/v1/plugin/P123StrmHelperRemote/redirect_url`

### 数据格式
```json
{
  "file_info": {
    "file_name": "电影名称.mkv",
    "file_size": 1234567890,
    "file_md5": "abc123...",
    "s3_key_flag": "def456...",
    "pan_path": "/媒体库/电影/电影名称.mkv",
    "upload_time": "2024-01-01T12:00:00Z"
  },
  "media_info": {
    "title": "电影名称",
    "year": 2024,
    "type": "movie",
    "category": "电影"
  },
  "callback_url": "http://服务器A/api/callback/strm_complete"
}
```

## 快速开始

### 1. 部署插件
```bash
# 运行部署脚本
./deploy_remote_plugins.sh
```

### 2. 配置服务器A (下载服务器)
- 启用 `p123disk_remote` 插件
- 配置123云盘账号信息
- 启用远程STRM通知
- 设置STRM服务器地址和API密钥

### 3. 配置服务器B (STRM生成服务器)
- 启用 `p123strmhelper_remote` 插件
- 配置123云盘账号信息
- 启用远程通知接收
- 设置相同的API密钥

### 4. 测试功能
```bash
# 运行测试脚本
python test_remote_strm.py
```

## 配置说明

### 服务器A配置项
```json
{
  "enabled": true,
  "passport": "手机号",
  "password": "密码",
  "enable_strm_notification": true,
  "strm_server_url": "http://192.168.1.100:3000",
  "strm_api_key": "your_shared_api_key"
}
```

### 服务器B配置项
```json
{
  "enabled": true,
  "passport": "手机号",
  "password": "密码",
  "moviepilot_address": "http://192.168.1.100:3000",
  "enable_remote_notification": true,
  "api_key": "your_shared_api_key",
  "callback_timeout": 30
}
```

## 安全考虑

1. **API密钥认证**：所有API请求都需要有效的API密钥
2. **网络隔离**：建议在内网环境使用
3. **HTTPS加密**：生产环境建议使用HTTPS
4. **防火墙配置**：限制API端点的访问权限

## 故障排除

### 常见问题
1. **通知发送失败**：检查网络连通性和服务器地址配置
2. **STRM生成失败**：验证123云盘账号和文件信息
3. **API认证失败**：确认API密钥配置一致

### 日志查看
插件会记录详细的执行日志，包括：
- 通知发送状态
- STRM生成结果
- 错误信息和异常堆栈

## 扩展功能

当前实现提供了基础框架，可以扩展：
1. **路径映射配置**：网盘路径到本地路径的自动映射
2. **媒体信息识别**：根据文件名自动识别媒体类型
3. **批量处理**：支持批量文件处理
4. **重试机制**：失败重试和队列管理
5. **监控面板**：Web界面查看处理状态

## 版本信息

- **p123disk_remote**: v1.2.0
- **p123strmhelper_remote**: v1.1.0
- **兼容性**: MoviePilot最新版本
- **Python版本**: 3.8+

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

本项目遵循原项目的许可证条款。

## 联系方式

如有问题，请通过以下方式联系：
- GitHub Issues
- 项目讨论区

---

**注意**: 这是一个实验性功能，建议在测试环境中充分验证后再部署到生产环境。
