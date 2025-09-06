from pathlib import Path
from typing import Any, List, Dict, Tuple, Optional
from threading import Thread

from p123client import P123Client
from app.core.event import eventmanager, Event
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType
from app.schemas import Notification, NotificationType
from p123client.tool import share_iterdir


class P123AutoClient:
    """
    123云盘自动重连客户端
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
                logger.info("123云盘Token失效，尝试重新登录...")
                self._client = P123Client(self._passport, self._password)
                attr = getattr(self._client, name)
                if not callable(attr):
                    return attr
                return attr(*args, **kwargs)
            return result
        return wrapped


class P123Share(_PluginBase):
    # 插件名称
    plugin_name = "123分享转存"
    # 插件描述
    plugin_desc = "通过消息或Web界面转存123云盘分享链接。"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/yuanjing-hash/MoviePilot-Plugins/main/icons/P123Disk.png"
    # 插件版本
    plugin_version = "0.2.1"
    # 插件作者
    plugin_author = "yuanjing"
    # 作者主页
    author_url = "https://github.com/yuanjing-hash"
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

    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled", False)
            self._passport = config.get("passport")
            self._password = config.get("password")
            self._transfer_save_path = config.get("transfer_save_path", "/")

            if self._enabled and self._passport and self._password:
                try:
                    self._client = P123AutoClient(self._passport, self._password)
                except Exception as e:
                    logger.error(f"123云盘客户端创建失败: {e}")
                    self._client = None
            else:
                self._client = None

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """
        定义远程控制命令
        """
        return []

    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """
        返回插件使用的前端渲染模式
        :return: 前端渲染模式，前端文件目录
        """
        return "vue", "dist/assets"

    def get_api(self) -> List[Dict[str, Any]]:
        """
        获取插件API
        """
        return [
            {
                "path": "/transfer",
                "endpoint": self.api_transfer,
                "methods": ["POST"],
                "summary": "转存分享链接",
                "description": "转存123云盘分享链接到指定目录",
            },
            {
                "path": "/browse_folders",
                "endpoint": self.api_browse_folders,
                "methods": ["GET"],
                "summary": "浏览网盘文件夹",
                "description": "获取网盘文件夹列表用于选择保存路径",
            },
            {
                "path": "/save_config",
                "endpoint": self.api_save_config,
                "methods": ["POST"],
                "summary": "保存插件配置",
                "description": "保存插件配置信息",
            },
            {
                "path": "/get_config",
                "endpoint": self.api_get_config,
                "methods": ["GET"],
                "summary": "获取插件配置",
                "description": "获取当前插件配置信息",
            },
            {
                "path": "/test_connection",
                "endpoint": self.api_test_connection,
                "methods": ["POST"],
                "summary": "测试123云盘连接",
                "description": "测试123云盘账号密码是否正确",
            }
        ]

    def get_page(self) -> List[dict]:
        """
        插件页面
        """
        return [
            {
                "component": "div",
                "text": "123分享转存",
                "props": {
                    "class": "text-h4 mb-4"
                }
            },
            {
                "component": "VCard",
                "props": {
                    "class": "mb-4"
                },
                "content": [
                    {
                        "component": "VCardTitle",
                        "text": "转存分享链接"
                    },
                    {
                        "component": "VCardText",
                        "content": [
                            {
                                "component": "VTextField",
                                "props": {
                                    "model": "shareLink",
                                    "label": "123云盘分享链接",
                                    "placeholder": "https://www.123684.com/s/xxxxx?提取码:1234 或 https://www.123684.com/s/xxxxx",
                                    "hint": "请输入123云盘的分享链接，支持带提取码的链接",
                                    "persistent-hint": True,
                                    "clearable": True
                                }
                            },
                            {
                                "component": "VTextField",
                                "props": {
                                    "model": "sharePassword",
                                    "label": "提取码（可选）",
                                    "placeholder": "1234",
                                    "hint": "如果分享链接需要提取码，请在此输入。如果链接中已包含提取码，可留空",
                                    "persistent-hint": True,
                                    "clearable": True
                                }
                            },
                            {
                                "component": "VTextField",
                                "props": {
                                    "model": "savePath",
                                    "label": "保存路径",
                                    "placeholder": "/我的资源/电影",
                                    "hint": "文件将保存到此网盘路径下，留空使用默认路径",
                                    "persistent-hint": True,
                                    "clearable": True
                                }
                            },
                            {
                                "component": "VAlert",
                                "props": {
                                    "type": "info",
                                    "variant": "tonal",
                                    "class": "mt-4"
                                },
                                "text": "请使用消息命令或API接口进行转存操作"
                            }
                        ]
                    }
                ]
            },
            {
                "component": "VCard",
                "props": {
                    "class": "mb-4"
                },
                "content": [
                    {
                        "component": "VCardTitle",
                        "text": "使用说明"
                    },
                    {
                        "component": "VCardText",
                        "content": [
                            {
                                "component": "div",
                                "text": "支持两种使用方式："
                            },
                            {
                                "component": "div",
                                "text": "1. 消息命令：发送 /123save <分享链接> [保存路径]"
                            },
                            {
                                "component": "div",
                                "text": "2. API接口：POST /api/v1/plugin/P123Share/transfer"
                            },
                            {
                                "component": "div",
                                "text": "支持的分享链接格式："
                            },
                            {
                                "component": "div",
                                "text": "• https://www.123684.com/s/xxxxx（无密码）"
                            },
                            {
                                "component": "div",
                                "text": "• https://www.123684.com/s/xxxxx?提取码:1234（带密码）"
                            },
                            {
                                "component": "div",
                                "text": "API使用示例："
                            },
                            {
                                "component": "VCard",
                                "props": {
                                    "variant": "outlined",
                                    "class": "mt-2 pa-3"
                                },
                                "content": [
                                    {
                                        "component": "pre",
                                        "props": {
                                            "style": "font-size: 12px; overflow-x: auto;"
                                        },
                                        "text": "curl -X POST /api/v1/plugin/P123Share/transfer \\\n  -H \"Content-Type: application/json\" \\\n  -d '{\n    \"shareLink\": \"https://www.123684.com/s/xxxxx?提取码:1234\",\n    \"sharePassword\": \"\",\n    \"savePath\": \"/我的资源/电影\"\n  }'"
                                    }
                                ]
                            },
                            {
                                "component": "div",
                                "text": "注意：使用前请先在插件设置中配置123云盘账号密码"
                            }
                        ]
                    }
                ]
            }
        ]

    def get_form(self) -> Tuple[Optional[List[dict]], Dict[str, Any]]:
        """
        为Vue组件模式返回初始配置数据。
        Vue模式下，第一个参数返回None，第二个参数返回初始配置数据。
        """
        return None, {
            "enabled": self._enabled,
            "passport": self._passport or "",
            "password": self._password or "",
            "transfer_save_path": self._transfer_save_path or "/",
        }

    def get_page(self) -> Optional[List[dict]]:
        """
        Vue模式不使用Vuetify页面定义
        """
        return None

    def get_legacy_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        传统模式的表单定义（保留作为备用）
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

    @eventmanager.register(EventType.UserMessage)
    def handle_message(self, event: Event):
        if not self._enabled or not self._client:
            return

        event_data = event.event_data or {}
        message = event_data.get("text", "").strip()
        channel = event_data.get("channel")
        userid = event_data.get("userid")

        if not message.startswith("/123save"):
            return

        parts = message.split()
        if len(parts) < 2:
            self.post_message(
                Notification(
                    channel=channel, userid=userid, mtype=NotificationType.Plugin,
                    title="命令错误", text="格式：/123save <分享链接> [保存路径]"
                )
            )
            return

        share_link = parts[1]
        save_path = parts[2] if len(parts) > 2 else self._transfer_save_path

        Thread(target=self.handle_transfer_task, args=(share_link, save_path, channel, userid)).start()

    def _parse_share_link(self, share_link: str, manual_password: str = "") -> tuple:
        """
        解析分享链接，提取ShareKey和SharePwd
        """
        import re
        
        # 尝试从链接中提取提取码
        extracted_password = ""
        
        # 匹配各种可能的提取码格式
        password_patterns = [
            r'提取码[：:]\s*([a-zA-Z0-9]+)',
            r'密码[：:]\s*([a-zA-Z0-9]+)',
            r'pwd[：:]\s*([a-zA-Z0-9]+)',
            r'password[：:]\s*([a-zA-Z0-9]+)',
        ]
        
        for pattern in password_patterns:
            match = re.search(pattern, share_link, re.IGNORECASE)
            if match:
                extracted_password = match.group(1)
                # 清理链接，移除提取码部分
                share_link = re.sub(r'[?&].*', '', share_link)
                break
        
        # 优先使用手动输入的密码，其次使用从链接提取的密码
        final_password = manual_password or extracted_password
        
        # 提取ShareKey（从URL中提取）
        share_key_match = re.search(r'/s/([a-zA-Z0-9]+)', share_link)
        if not share_key_match:
            raise Exception("无法从分享链接中提取ShareKey，请检查链接格式")
        
        share_key = share_key_match.group(1)
        
        return share_key, final_password

    async def api_transfer(self, request):
        """
        API接口：转存分享链接
        """
        try:
            from fastapi import Request
            from fastapi.responses import JSONResponse
            
            data = await request.json()
            share_link = data.get("shareLink", "").strip()
            share_password = data.get("sharePassword", "").strip()
            save_path = data.get("savePath", "").strip() or self._transfer_save_path
            
            if not share_link:
                return JSONResponse({
                    "success": False,
                    "message": "请输入分享链接"
                }, status_code=400)
            
            if not self._client:
                return JSONResponse({
                    "success": False,
                    "message": "123云盘客户端未初始化，请检查插件配置"
                }, status_code=400)
            
            # 在后台执行转存任务
            result = self.handle_transfer_task(share_link, save_path, share_password=share_password)
            
            return JSONResponse({
                "success": result.get("success", False),
                "message": result.get("message", "转存完成")
            })
            
        except Exception as e:
            logger.error(f"API转存失败: {e}", exc_info=True)
            return JSONResponse({
                "success": False,
                "message": f"转存失败: {str(e)}"
            }, status_code=500)

    async def api_browse_folders(self, request):
        """
        API接口：浏览网盘文件夹
        """
        try:
            from fastapi import Request
            from fastapi.responses import JSONResponse
            
            parent_id = request.query_params.get("parent_id", "0")
            
            if not self._client:
                return JSONResponse({
                    "success": False,
                    "message": "123云盘客户端未初始化"
                }, status_code=400)
            
            file_list = self._client.list(parent_file_id=int(parent_id))
            if not file_list or file_list.get("code") != 0:
                return JSONResponse({
                    "success": False,
                    "message": "获取文件夹列表失败"
                }, status_code=400)
            
            folders = []
            for item in file_list.get("data", []):
                if item.get("IsDir"):
                    folders.append({
                        "id": item.get("FileID"),
                        "name": item.get("FileName"),
                        "path": item.get("Path", "")
                    })
            
            return JSONResponse({
                "success": True,
                "data": folders
            })
            
        except Exception as e:
            logger.error(f"浏览文件夹失败: {e}", exc_info=True)
            return JSONResponse({
                "success": False,
                "message": f"浏览文件夹失败: {str(e)}"
            }, status_code=500)

    def _get_folder_id_by_path(self, path: str) -> int:
        if path == "/":
            return 0
        path_parts = [part for part in path.split("/") if part]
        
        current_id = 0
        for part in path_parts:
            file_list = self._client.list(parent_file_id=current_id) 
            if not file_list or file_list.get("code") != 0 or "data" not in file_list:
                raise Exception(f"无法获取目录 '{part}' 的内容，请检查路径或网盘连接")
            
            found = False
            for item in file_list["data"]:
                if item["FileName"] == part and item["IsDir"]:
                    current_id = item["FileID"]
                    found = True
                    break
            if not found:
                raise Exception(f"在路径中未找到文件夹 '{part}'")
        
        return current_id

    def handle_transfer_task(self, share_link: str, save_path: str, channel: str = None, userid: str = None, share_password: str = ""):
        def notify(title, text):
            if channel and userid:
                self.post_message(
                    Notification(
                        channel=channel, userid=userid, mtype=NotificationType.Plugin,
                        title=title, text=text
                    )
                )

        try:
            notify("任务开始", f"开始转存链接：{share_link}")

            if not self._client:
                raise Exception("123云盘客户端未初始化，请检查插件配置")

            # 解析分享链接
            share_key, share_pwd = self._parse_share_link(share_link, share_password)
            
            logger.info(f"解析分享链接成功: ShareKey={share_key}, 有密码={bool(share_pwd)}")

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

    async def api_save_config(self, request):
        """
        API接口：保存插件配置
        """
        try:
            from fastapi import Request
            from fastapi.responses import JSONResponse
            
            data = await request.json()
            
            # 更新配置
            self._enabled = data.get("enabled", False)
            self._passport = data.get("passport", "")
            self._password = data.get("password", "")
            self._transfer_save_path = data.get("transfer_save_path", "/")
            
            # 重新初始化客户端
            if self._passport and self._password:
                try:
                    self._client = P123AutoClient(self._passport, self._password)
                    logger.info("123云盘客户端重新初始化成功")
                except Exception as e:
                    logger.error(f"123云盘客户端初始化失败: {e}")
                    self._client = None
            else:
                self._client = None
            
            return JSONResponse({
                "code": 0,
                "msg": "配置保存成功"
            })
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}", exc_info=True)
            return JSONResponse({
                "code": 1,
                "msg": f"保存配置失败: {e}"
            }, status_code=500)

    async def api_get_config(self, request):
        """
        API接口：获取插件配置
        """
        try:
            return {
                "enabled": self._enabled,
                "passport": self._passport or "",
                "password": self._password or "",
                "transfer_save_path": self._transfer_save_path or "/",
            }
        except Exception as e:
            logger.error(f"获取配置失败: {e}", exc_info=True)
            return {"error": str(e)}

    async def api_test_connection(self, request):
        """
        API接口：测试123云盘连接
        """
        try:
            from fastapi import Request
            from fastapi.responses import JSONResponse
            
            data = await request.json()
            passport = data.get("passport", "")
            password = data.get("password", "")
            
            if not passport or not password:
                return JSONResponse({
                    "success": False,
                    "message": "请提供账号和密码"
                }, status_code=400)
            
            # 测试连接
            test_client = P123AutoClient(passport, password)
            
            # 尝试获取用户信息来验证登录
            user_info = test_client.user_info()
            
            if user_info and user_info.get("code") == 0:
                return JSONResponse({
                    "success": True,
                    "message": "连接测试成功",
                    "user_info": user_info.get("data", {})
                })
            else:
                return JSONResponse({
                    "success": False,
                    "message": "连接测试失败，请检查账号密码"
                })
                
        except Exception as e:
            logger.error(f"测试连接失败: {e}", exc_info=True)
            return JSONResponse({
                "success": False,
                "message": f"连接测试失败: {e}"
            }, status_code=500)

    def stop_service(self):
        """
        退出插件
        """
        pass
