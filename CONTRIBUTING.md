# 贡献指南

感谢你对 WeChatAuto 的关注！欢迎任何形式的贡献，包括报告问题、提交建议、完善文档和贡献代码。

## 行为准则

参与本项目即表示你同意：

- 尊重所有参与者和使用者，保持友善、专业的沟通
- 就事论事，对事不对人
- 不发布与项目无关的内容

## 如何贡献

### 报告问题（Issue）

提交问题前请先搜索已有 Issue，避免重复。提交时请包含：

- 操作系统版本、Python 版本、微信版本
- 复现步骤（尽量详细）
- 期望结果与实际结果
- 相关的报错信息或日志

### 提交代码（Pull Request）

1. Fork 本仓库，创建你的功能分支：

```bash
git checkout -b feature/your-feature
```

2. 完成开发后提交，Commit Message 使用以下格式：

```
类型: 简要描述

类型取值：
- feat: 新功能
- fix: 修复缺陷
- docs: 文档变更
- refactor: 重构
- test: 测试相关
- chore: 构建、依赖等杂项
```

3. 推送分支并发起 Pull Request，描述清楚改动内容和动机。

### 代码规范

- Python 代码遵循 [PEP 8](https://peps.python.org/pep-0008/)
- 缩进使用 4 个空格，不使用 Tab
- 新增功能需同步更新 README 中的使用说明和 API 参考
- 不引入与功能无关的依赖；确有需要时在 PR 中说明理由
- 注释、文档、Commit Message 一律使用中文

### 开发环境

- Windows 10/11、Python 3.11+
- 微信 Windows 版需已登录

```bash
git clone https://gitee.com/Yangshengzhou/WeChatAuto.git
cd WeChatAuto
pip install -r requirements.txt
pip install -e .
```

## 协作者说明

- 长期活跃并多次贡献高质量 PR 的开发者，可申请成为协作者（拥有直接推分支的权限）
- 协作者改动仍需走 Pull Request 流程，由其他协作者审核后合并
- 协作者需维护 `master` 分支的可发布状态，不直接推送破坏性改动

## 分支约定

- `master`：稳定分支，保持可用状态
- `feature/*`：功能开发分支
- `fix/*`：缺陷修复分支

## 许可证

提交的代码将遵循项目的 [MIT License](LICENSE)。提交即表示你同意按照该许可证授权你的贡献。
