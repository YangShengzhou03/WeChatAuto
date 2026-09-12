"""WeChat 类：微信 GUI 自动化核心实现。

整体思路（接手前先读这一段）：

本类不调用微信内部接口，而是把微信当作普通 Windows 程序来操作，分为两层：

1. 窗口/控件层（uiautomation）
   微信 3.9+ 的主窗口类名是 mmui::MainWindow，内部控件树暴露了稳定的
   AutomationId，例如：
       session_list          左侧会话列表
       chat_input_field      聊天输入框
       head_image_v_view...  个人头像按钮（用于读取昵称）
   定位控件统一用 Exists() 判断是否存在，找不到时返回 None/False，
   由上层封装成 WxResponse.failure，而不是抛异常。

2. 操作层（pyautogui）
   控件定位到坐标后，用 pyautogui.click / hotkey / press 模拟真实操作。
   输入大段文本时不模拟逐字键入，而是通过控件自带的 ValuePattern
   直接写入值（相当于程序化赋值），速度快且不受输入法影响。

发送流程统一走 _send_to_contact：
   先判断当前会话是不是目标联系人（标题栏匹配，最快）
   -> 不是则在左侧会话列表里找并点击（次快）
   -> 还找不到就调用搜索框搜索定位（兜底）
   -> 都失败则返回失败响应。
找到会话后调用具体的发送函数（文本/文件/表情）完成发送。

风险提示：所有 AutomationId / Name 都来自特定微信版本（3.9.x），
微信更新界面后这些标识可能变化，届时需要重新用 inspect / Accessibility
Insights 等工具抓取控件树并更新对应常量。
"""

import os
import struct
import time
import ctypes
import re
from typing import Optional, Union
import pyautogui
import win32clipboard
import uiautomation as auto
from .wxResponse import WxResponse

# Windows API（user32）用于窗口前台化、还原最小化窗口等底层操作
user32 = ctypes.windll.user32

# 各类等待间隔（秒）。GUI 自动化必须留出界面响应时间：
# 点击搜索框后界面弹出需要时间、粘贴文件后聊天区生成缩略图需要时间。
# 数值过小会导致控件还没出现就去找，返回 Exists() 为 False。
DEFAULT_DELAY = 0.5   # 通用等待：会话切换、搜索结果弹出
SHORT_DELAY = 0.1     # 短等待：输入框点击、点击发送后的收尾
SEARCH_DELAY = 0.3    # 搜索相关等待：搜索结果列表刷新


class WeChat:
    """微信自动化操作类。

    使用方式：

        wx = WeChat()
        wx.SendMsg("你好", "文件传输助手")

    实例属性：
        activated: bool  微信窗口是否成功找到并激活
        nickname:  str   当前登录账号的昵称（可能为 None，见 _try_get_nickname）
        wechat_window: WindowControl  缓存的微信主窗口控件，避免重复查找
    """

    def __init__(self):
        self.activated = False
        self.wechat_window = None
        self.nickname = None

        # 第一步：找到微信主窗口；如果微信缩到系统托盘，尝试用快捷键唤醒
        wechat_window = self._init_wechat_window()

        # 第二步：尝试读取登录账号昵称（顺便触发一次界面交互，确认窗口可用）
        if wechat_window:
            self._try_get_nickname(wechat_window)

        if self.nickname:
            print(f"初始化成功，获取到已登录窗口：{self.nickname}")
            self.activated = True
        # 注意：即使 nickname 没拿到也不抛异常，发送功能仍可能可用，
        # 只是用 activated=False 提示调用方初始化不完整。

    # ------------------------------------------------------------------
    # 初始化与窗口管理
    # ------------------------------------------------------------------

    def _init_wechat_window(self) -> Optional[auto.WindowControl]:
        """初始化时定位微信主窗口。

        优先直接查找主窗口；找不到时检查微信是否缩在系统托盘，
        若在则模拟 Ctrl+Alt+W（微信的唤起快捷键）把它带回前台再找一次。
        """
        wechat_window = self.find_wechat_window()
        if wechat_window:
            return wechat_window

        if self.is_wechat_in_system_tray():
            pyautogui.hotkey('ctrl', 'alt', 'w')
            time.sleep(DEFAULT_DELAY)
            return self.find_wechat_window()

        return None

    def _try_get_nickname(self, wechat_window) -> None:
        """读取当前登录账号的昵称。

        原理：点击微信窗口左上角头像按钮会弹出个人资料卡片，
        卡片上的昵称控件可通过 get_nickname() 读取。
        读取后再次点击原位置关闭弹窗，界面恢复原状。

        用 BoundingRectangle 计算按钮中心坐标后用 pyautogui 点击，
        而不是调用控件自身的 Click()，是为了保证点击落在可见位置
        （控件 Click 在窗口未完全前台时可能失效）。
        """
        try:
            # 头像按钮位于窗口侧栏，定位失败不影响主流程
            wechat_button = wechat_window.ButtonControl(searchDepth=10, ClassName="mmui::XTabBarItem", Name="微信")
            if wechat_button.Exists():
                rect = wechat_button.BoundingRectangle
                if rect:
                    center_x = rect.left + (rect.width() // 2)
                    center_y = rect.top + (rect.height() // 2) - rect.height()
                    pyautogui.click(center_x, center_y)
                    self.nickname = self.get_nickname()
                    pyautogui.click(center_x, center_y)
        except Exception:
            pass

    def is_wechat_in_system_tray(self) -> bool:
        """判断微信是否最小化在系统托盘（任务栏通知区域）。

        原理：任务栏是类名为 Shell_TrayWnd 的系统窗口，
        通知区域图标可能在任务栏本体，也可能在"溢出窗口"的 ToolBar 里，
        所以两层都找一遍。注意：如果微信图标被折叠进"隐藏的图标"弹出区，
        该区域不展开时控件树中不可见，此时本方法返回 False（见 README 常见问题）。
        """
        try:
            taskbar = auto.PaneControl(Name="任务栏", ClassName="Shell_TrayWnd")
            if taskbar.Exists():
                wechat_button = taskbar.ButtonControl(searchDepth=5, Name="微信")
                if wechat_button.Exists():
                    return True
                # 溢出的通知图标存放在 ToolBar 容器中，逐个尝试
                toolbars = taskbar.FindAll(auto.ToolBarControl)
                for toolbar in toolbars:
                    try:
                        wechat_button = toolbar.ButtonControl(Name="微信")
                        if wechat_button.Exists():
                            return True
                    except Exception:
                        continue
        except Exception:
            pass
        return False

    def _bring_window_to_front(self, hwnd) -> None:
        """把指定窗口带到前台并激活。

        Windows 对 SetForegroundWindow 有安全限制（不允许后台进程随意抢焦点），
        所以失败时用 SetWindowPos 把窗口临时置顶（-1 = HWND_TOPMOST）再取消
        （-2 = HWND_NOTOPMOST），触发一次焦点切换。0x0001|0x0002 对应
        SWP_NOSIZE | SWP_NOMOVE，即只改层级不改位置大小。
        """
        if user32.IsIconic(hwnd):
            # 窗口处于最小化状态时先还原（9 = SW_RESTORE）
            user32.ShowWindow(hwnd, 9)
        user32.SetForegroundWindow(hwnd)
        user32.BringWindowToTop(hwnd)
        if not user32.SetForegroundWindow(hwnd):
            user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)
            time.sleep(SHORT_DELAY)
            user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002)

    def find_wechat_window(self) -> Optional[auto.WindowControl]:
        """查找并激活微信主窗口，成功则缓存复用。

        微信 3.9+ 主窗口类名为 mmui::MainWindow。
        已缓存时先通过 NativeWindowHandle 拿到句柄做前台化，
        避免重复走一遍耗时的控件树搜索（Exists(0) 表示不等待立刻返回）。
        """
        if self.wechat_window and self.wechat_window.Exists(0):
            hwnd = self.wechat_window.NativeWindowHandle
            self._bring_window_to_front(hwnd)
            return self.wechat_window
        try:
            window = auto.WindowControl(ClassName='mmui::MainWindow', searchDepth=1)
            if window.Exists(1):
                hwnd = window.NativeWindowHandle
                self._bring_window_to_front(hwnd)
                self.activated = True
                self.wechat_window = window
                return window
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # 昵称与联系人定位
    # ------------------------------------------------------------------

    def get_nickname(self) -> Optional[str]:
        """读取登录账号昵称，优先使用缓存。

        有两个来源，按可靠性排序：
        1. 主窗口侧栏的头像按钮控件，其 Name 就是昵称（AutomationId 对应
           个人资料视图的头像元素）；
        2. 个人资料弹窗 mmui::ProfileUniquePop 的第一个按钮（弹窗首行是昵称）。
        来源 1 点击头像后才存在，来源 2 在弹窗打开期间有效。
        """
        if self.nickname:
            return self.nickname

        if self.wechat_window:
            try:
                nickname_control = self.wechat_window.ButtonControl(AutomationId="head_image_v_view.head_view_")
                if nickname_control.Exists(1):
                    name = nickname_control.Name
                    if name:
                        self.nickname = name
                        return self.nickname
            except Exception:
                pass

        try:
            profile_window = auto.WindowControl(ClassName="mmui::ProfileUniquePop")
            if profile_window.Exists(1):
                nickname_button = profile_window.ButtonControl()
                if nickname_button.Exists(1):
                    name = nickname_button.Name
                    if name:
                        self.nickname = name
                        return self.nickname
        except Exception:
            pass

        return None

    def _get_current_chat_title(self, wechat_window) -> Optional[str]:
        """读取当前打开会话的标题（联系人名或群名）。

        标题控件是聊天区顶部的长 AutomationId，直接指到具体元素。
        群聊标题可能带未读/在线人数后缀如 "某某群 (23)"，
        用正则去掉末尾括号数字再比对，避免误判为不同联系人。
        """
        try:
            title_control = wechat_window.TextControl(
                AutomationId="content_view.top_content_view.title_h_view.left_v_view.left_content_v_view.left_ui_.big_title_line_h_view",
            )
            if title_control.Exists():
                title = title_control.Name
                title = re.sub(r'\(\d+\)$', '', title)
                return title.strip()
        except Exception:
            pass
        return None

    def _get_session_item_by_name(self, wechat_window, who: str):
        """在左侧会话列表中找到名称匹配的会话项。

        会话列表控件 AutomationId 固定为 session_list。
        每个子项的 Name 是多行文本（第一行是会话名，后面是最新消息摘要），
        所以取 Name.split('\n')[0] 后再比对。
        """
        try:
            session_list = wechat_window.ListControl(AutomationId="session_list")
            if not session_list.Exists():
                return None
            session_items = session_list.GetChildren()
            for item in session_items:
                item_name = item.Name.split('\n')[0].strip() if item.Name else ""
                if who == item_name:
                    return item
            return None
        except Exception:
            return None

    def _find_and_click_in_session_list(self, wechat_window, who: str) -> bool:
        """在会话列表中找到目标会话并点击打开。"""
        item = self._get_session_item_by_name(wechat_window, who)
        if item:
            item.Click()
            return True
        return False

    def _search_and_open_contact(self, wechat_window, who: str) -> bool:
        """通过搜索框定位联系人（会话列表里找不到时的兜底方案）。

        流程：
        1. 点击主窗口搜索框（EditControl Name="搜索"）；
        2. 用 ValuePattern 直接写入关键词（SetValue 相当于程序化输入，
           比逐字键入快且不受输入法干扰）；
        3. 等待搜索结果弹窗 mmui::SearchContentPopover 出现；
        4. 弹窗内是分组列表：组头（"联系人"/"群聊"等）和条目交替出现。
           逐个遍历，记录当前所处的分组，只有当条目出现在有效分组
           （联系人/群聊/功能/最常使用）且名称完全匹配时才点击；
           跳过"搜索网络结果"分组，避免点到网页结果。
        5. 未找到时按 Esc 收起搜索弹窗并返回 False。
        """
        try:
            search_edit = wechat_window.EditControl(Name="搜索")
            if not search_edit.Exists():
                return False
            search_edit.Click()
            time.sleep(0.1)
            value_pattern = search_edit.GetValuePattern()
            value_pattern.SetValue(who)
            time.sleep(0.5)
            search_popup = wechat_window.WindowControl(ClassName="mmui::SearchContentPopover")
            if not search_popup.Exists():
                return False
            table_view = search_popup.Control(ClassName="mmui::XTableView")
            if not table_view.Exists():
                return False

            cells = table_view.GetChildren()
            if not cells:
                return False

            valid_groups = {"联系人", "群聊", "功能", "最常使用"}
            skip_groups = {"搜索网络结果"}
            current_group = None

            for cell in cells:
                cell_name = cell.Name or ""
                if not cell_name.strip():
                    continue

                # 组头节点用于切换当前分组上下文
                if cell_name in valid_groups or cell_name in skip_groups:
                    current_group = cell_name
                    continue

                if current_group in skip_groups:
                    continue

                if current_group in valid_groups and cell_name == who:
                    cell.Click()
                    time.sleep(0.3)
                    return True

            # 没有匹配项，按 Esc 收起搜索弹窗，避免残留状态影响下一次操作
            pyautogui.press('esc')
            return False
        except Exception:
            return False

    # ------------------------------------------------------------------
    # 内容发送（前置条件：目标会话已打开）
    # ------------------------------------------------------------------

    def _send_message_content(self, msg: str) -> bool:
        """向当前打开的会话发送文本消息。

        1. 定位聊天输入框（AutomationId=chat_input_field），
           用 ValuePattern 直接写入内容；
        2. 优先点击"发送"按钮（mmui::XOutlineButton 类），
           按钮不存在（如某些场景按钮隐藏）时退回按回车发送。
        """
        try:
            wechat_window = self.find_wechat_window()
            if not wechat_window:
                return False
            chat_input = wechat_window.EditControl(AutomationId="chat_input_field")
            if not chat_input.Exists():
                return False
            value_pattern = chat_input.GetValuePattern()
            value_pattern.SetValue(msg)
            send_button = wechat_window.ButtonControl(Name="发送", ClassName="mmui::XOutlineButton")
            if send_button.Exists() and send_button.IsEnabled:
                send_button.Click()
            else:
                pyautogui.press('enter')
            time.sleep(SHORT_DELAY)
            return True
        except Exception:
            return False

    def _send_file_content(self, filepaths: list) -> bool:
        """向当前打开的会话发送一个或多个文件。

        原理：先把文件路径列表写入剪贴板（CF_HDROP 格式，
        与资源管理器"复制文件"格式一致），再在聊天输入框模拟 Ctrl+V，
        微信会自动识别剪贴板中的文件并生成待发送条目，最后点击发送。
        这也是手动批量发文件时微信的原生路径，所以多文件可以一次全部发出。
        """
        try:
            self._set_clipboard_files(filepaths)
            wechat_window = self.find_wechat_window()
            if not wechat_window:
                return False
            chat_input = wechat_window.EditControl(AutomationId="chat_input_field")
            if not chat_input.Exists():
                return False
            # 先点一下输入框确保焦点在聊天窗口，否则 Ctrl+V 会粘到别处
            chat_input.Click()
            time.sleep(SHORT_DELAY)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(DEFAULT_DELAY)
            send_button = wechat_window.ButtonControl(Name="发送", ClassName="mmui::XOutlineButton")
            if send_button.Exists() and send_button.IsEnabled:
                send_button.Click()
            else:
                pyautogui.press('enter')
            time.sleep(SHORT_DELAY)
            return True
        except Exception:
            return False

    def _set_clipboard_files(self, filepaths: list) -> None:
        """把文件路径列表以 CF_HDROP 格式写入剪贴板。

        数据结构（微软文档 DROPFILES）：
        - 20 字节头：结构体大小(20) + 三个占位 0 + fWide=1（1 表示宽字符）；
        - 数据体：每个绝对路径以 \0 结尾，多个路径连续排列，
          末尾再加一个 \0 表示列表结束（共两个 \0 收尾）；
        - 路径中的 / 统一替换为 Windows 风格的 \，并按 UTF-16LE 编码。

        OpenClipboard 成功后用 try/finally 保证 CloseClipboard 一定执行，
        否则剪贴板被本进程占用，其他程序将无法打开剪贴板。
        """
        win32clipboard.OpenClipboard()
        try:
            files = "\0".join(filepaths).replace("/", "\\") + "\0\0"
            dropfiles_data = files.encode('utf-16le')
            dropfiles_header = struct.pack("<lllll", 20, 0, 0, 0, 1)
            dropfiles = dropfiles_header + dropfiles_data
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_HDROP, dropfiles)
        finally:
            win32clipboard.CloseClipboard()

    def _send_emotion_content(self, emotion: int) -> bool:
        """向当前打开的会话发送收藏的自定义表情。

        流程：
        1. 点击聊天工具栏的表情按钮（Name 固定为"发送表情(Alt+E)"）；
        2. 等待表情弹窗 mmui::XPopover（AutomationId=EmoticonPopover）出现；
        3. 点击"自定义表情"分类页签；
        4. 表格视图 mmui::EmoticonGridView 的子项按收藏顺序排列，
           直接用索引取对应表情并点击，点击后微信会立即发送并关闭弹窗。
        """
        if emotion < 0:
            return False
        try:
            wechat_window = self.find_wechat_window()
            if not wechat_window:
                return False

            emotion_button = wechat_window.ButtonControl(searchDepth=15, Name="发送表情(Alt+E)")
            if not emotion_button.Exists(1):
                return False

            emotion_button.Click()
            time.sleep(DEFAULT_DELAY)

            emotion_window = auto.WindowControl(
                searchDepth=1,
                ClassName="mmui::XPopover",
                AutomationId="EmoticonPopover",
                Name="Weixin"
            )
            if not emotion_window.Exists(1):
                return False

            category_tab = emotion_window.TabItemControl(searchDepth=5, Name="自定义表情")
            if category_tab.Exists(1):
                category_tab.Click()
                time.sleep(DEFAULT_DELAY)

            emotion_items = emotion_window.ListControl(searchDepth=5, ClassName="mmui::EmoticonGridView").GetChildren()
            if not emotion_items or emotion >= len(emotion_items):
                return False

            emotion_items[emotion].Click()
            time.sleep(SEARCH_DELAY)

            return True

        except Exception:
            return False

    # ------------------------------------------------------------------
    # 对外入口：统一定位联系人再发送
    # ------------------------------------------------------------------

    def _ensure_wechat_window(self) -> Optional[auto.WindowControl]:
        """发送前确保微信窗口可用，必要时从托盘唤醒。"""
        wechat_window = self.find_wechat_window()
        if not wechat_window:
            if self.is_wechat_in_system_tray():
                pyautogui.hotkey('ctrl', 'alt', 'w')
                time.sleep(DEFAULT_DELAY)
                wechat_window = self.find_wechat_window()
        return wechat_window

    def _send_to_contact(self, who: str, send_func, success_msg: str, fail_msg: str, delay: float = DEFAULT_DELAY):
        """定位目标会话并执行发送，所有对外方法的公共流程。

        会话定位按开销从小到大三级递进：
        1. 当前会话标题栏已经等于 who —— 直接发，零切换成本；
        2. 左侧会话列表里有 who —— 点击切换后发送；
        3. 都没有 —— 走搜索框搜索定位后发送。

        参数说明：
            who:        目标联系人/群聊名称（需与界面显示完全一致）
            send_func:  实际执行发送的函数（返回 bool），由各对外方法传入
            success_msg/fail_msg: 发送成功/失败时写入响应的 msg
            delay:      切换会话后的等待时间（界面渲染需要时间）
        """
        wechat_window = self._ensure_wechat_window()
        if not wechat_window:
            return WxResponse.failure("未找到微信窗口")

        def try_send():
            if send_func():
                return WxResponse.success(success_msg)
            return WxResponse.failure(fail_msg)

        # 第一级：当前会话就是目标，无需切换
        current_chat_title = self._get_current_chat_title(wechat_window)
        if current_chat_title and who == current_chat_title:
            return try_send()

        # 第二级：会话列表中直接可见，点击切换
        if self._find_and_click_in_session_list(wechat_window, who):
            time.sleep(delay)
            return try_send()

        # 第三级：走搜索框兜底定位
        if self._search_and_open_contact(wechat_window, who):
            time.sleep(delay)
            return try_send()

        return WxResponse.failure(f"发送对象<{who}>不存在，发送失败")

    def SendMsg(self, msg: str, who: str = "文件传输助手") -> WxResponse:
        """发送文本消息。

        参数：
            msg: 消息文本
            who: 目标联系人或群聊名称，默认"文件传输助手"
        返回：WxResponse，is_success 判断是否成功。
        """
        try:
            return self._send_to_contact(
                who,
                lambda: self._send_message_content(msg),
                "发送成功",
                "发送消息失败"
            )
        except Exception as e:
            return WxResponse.failure(f"发送消息异常：{str(e)}")

    def SendFiles(self, filepath: Union[str, list], who: str = "文件传输助手") -> WxResponse:
        """发送文件，支持单个路径字符串或路径列表批量发送。

        多个文件通过剪贴板一次性传输（见 _send_file_content）。
        发送前逐个校验路径是否存在，任一文件缺失则整批拒绝发送，
        避免出现"发了一半"的尴尬状态。
        """
        try:
            if isinstance(filepath, str):
                filepaths = [filepath]
            elif isinstance(filepath, list):
                filepaths = filepath
            else:
                return WxResponse.failure("文件路径参数类型错误，应为字符串或列表")

            for fp in filepaths:
                if not os.path.exists(fp):
                    return WxResponse.failure(f"未找到文件：{fp}，无法成功发送")

            return self._send_to_contact(
                who,
                lambda: self._send_file_content(filepaths),
                "文件发送成功",
                "文件发送失败"
            )
        except Exception as e:
            return WxResponse.failure(f"发送文件异常：{str(e)}")

    def SendEmotion(self, emotion: int, who: str = "文件传输助手") -> WxResponse:
        """发送收藏的自定义表情。

        参数：
            emotion: 表情在收藏列表中的索引，从 0 开始
            who:     目标联系人或群聊名称
        切换会话后界面刷新较慢，这里使用更长的 delay（0.8 秒）。
        """
        try:
            return self._send_to_contact(
                who,
                lambda: self._send_emotion_content(emotion),
                "表情发送成功",
                f"未找到表情索引：{emotion}",
                delay=0.8
            )
        except Exception as e:
            return WxResponse.failure(f"发送表情异常：{str(e)}")