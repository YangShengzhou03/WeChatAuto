"""WeChatAuto - 基于 Python 的 Windows 微信自动化工具。

对外只暴露 WeChat 类和版本号。典型用法：

    from wechatauto import WeChat

    wx = WeChat()
    result = wx.SendMsg("你好", "文件传输助手")
    print(result.is_success)

工作原理简述：
    本项目属于 GUI 自动化，不依赖微信内部接口，也不修改微信本体。
    它把微信当成一个普通的 Windows 桌面程序来"操作"：
      1. 用 uiautomation 通过 Windows UI Automation (UIA) 接口识别微信窗口
         和界面控件（按钮、输入框、会话列表等），通过 AutomationId / Name /
         ClassName 定位，这些标识来自微信客户端的控件树，微信版本更新可能变化；
      2. 用 pyautogui 模拟真实的鼠标点击和键盘输入完成发送；
      3. 用 pywin32 操作 Windows 剪贴板，实现多文件的批量传输。
    因此运行期间必须保持微信窗口在前台、不移动鼠标，否则模拟操作会被干扰。
"""

from .wechat import WeChat

__version__ = "0.1.0"

__all__ = [
    'WeChat',
    '__version__',
]
