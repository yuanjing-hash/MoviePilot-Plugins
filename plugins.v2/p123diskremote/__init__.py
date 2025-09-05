from pathlib import Path
from typing import Any, List, Dict, Tuple, Optional
import json
import requests
from datetime import datetime

from p123client import P123Client
from .p123_api import P123Api

from app import schemas
from app.core.event import eventmanager, Event
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import ChainEventType, EventType
from app.helper.storage import StorageHelper
from schemas import StorageOperSelectionEventData, FileItem


class P123AutoClient:
    """
    123云盘客户端
    """

    def __init__(self, passport, password):
        self._client = None
        self._passport = passport
        self._password = password

    def __getattr__(self, name):
        if self._client is None:
            self._client = P123Client(self._passport, self._password)

        def wrapped(*args, **kwargs):
            attr = getattr(self._client, name)
            if not callable(attr):
                return attr
            result = attr(*args, **kwargs)
            if (
                isinstance(result, dict)
                and result.get("code") == 401
                and result.get("message") == "tokens number has exceeded the limit"
            ):
                self._client = P123Client(self._passport, self._password)
                attr = getattr(self._client, name)
                if not callable(attr):
                    return attr
                return attr(*args, **kwargs)
            return result

        return wrapped


class P123DiskRemote(_PluginBase):
    # 插件名称
    plugin_name = "123云盘储存(远程STRM)"
    # 插件描述
    plugin_desc = "使存储支持123云盘，支持远程STRM生成通知。"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/yuanjing-hash/MoviePilot-Plugins/main/icons/P123Disk.png"
    # 插件版本
    plugin_version = "2.0.2"
    # 插件作者
    plugin_author = "yuanjing"
    # 作者主页
    author_url = "https://github.com/yuanjing-hash"
    # 插件配置项ID前缀
    plugin_config_prefix = "p123disk_remote_"
    # 加载顺序
    plugin_order = 99
    # 可使用的用户级别
    auth_level = 1

    # 是否启用
    _enabled = False
    _client = None
    _disk_name = None
    _p123_api = None
    _passport = None
    _password = None
    # 远程STRM通知相关配置
    _strm_server_url = None
    _enable_strm_notification = False
    _notification_file_extensions = None

    def __init__(self):
        """
        初始化
        """
        super().__init__()

        self._disk_name = "123云盘"

    def init_plugin(self, config: dict = None):
        """
        初始化插件
        """
        if config:
            storage_helper = StorageHelper()
            storages = storage_helper.get_storagies()
            if not any(
                s.type == self._disk_name and s.name == self._disk_name
                for s in storages
            ):
                # 添加云盘存储配置
                storage_helper.add_storage(
                    storage=self._disk_name, name=self._disk_name, conf={}
                )

            self._enabled = config.get("enabled")
            self._passport = config.get("passport")
            self._password = config.get("password")
            # 远程STRM通知配置
            self._strm_server_url = config.get("strm_server_url")
            self._enable_strm_notification = config.get("enable_strm_notification")
            self._notification_file_extensions = config.get("notification_file_extensions")

            try:
                self._client = P123AutoClient(self._passport, self._password)
                self._p123_api = P123Api(client=self._client, disk_name=self._disk_name)
            except Exception as e:
                logger.error(f"123云盘客户端创建失败: {e}")

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        """
        获取API接口
        """
        return [
            {
                "path": "/callback/strm_complete",
                "endpoint": self.callback_strm_complete,
                "methods": ["POST"],
                "summary": "STRM生成完成回调",
                "description": "接收STRM生成完成回调通知",
            }
        ]

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "enabled",
                                            "label": "启用插件",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "passport",
                                            "label": "手机号",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "password",
                                            "label": "密码",
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "enable_strm_notification",
                                            "label": "启用远程STRM通知",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "strm_server_url",
                                            "label": "STRM服务器地址",
                                            "placeholder": "http://192.168.1.100:3000",
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "notification_file_extensions",
                                            "label": "通知文件扩展名",
                                            "placeholder": "mp4,mkv,ts,iso,rmvb,avi,mov,mpeg,mpg,wmv,3gp,asf,m4v,flv,m2ts,tp,f4v",
                                            "hint": "只有这些扩展名的文件上传完成后才会发送通知，多个扩展名用逗号分隔",
                                            "persistent-hint": True,
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                ],
            }
        ], {
            "enabled": False,
            "passport": "",
            "password": "",
            "enable_strm_notification": False,
            "strm_server_url": "",
            "notification_file_extensions": "mp4,mkv,ts,iso,rmvb,avi,mov,mpeg,mpg,wmv,3gp,asf,m4v,flv,m2ts,tp,f4v",
        }

    def get_page(self) -> List[dict]:
        pass

    def get_module(self) -> Dict[str, Any]:
        """
        获取插件模块声明，用于胁持系统模块实现（方法名：方法实现）
        {
            "id1": self.xxx1,
            "id2": self.xxx2,
        }
        """
        return {
            "list_files": self.list_files,
            "any_files": self.any_files,
            "download_file": self.download_file,
            "upload_file": self.upload_file,
            "delete_file": self.delete_file,
            "rename_file": self.rename_file,
            "get_file_item": self.get_file_item,
            "get_parent_item": self.get_parent_item,
            "snapshot_storage": self.snapshot_storage,
            "storage_usage": self.storage_usage,
            "support_transtype": self.support_transtype,
            "create_folder": self.create_folder,
            "exists": self.exists,
            "get_item": self.get_item,
        }

    @eventmanager.register(ChainEventType.StorageOperSelection)
    def storage_oper_selection(self, event: Event):
        """
        监听存储选择事件，返回当前类为操作对象
        """
        if not self._enabled:
            return
        event_data: StorageOperSelectionEventData = event.event_data
        if event_data.storage == self._disk_name:
            # 处理云盘的操作
            event_data.storage_oper = self._p123_api

    def list_files(
        self, fileitem: schemas.FileItem, recursion: bool = False
    ) -> Optional[List[schemas.FileItem]]:
        """
        查询当前目录下所有目录和文件
        """

        if fileitem.storage != self._disk_name:
            return None

        def __get_files(_item: FileItem, _r: Optional[bool] = False):
            """
            递归处理
            """
            _items = self._p123_api.list(_item)
            if _items:
                if _r:
                    for t in _items:
                        if t.type == "dir":
                            __get_files(t, _r)
                        else:
                            result.append(t)
                else:
                    result.extend(_items)

        # 返回结果
        result = []
        __get_files(fileitem, recursion)

        return result

    def any_files(
        self, fileitem: schemas.FileItem, extensions: list = None
    ) -> Optional[bool]:
        """
        查询当前目录下是否存在指定扩展名任意文件
        """
        if fileitem.storage != self._disk_name:
            return None

        def __any_file(_item: FileItem):
            """
            递归处理
            """
            _items = self._p123_api.list(_item)
            if _items:
                if not extensions:
                    return True
                for t in _items:
                    if (
                        t.type == "file"
                        and t.extension
                        and f".{t.extension.lower()}" in extensions
                    ):
                        return True
                    elif t.type == "dir":
                        if __any_file(t):
                            return True
            return False

        # 返回结果
        return __any_file(fileitem)

    def create_folder(
        self, fileitem: schemas.FileItem, name: str
    ) -> Optional[schemas.FileItem]:
        """
        创建目录
        """
        if fileitem.storage != self._disk_name:
            return None

        return self._p123_api.create_folder(fileitem=fileitem, name=name)

    def download_file(
        self, fileitem: schemas.FileItem, path: Path = None
    ) -> Optional[Path]:
        """
        下载文件
        :param fileitem: 文件项
        :param path: 本地保存路径
        """
        if fileitem.storage != self._disk_name:
            return None

        return self._p123_api.download(fileitem, path)

    def upload_file(
        self, fileitem: schemas.FileItem, path: Path, new_name: Optional[str] = None
    ) -> Optional[schemas.FileItem]:
        """
        上传文件
        :param fileitem: 保存目录项
        :param path: 本地文件路径
        :param new_name: 新文件名
        """
        if fileitem.storage != self._disk_name:
            return None

        result = self._p123_api.upload(fileitem, path, new_name)
        
        # 如果上传成功且启用了远程STRM通知，则检查文件扩展名并发送通知
        if result and self._enable_strm_notification and self._strm_server_url:
            # 检查文件扩展名是否在配置的列表中
            if self._should_notify_file(result):
                self._notify_strm_server(result, path)
            
        return result

    def delete_file(self, fileitem: schemas.FileItem) -> Optional[bool]:
        """
        删除文件或目录
        """
        if fileitem.storage != self._disk_name:
            return None

        return self._p123_api.delete(fileitem)

    def rename_file(self, fileitem: schemas.FileItem, name: str) -> Optional[bool]:
        """
        重命名文件或目录
        """
        if fileitem.storage != self._disk_name:
            return None

        return self._p123_api.rename(fileitem, name)

    def exists(self, fileitem: schemas.FileItem) -> Optional[bool]:
        """
        判断文件或目录是否存在
        """
        if fileitem.storage != self._disk_name:
            return None

        return True if self.get_item(fileitem) else False

    def get_item(self, fileitem: schemas.FileItem) -> Optional[schemas.FileItem]:
        """
        查询目录或文件
        """
        if fileitem.storage != self._disk_name:
            return None

        return self.get_file_item(storage=fileitem.storage, path=Path(fileitem.path))

    def get_file_item(self, storage: str, path: Path) -> Optional[schemas.FileItem]:
        """
        根据路径获取文件项
        """
        if storage != self._disk_name:
            return None

        return self._p123_api.get_item(path)

    def get_parent_item(self, fileitem: schemas.FileItem) -> Optional[schemas.FileItem]:
        """
        获取上级目录项
        """
        if fileitem.storage != self._disk_name:
            return None

        return self._p123_api.get_parent(fileitem)

    def snapshot_storage(
        self,
        storage: str,
        path: Path,
        last_snapshot_time: float = None,
        max_depth: int = 5,
    ) -> Optional[Dict[str, Dict]]:
        """
        快照存储
        :param storage: 存储类型
        :param path: 路径
        :param last_snapshot_time: 上次快照时间，用于增量快照
        :param max_depth: 最大递归深度，避免过深遍历
        """
        if storage != self._disk_name:
            return None

        files_info = {}

        def __snapshot_file(_fileitm: schemas.FileItem, current_depth: int = 0):
            """
            递归获取文件信息
            """
            try:
                if _fileitm.type == "dir":
                    # 检查递归深度限制
                    if current_depth >= max_depth:
                        return

                    # 增量检查：如果目录修改时间早于上次快照，跳过
                    if (
                        self.snapshot_check_folder_modtime
                        and last_snapshot_time
                        and _fileitm.modify_time
                        and _fileitm.modify_time <= last_snapshot_time
                    ):
                        return

                    # 遍历子文件
                    sub_files = self._p123_api.list(_fileitm)
                    for sub_file in sub_files:
                        __snapshot_file(sub_file, current_depth + 1)
                else:
                    # 记录文件的完整信息用于比对
                    if getattr(_fileitm, "modify_time", 0) > last_snapshot_time:
                        files_info[_fileitm.path] = {
                            "size": _fileitm.size or 0,
                            "modify_time": getattr(_fileitm, "modify_time", 0),
                            "type": _fileitm.type,
                        }

            except Exception as e:
                logger.debug(f"Snapshot error for {_fileitm.path}: {e}")

        fileitem = self._p123_api.get_item(path)
        if not fileitem:
            return {}

        __snapshot_file(fileitem)

        return files_info

    def storage_usage(self, storage: str) -> Optional[schemas.StorageUsage]:
        """
        存储使用情况
        """
        if storage != self._disk_name:
            return None

        return self._p123_api.usage()

    def support_transtype(self, storage: str) -> Optional[dict]:
        """
        获取支持的整理方式
        """
        if storage != self._disk_name:
            return None

        return {"move": "移动", "copy": "复制"}

    def _should_notify_file(self, uploaded_file: schemas.FileItem) -> bool:
        """
        检查文件是否应该发送通知
        :param uploaded_file: 上传完成的文件信息
        :return: 是否应该发送通知
        """
        if not self._notification_file_extensions:
            # 如果没有配置扩展名，则默认发送所有文件的通知
            return True
        
        # 获取文件扩展名
        file_extension = uploaded_file.extension
        if not file_extension:
            return False
        
        # 将配置的扩展名转换为小写列表
        allowed_extensions = [ext.strip().lower() for ext in self._notification_file_extensions.split(",")]
        
        # 检查文件扩展名是否在允许列表中
        return file_extension.lower() in allowed_extensions

    def _notify_strm_server(self, uploaded_file: schemas.FileItem, local_path: Path):
        """
        通知远程STRM服务器文件上传完成
        :param uploaded_file: 上传完成的文件信息
        :param local_path: 本地文件路径
        """
        try:
            # 解析文件信息
            try:
                file_info = json.loads(uploaded_file.pickcode)
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"【远程STRM通知】解析文件信息失败: {e}, pickcode: {uploaded_file.pickcode}")
                return
            
            # 构建通知数据 - 使用新的简化API格式
            notification_data = {
                "file_name": uploaded_file.name,
                "pan_path": uploaded_file.path
            }
            
            # 发送HTTP通知 - 使用MoviePilot内置API密钥
            headers = {
                "Content-Type": "application/json"
            }
            
            # 使用MoviePilot内置的API_TOKEN作为apikey参数
            from app.core.config import settings
            url = f"{self._strm_server_url}/api/v1/plugin/P123StrmHelperRemote/notify/upload_complete?apikey={settings.API_TOKEN}"
            
            response = requests.post(
                url,
                json=notification_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"【远程STRM通知】文件 {uploaded_file.name} 上传完成通知发送成功")
            else:
                logger.error(f"【远程STRM通知】文件 {uploaded_file.name} 上传完成通知发送失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"【远程STRM通知】发送上传完成通知时发生错误: {e}")

    async def callback_strm_complete(self, request):
        """
        接收STRM生成完成回调通知
        """
        try:
            from fastapi import Request
            from fastapi.responses import JSONResponse
            
            # 解析请求数据
            data = await request.json()
            
            success = data.get("success", False)
            message = data.get("message", "")
            strm_path = data.get("strm_path", "")
            media_refresh = data.get("media_refresh", {})
            library_info = data.get("library_info", {})
            timestamp = data.get("timestamp", "")
            
            logger.info(f"【远程STRM回调】接收到STRM生成完成回调: {message}")
            
            # 处理入库完成通知
            if success and library_info:
                await self._handle_library_complete(library_info, media_refresh)
            
            return JSONResponse({
                "success": True,
                "message": "回调接收成功"
            })
            
        except Exception as e:
            logger.error(f"【远程STRM回调】处理回调通知时发生错误: {e}")
            return JSONResponse({
                "success": False,
                "message": f"处理回调失败: {e}"
            }, status_code=500)

    async def _handle_library_complete(self, library_info: dict, media_refresh: dict):
        """
        处理入库完成通知
        """
        try:
            title = library_info.get("title", "")
            year = library_info.get("year", "")
            media_type = library_info.get("type", "")
            category = library_info.get("category", "")
            file_name = library_info.get("file_name", "")
            strm_path = library_info.get("strm_path", "")
            pan_path = library_info.get("pan_path", "")
            
            logger.info(f"【入库完成通知】{title} 入库完成")
            
            # 发送MoviePilot内置通知
            await self._send_mp_notification(library_info, media_refresh)
            
        except Exception as e:
            logger.error(f"【入库完成通知】处理入库完成通知时发生错误: {e}")

    async def _send_mp_notification(self, library_info: dict, media_refresh: dict):
        """
        发送MoviePilot内置通知
        """
        try:
            
            title = library_info.get("title", "")
            year = library_info.get("year", "")
            media_type = library_info.get("type", "")
            category = library_info.get("category", "")
            file_name = library_info.get("file_name", "")
            strm_path = library_info.get("strm_path", "")
            pan_path = library_info.get("pan_path", "")
            
            # 媒体类型中文映射
            type_map = {
                "movie": "电影",
                "tv": "电视剧",
                "unknown": "未知"
            }
            
            media_type_cn = type_map.get(media_type, media_type)
            
            # 媒体服务器刷新状态
            refresh_status = "成功" if media_refresh.get("success", False) else "失败"
            refresh_message = media_refresh.get("message", "")
            
            # 构建通知消息
            message = f"""🎬 媒体入库完成通知

📺 标题: {title}
📅 年份: {year or "未知"}
🎭 类型: {media_type_cn}
📂 分类: {category}
📁 文件名: {file_name}

📋 处理状态:
• STRM生成: ✅ 成功
• 媒体服务器刷新: {refresh_status}
• 刷新详情: {refresh_message}

📂 文件路径:
• 网盘路径: {pan_path}
• STRM路径: {strm_path}

⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            # 发送MoviePilot内置通知事件
            event_data = {
                "title": f"媒体入库完成 - {title}",
                "message": message,
                "type": "success" if media_refresh.get("success", False) else "warning",
                "library_info": library_info,
                "media_refresh": media_refresh
            }
            
            # 触发通知事件
            event = Event(
                event_type=EventType.Notification,
                event_data=event_data
            )
            eventmanager.send_event(event)
            
            logger.info(f"【MoviePilot通知】入库完成通知已发送: {title}")
            
        except Exception as e:
            logger.error(f"【MoviePilot通知】发送通知时发生错误: {e}")

    def stop_service(self):
        """
        退出插件
        """
        pass
