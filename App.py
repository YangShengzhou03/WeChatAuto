from wechatauto import WeChat

wx = WeChat()

# 1. 发送文本消息
print(wx.SendMsg('测试消息', '文件传输助手'))

# 2. 发送单个文件
# print(wx.SendFiles(r'C:\path\to\file.txt', '文件传输助手'))

# 3. 批量发送多个文件（通过剪贴板一次性传输）
# print(wx.SendFiles([r'C:\path\to\file1.txt', r'C:\path\to\file2.pdf'], '文件传输助手'))

# 4. 发送收藏的自定义表情（索引从 0 开始）
# print(wx.SendEmotion(0, '文件传输助手'))
