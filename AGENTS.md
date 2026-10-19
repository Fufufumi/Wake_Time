# AGENTS.md（指向工作区根）

本工程的完整 AI 代理规范在 **`../AGENTS.md`**（`E:/Projects_UE/AGENTS.md`）。动手前先完整读它。

要点：
- 本目录是 UE 5.8 工程根，也是唯一的 Git 仓库；分支、提交、LFS 都在这里
- C++ 模块 `Wake_Time`；玩法逻辑写 C++，蓝图禁止 Tick（见根文件 §7.1）
- AI 用行为树（见根文件 §9）
- `../StoryFramework` 是待迁移的框架工程，迁移任务见根文件 §5
