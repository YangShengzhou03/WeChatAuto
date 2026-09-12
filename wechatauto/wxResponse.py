"""统一响应对象模块。

所有对外方法（SendMsg / SendFiles / SendEmotion）都不直接抛出业务异常，
而是返回一个 WxResponse 对象。这样做的好处是：

1. 调用方不需要写 try/except 就能拿到结果：
       result = wx.SendMsg("你好", "文件传输助手")
       if result.is_success: ...
2. 结果是 dict 的子类，可以直接序列化成 JSON，也可以用 result['msg'] 取值，
   便于接入日志系统或上层框架。
3. status 字段统一取值，避免各处用不同的错误表示方式：
   - "success" 操作成功
   - "failure" 业务失败（例如找不到联系人、文件不存在，属于正常可预期的失败）
   - "error"   系统级错误（例如接口调用异常，一般来自未预期的异常场景）
"""


class WxResponse(dict):
    """描述一次自动化操作的结果。

    继承自 dict，内部固定保存三个键：
        status: str  结果状态，取值 "success" / "failure" / "error"
        msg:    str  结果说明，可直接展示给用户或写入日志
        data:   dict 附加数据，预留扩展位（例如发送文件时带回耗时等）
    """

    def __init__(self, status: str, msg: str, data: dict = None):
        # data 允许传 None，统一兜底为空 dict，保证下游取值不需要判空
        super().__init__(status=status, msg=msg, data=data or {})

    def __str__(self):
        return str(dict(self))

    __repr__ = __str__

    @property
    def is_success(self):
        """快捷判断：本次操作是否成功。"""
        return self['status'] == 'success'

    def __bool__(self):
        # 让 WxResponse 可以直接用于 if 判断：
        #   if wx.SendMsg(...): 等价于 is_success 为 True
        # 注意：这也意味着 if result == False 这种判断要改用 is_success，
        # 因为任何非空 dict 的布尔值都是 True，这里通过 __bool__ 重载修正语义。
        return self.is_success

    @classmethod
    def success(cls, msg=None, data: dict = None):
        """构造成功响应。"""
        return cls(status="success", msg=msg, data=data)

    @classmethod
    def failure(cls, msg: str, data: dict = None):
        """构造业务失败响应（可预期的失败，例如联系人不存在）。"""
        return cls(status="failure", msg=msg, data=data)

    @classmethod
    def error(cls, msg: str, data: dict = None):
        """构造系统错误响应（未预期的异常场景）。"""
        return cls(status="error", msg=msg, data=data)
