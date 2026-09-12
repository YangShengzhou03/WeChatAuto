# WeChatAuto

<div align="center">

<img src="https://img.shields.io/badge/WeChatAuto-微信自动化工具-red?style=for-the-badge&labelColor=grey" alt="WeChatAuto"/>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE) [![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) [![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows) [![GitHub stars](https://img.shields.io/github/stars/YangShengzhou03/WeChatAuto?style=for-the-badge&logo=github)](https://github.com/YangShengzhou03/WeChatAuto/stargazers) [![GitHub issues](https://img.shields.io/github/issues/YangShengzhou03/WeChatAuto?style=for-the-badge&logo=github)](https://github.com/YangShengzhou03/WeChatAuto/issues) [![GitHub pull requests](https://img.shields.io/github/issues-pr/YangShengzhou03/WeChatAuto?style=for-the-badge&logo=github)](https://github.com/YangShengzhou03/WeChatAuto/pulls) [![Last Commit](https://img.shields.io/github/last-commit/YangShengzhou03/WeChatAuto?style=for-the-badge&logo=github)](https://github.com/YangShengzhou03/WeChatAuto/commits) [![Code Size](https://img.shields.io/github/languages/code-size/YangShengzhou03/WeChatAuto?style=for-the-badge&logo=github)](https://github.com/YangShengzhou03/WeChatAuto) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge)](CONTRIBUTING.md)

</div>

<div align="center">
<h3>让微信替你干活：批量发消息、传文件，一键搞定</h3>
</div>

基于 Python 的 Windows 微信自动化工具，通过 GUI 自动化技术模拟用户操作实现消息发送、文件传输等功能。

这个工具设计的初衷是为了简化微信的日常操作，特别是在需要批量发送消息或文件时，能够提高工作效率，减少重复劳动。它通过模拟真实用户的鼠标和键盘行为来驱动微信界面，不需要修改微信本身，也不依赖任何破解手段。只要微信窗口处于正常的登录状态，程序就能自动定位窗口、找到联系人并完成发送，整个过程与你亲手操作微信几乎没有区别。

借助这套机制，你可以让程序自动发送文本消息、传输文件、发送自定义表情，还可以在微信被最小化到系统托盘时自动唤醒窗口。无论是定时提醒、批量通知，还是日常的自动化脚本，它都能派上用场。

## 功能特性

WeChatAuto 的核心能力围绕"发消息"这件事展开。它支持向指定的联系人或群聊发送文本消息，也支持一次发送一个或多个文件，多个文件会通过剪贴板批量传输，不需要逐个手动拖拽。如果你收藏了自定义表情，还可以通过索引直接把表情发出去。

除了发送本身，窗口管理也是它的一部分。程序启动时会自动查找并激活微信窗口，如果微信被最小化到了系统托盘，它会尝试通过快捷键把微信唤醒，省去手动切窗口的麻烦。

## 项目结构

整个项目的结构非常简单。核心逻辑全部集中在 `wechatauto` 包里，其中 `wechat.py` 包含 WeChat 类的主要实现，`wxResponse.py` 定义了统一的响应对象。仓库根目录下的 `App.py` 是一个可以直接运行的示例脚本，`requirements.txt` 和 `pyproject.toml` 分别负责依赖声明和打包配置。

```
WeChatAuto/
├── wechatauto/               # 核心包
│   ├── __init__.py
│   ├── wechat.py
│   └── wxResponse.py
├── App.py                    # 示例应用
├── CONTRIBUTING.md           # 贡献指南
├── LICENSE                   # MIT 许可证
├── README.md
├── requirements.txt
├── pyproject.toml
└── wxautox-3.9.11.17.25b47-py3-none-any.whl
```

## 环境要求

由于项目依赖 Windows 的 UI 自动化接口，它只能在 Windows 系统上运行，推荐使用 Windows 10 或 Windows 11。Python 版本要求 3.11 及以上。使用前请先安装 Windows 版微信并登录账号，同时确保任务栏托盘中能看到微信图标，这是程序定位窗口的前提。

## 安装

推荐从源码安装，这样既能拿到最新代码，也方便你阅读和修改。只需要把仓库克隆到本地，装好依赖，再以可编辑模式安装即可。

```bash
git clone https://gitee.com/Yangshengzhou/WeChatAuto.git
cd WeChatAuto
pip install -r requirements.txt
pip install -e .
```

项目的运行依赖三个库，它们各司其职：`pyautogui` 负责模拟鼠标和键盘操作，`uiautomation` 负责 Windows 界面控件的识别与读取，`pywin32` 则用于调用 Windows 系统 API（例如操作剪贴板）。这些依赖在执行 `pip install -r requirements.txt` 时会一并安装。

## 快速上手

只需三步就能发出第一条消息。首先启动 Windows 版微信并完成登录，然后确认微信图标直接显示在任务栏托盘区域而不是被折叠隐藏，最后运行下面的代码。

```python
from wechatauto import WeChat

wx = WeChat()
result = wx.SendMsg("你好，世界", "文件传输助手")

if result.is_success:
    print("发送成功")
else:
    print(f"发送失败: {result['msg']}")
```

如果想偷懒，也可以直接运行仓库中的示例脚本 `python App.py`，它会向「文件传输助手」发送一条测试消息，不会打扰任何真实联系人，适合用来快速验证环境是否就绪。

## 使用方法

初始化时只需创建一个 WeChat 实例，程序会自动查找微信窗口。如果微信当时在系统托盘里，它会尝试通过 `Ctrl+Alt+W` 快捷键唤醒。实例上有两个常用属性：`activated` 表示窗口是否成功激活，`nickname` 是当前登录账号的昵称。

```python
from wechatauto import WeChat

wx = WeChat()
```

发送文本消息使用 `SendMsg` 方法，默认发送给「文件传输助手」。`who` 参数既可以填联系人昵称，也可以填群聊名称。当目标联系人不在当前会话列表时，程序会自动通过微信的搜索功能定位到对方再发送。

```python
result = wx.SendMsg("你好", "文件传输助手")

if result.is_success:
    print("发送成功")
else:
    print(f"发送失败: {result['msg']}")
```

发送文件使用 `SendFiles` 方法，传入一个路径字符串可以发送单个文件，传入路径列表则可以批量发送。多个文件会通过剪贴板一次性传输，因此发送过程中请保持微信窗口在前台，不要移动鼠标。

```python
# 发送单个文件
result = wx.SendFiles("C:/path/to/file.txt", "文件传输助手")

# 发送多个文件
result = wx.SendFiles(["C:/path/to/file1.txt", "C:/path/to/file2.pdf"], "文件传输助手")
```

发送表情使用 `SendEmotion` 方法，通过索引选择微信收藏的自定义表情，索引从 0 开始，0 就是收藏列表里的第一个表情。

```python
result = wx.SendEmotion(0, "文件传输助手")
```

## API 参考

WeChat 类提供三个发送方法。`SendMsg(msg, who)` 发送文本消息，`SendFiles(filepath, who)` 发送文件，其中 `filepath` 可以是字符串也可以是列表，`SendEmotion(emotion, who)` 发送自定义表情。三个方法的 `who` 参数默认值都是「文件传输助手」，返回值都是 WxResponse 对象。

WxResponse 是统一的响应对象，继承自 dict，用来描述每次操作的结果。它的 `is_success` 属性可以快速判断操作是否成功，`status` 字段取值为 "success"、"failure" 或 "error"，`msg` 携带结果说明，`data` 则存放附加数据。此外它还提供了 `success`、`failure`、`error` 三个类方法，方便你在扩展功能时构造相同格式的响应。

## 常见问题

如果程序提示找不到微信窗口，请先确认微信已经启动并登录，然后检查任务栏托盘区域。微信图标必须直接显示在托盘中，如果被折叠进了「隐藏的图标」弹出区域，程序将无法识别到窗口。此时可以把图标拖出到可见区域，或者通过 `Ctrl+Alt+W` 快捷键手动唤醒微信窗口后重试。

如果消息发送失败，建议先手动操作一次微信确认账号状态正常，然后检查 `who` 参数中的名称是否与微信界面上显示的完全一致，包括其中的表情符号和空格，任何一个字符的差异都可能导致定位失败。

由于程序是通过模拟鼠标键盘来操作微信界面的，发送过程中如果移动鼠标或切换窗口，会直接干扰自动化流程，导致消息发错位置或发送中断。请养成在发送期间保持窗口焦点不变的习惯。

## 注意事项

使用前请确保微信已经启动并登录。整个操作期间请勿手动干扰微信窗口，否则模拟的鼠标键盘动作会与你的真实操作互相冲突。部分操作可能需要管理员权限才能正常执行。另外需要说明的是，GUI 自动化本质上依赖微信界面的控件结构，因此微信版本更新导致界面变化时，可能出现控件识别失败的情况，这类问题通常需要等代码适配后才能解决。

## 关于作者

我是杨圣洲，江西吉安人，江西科技师范大学 2022 级信息管理与信息系统专业，2026 届毕业生，目前在杭州从事开发工作。

比起刷题和竞赛，我更喜欢动手做能落地的东西。日常被文件混乱、重复批量操作这类琐事困扰时，就自己写程序解决。独立开发的轻羽归档、轻羽大师等多款桌面工具已上架 Microsoft Store、联想应用商店，同时长期保持开源习惯。

我的开发理念比较务实：不追求炫技式的技术堆砌，优先做轻量化、稳定、能切实减轻负担的工具，好用够用是第一位。

- GitHub：[yangshengzhou03](https://github.com/yangshengzhou03)
- Gitee：[yang-shengzhou](https://gitee.com/Yangshengzhou/yang-shengzhou)

如果对这个项目有想法，欢迎提 Issue 留言，我都会认真看。

## Star 趋势

如果这个项目对你有帮助，欢迎点一个 Star，让更多人看到它。

[![Star History Chart](https://api.star-history.com/svg?repos=YangShengzhou03/WeChatAuto&type=Date)](https://star-history.com/#YangShengzhou03/WeChatAuto&Date)

## 参与贡献

欢迎提交 Issue 和 Pull Request！贡献流程、代码规范与协作者说明请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
