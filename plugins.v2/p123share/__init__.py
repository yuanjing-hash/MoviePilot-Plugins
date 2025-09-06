from pathlib import Path
from typing import Any, List, Dict, Tuple, Optional
from threading import Thread

from p123client import P123Client
from app.core.event import eventmanager, Event
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType
from app.chain.plugin import PluginChain
from app.schemas import Notification, NotificationType
from p123client.tool.util import share_extract_payload


class P123Share(_PluginBase):
    # 插件名称
    plugin_name = "123分享转存"
    # 插件描述
    plugin_desc = "通过消息或Web界面转存123云盘分享链接。"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/yuanjing-hash/MoviePilot-Plugins/main/icons/P123Disk.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "Gemini"
    # 作者主页
    author_url = "https://github.com/google/gemini"
    # 插件配置项ID前缀
    plugin_config_prefix = "p123share_"
    # 加载顺序
    plugin_order = 100
    # 可使用的用户级别
    auth_level = 1

    _enabled = False
    _client = None
    _passport = None
    _password = None
    _transfer_save_path = None

    def __init__(self):
        super().__init__()
        eventmanager.register(EventType.Messager, self.handle_message)

    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled", False)
            self._passport = config.get("passport")
            self._password = config.get("password")
            self._transfer_save_path = config.get("transfer_save_path", "/")

            if self._enabled and self._passport and self._password:
                try:
                    self._client = P123Client(self._passport, self._password)
                except Exception as e:
                    logger.error(f"123云盘客户端创建失败: {e}")
                    self._client = None
            else:
                self._client = None

    def get_state(self) -> bool:
        return self._enabled

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {"model": "enabled", "label": "启用插件"},
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {"model": "passport", "label": "手机号"},
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {"model": "password", "label": "密码", "type": "password"},
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
                                            "model": "transfer_save_path",
                                            "label": "转存默认保存路径",
                                            "placeholder": "/我的资源/电影",
                                            "hint": "消息或WebUI触发转存时的默认网盘保存路径",
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
            "transfer_save_path": "/",
        }

    def handle_message(self, event: Event):
        if not self._enabled or not self._client:
            return

        event_data = event.event_data or {}
        message = event_data.get("text", "").strip()
        channel = event_data.get("channel")
        userid = event_data.get("userid")

        if not message.startswith("/transfer"):
            return

        parts = message.split()
        if len(parts) < 2:
            PluginChain().post_message(
                Notification(
                    channel=channel, userid=userid, mtype=NotificationType.Plugin,
                    title="命令错误", text="格式：/transfer <分享链接> [保存路径]"
                )
            )
            return

        share_link = parts[1]
        save_path = parts[2] if len(parts) > 2 else self._transfer_save_path

        Thread(target=self.handle_transfer_task, args=(share_link, save_path, channel, userid)).start()

    def _get_folder_id_by_path(self, path: str) -> int:
        if path == "/":
            return 0
        path_parts = [part for part in path.split("/") if part]
        
        current_id = 0
        for part in path_parts:
            # Note: p123client file_list is deprecated, use list instead.
            # Assuming the API is similar.
            file_list = self._client.list(parent_file_id=current_id) 
            if not file_list or "data" not in file_list:
                raise Exception(f"无法获取目录 '{part}' 的内容")
            
            found = False
            for item in file_list["data"]:
                if item["FileName"] == part and item["IsDir"]:
                    current_id = item["FileID"]
                    found = True
                    break
            if not found:
                raise Exception(f"在路径中未找到文件夹 '{part}'")
        
        return current_id

    def handle_transfer_task(self, share_link: str, save_path: str, channel: str = None, userid: str = None):
        plugin_chain = PluginChain()
        def notify(title, text):
            if channel and userid:
                plugin_chain.post_message(
                    Notification(
                        channel=channel, userid=userid, mtype=NotificationType.Plugin,
                        title=title, text=text
                    )
                )

        try:
            notify("任务开始", f"开始转存链接：{share_link}")

            if not self._client:
                raise Exception("123云盘客户端未初始化，请检查插件配置")

            payload = share_extract_payload(share_link)
            share_key = payload.get("ShareKey")
            share_pwd = payload.get("SharePwd", "")

            if not share_key:
                raise Exception("无法从链接中解析出 ShareKey")

            file_ids = []  # Empty list to save all files from share
            parent_id = self._get_folder_id_by_path(save_path)

            result = self._client.share_save(
                share_key=share_key,
                share_pwd=share_pwd,
                file_ids=file_ids,
                parent_id=parent_id
            )

            if result and result.get("code") == 0:
                notify("转存成功", f"分享链接的内容已成功转存到 “{save_path}”")
                return {"success": True, "message": "转存成功"}
            else:
                error_message = result.get("message", "未知错误")
                raise Exception(error_message)

        except Exception as e:
            logger.error(f"123云盘转存失败: {e}", exc_info=True)
            notify("转存失败", f"错误信息：{e}")
            return {"success": False, "message": str(e)}

    def stop_service(self):
        eventmanager.unregister(EventType.Messager, self.handle_message)
        pass
