# 远程STRM生成插件使用说明

## 概述

本方案实现了跨服务器的STRM生成功能，将下载服务器和STRM生成服务器分离，通过HTTP API进行通信。

## 架构说明

```
服务器A (下载服务器)         服务器B (STRM生成服务器)
     ↓                              ↓
p123disk_remote (上传完成)  → HTTP通知 → p123strmhelper_remote (API接收)
     ↓                              ↓
触发通知事件                   生成STRM文件
     ↓                              ↓
                             通知MP入库完成
```

## 插件说明

### 1. p123disk_remote 插件
- **功能**：在原有p123disk基础上，添加了上传完成后的远程通知功能
- **位置**：`plugins.v2/p123disk_remote/`
- **新增配置**：
  - `enable_strm_notification`: 启用远程STRM通知
  - `strm_server_url`: STRM服务器地址
  - `strm_api_key`: API密钥

### 2. p123strmhelper_remote 插件
- **功能**：在原有p123strmhelper基础上，添加了接收远程通知和生成STRM的API接口
- **位置**：`plugins.v2/p123strmhelper_remote/`
- **新增配置**：
  - `enable_remote_notification`: 启用远程通知接收
  - `api_key`: API密钥
  - `callback_timeout`: 回调超时时间

## 安装配置

### 服务器A (下载服务器) 配置

1. 安装 `p123disk_remote` 插件
2. 配置插件参数：
   - 启用插件
   - 配置123云盘账号信息
   - **启用远程STRM通知**
   - **配置STRM服务器地址** (服务器B的地址)
   - **配置API密钥** (与服务器B保持一致)

### 服务器B (STRM生成服务器) 配置

1. 安装 `p123strmhelper_remote` 插件
2. 配置插件参数：
   - 启用插件
   - 配置123云盘账号信息
   - 配置MoviePilot内网访问地址
   - **启用远程通知接收**
   - **配置API密钥** (与服务器A保持一致)
   - 配置其他STRM生成相关参数

## API接口说明

### 1. 上传完成通知接口
- **URL**: `POST /api/v1/plugin/P123StrmHelperRemote/notify/upload_complete`
- **认证**: Bearer Token
- **请求体**:
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

### 2. STRM生成完成回调接口
- **URL**: `POST /api/v1/plugin/P123StrmHelperRemote/callback/strm_complete`
- **请求体**:
```json
{
  "success": true,
  "message": "STRM生成成功",
  "strm_path": "/strm/media/电影名称.strm",
  "media_refresh": {
    "success": true,
    "message": "媒体服务器刷新完成",
    "details": {
      "Plex": {"success": true, "message": "刷新成功"},
      "Emby": {"success": true, "message": "刷新成功"}
    }
  },
  "library_info": {
    "title": "电影名称",
    "year": 2024,
    "type": "movie",
    "category": "电影",
    "file_name": "电影名称.mkv",
    "strm_path": "/strm/media/电影名称.strm",
    "pan_path": "/媒体库/电影/电影名称.mkv"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 工作流程

1. **文件上传**：服务器A上的MoviePilot下载文件并上传到123云盘
2. **发送通知**：p123disk_remote插件检测到上传完成，发送HTTP通知到服务器B
3. **接收通知**：服务器B的p123strmhelper_remote插件接收通知
4. **生成STRM**：根据通知信息生成对应的STRM文件
5. **刷新媒体服务器**：STRM生成完成后，自动刷新配置的媒体服务器（Plex、Emby等）
6. **回调通知**：将STRM生成结果、媒体服务器刷新状态和入库信息发送回服务器A
7. **MoviePilot通知**：服务器A接收到回调后，触发MoviePilot内置通知系统，通过配置的通知渠道发送入库完成消息

## 注意事项

1. **网络连通性**：确保两台服务器之间网络互通
2. **API密钥**：两台服务器必须使用相同的API密钥
3. **路径映射**：需要根据实际情况配置本地STRM文件保存路径
4. **错误处理**：插件包含完整的错误处理和日志记录
5. **安全性**：建议在内网环境使用，或配置适当的防火墙规则

## 故障排除

### 常见问题

1. **通知发送失败**
   - 检查网络连通性
   - 验证STRM服务器地址配置
   - 确认API密钥正确

2. **STRM生成失败**
   - 检查123云盘账号配置
   - 验证文件信息完整性
   - 查看插件日志

3. **回调通知失败**
   - 检查回调URL配置
   - 验证网络连通性
   - 确认超时时间设置

### 日志查看

插件运行日志会记录详细的执行过程，包括：
- 通知发送状态
- STRM生成结果
- 回调通知状态
- 错误信息

## 扩展功能

当前实现提供了基础框架，可以根据需要扩展以下功能：

1. **路径映射配置**：添加网盘路径到本地路径的映射配置
2. **媒体信息识别**：根据文件名自动识别媒体类型和年份
3. **批量处理**：支持批量文件的通知和STRM生成
4. **重试机制**：添加失败重试和队列机制
5. **监控面板**：添加Web界面查看处理状态

## MoviePilot内置通知系统

### 通知机制

本插件使用MoviePilot内置的通知系统，无需额外配置通知渠道。当接收到STRM生成完成回调时，插件会自动触发MoviePilot的通知事件。

### 支持的通知渠道

通过MoviePilot的通知设置，可以配置以下通知渠道：
- 📱 微信通知（企业微信、个人微信）
- 📧 邮件通知
- 🔔 钉钉通知
- 📲 其他自定义通知渠道

### 通知消息内容

通知消息包含以下详细信息：
- 📺 媒体标题和年份
- 🎭 媒体类型（电影/电视剧）
- 📂 分类信息
- 📁 文件名
- 📋 处理状态（STRM生成、媒体服务器刷新）
- 📂 文件路径信息
- ⏰ 完成时间

### 配置方法

1. 在MoviePilot设置中配置通知渠道
2. 启用相应的通知方式（微信、邮件等）
3. 插件会自动使用这些配置发送入库完成通知

### 优势

- ✅ 无需重复配置通知渠道
- ✅ 支持多种通知方式
- ✅ 统一的通知管理
- ✅ 与MoviePilot其他功能保持一致

## 版本信息

- p123disk_remote: v1.2.0
- p123strmhelper_remote: v1.1.0
- 兼容MoviePilot版本: 最新版本
