# AGENTS.md — Wake Time（UE5 第三人称潜行游戏）

本文件是**本工程**（`Wake_Time/`）内一切 AI 代理的行为规范，适用于上传美术素材、编辑关卡、编写玩法程序的各类代理。开始任何任务前先完整读本文件。

- 工作区根 ≠ 本文件所在目录时，以本文件为准（工程级比工作区级更具体）。
- **任何情况下，用户的直接指令优先于本文件**（见 §0）。

---

## 0. 用户手动介入优先（最高优先级）

**用户在任何时候的手动操作，优先级高于本文件的一切条款。**

- 「手动介入」包括但不限于：在编辑器里改资产、直接编辑文件、口头纠正、临时决定、推翻前面已经给出的指示。
- AI **不得**以本文件的任何条款为由，撤销、覆盖、还原、重置或忽略用户**已经做出**的改动。
- 发现用户的改动与本文件规范冲突时，正确顺序是：**保留用户改动 → 在汇报里指出冲突与影响 → 等用户指示**。不得自行回滚。
- 因「规范要求」需要还原、丢弃或重写用户改动时，**必须先问**；问之前不得动手。
- 判断「这是用户改的还是编辑器自动改的」有疑问时，按用户改动处理。
- 本条优先于本文件其他所有条款；两者冲突时，以用户为准。

> 历史教训：曾有代理以「迁移不得修改框架资产」为由，用源文件覆盖了用户在编辑器里的手动修复，且未备份，导致改动永久丢失。不要重演。

---

## 1. 工程事实（不要猜，用这些）

| 项 | 事实 |
| --- | --- |
| 引擎 | UE `5.8`（`Wake_Time.uproject` 的 `EngineAssociation`） |
| 本目录 | 工程根，**同时是 Git 仓库根**（分支、提交、LFS 都在这里） |
| C++ 模块 | 单一运行时模块 `Wake_Time`（`Source/Wake_Time/Wake_Time.Build.cs`） |
| 版本控制 | Git + Git LFS（`Content/**` 已纳入 LFS） |
| 渲染 | Lumen + Virtual Shadow Maps + Substrate + Ray Tracing，DX12 / SM6 |

**已启用插件**：`StateTree`、`GameplayStateTree`、`ModelContextProtocol`、`MCPClientToolset`、`AllToolsets`、`ModelingToolsEditorMode`(Editor)

**已链接模块**：`Core`、`CoreUObject`、`Engine`、`InputCore`、`EnhancedInput`、`AIModule`、`StateTreeModule`、`GameplayStateTreeModule`、`UMG`、`Slate`
- 行为树所需类都在 `AIModule` 内，**不需要新增模块**
- 只有确实需要时才在 `Build.cs` 加依赖：`NavigationSystem`、`GameplayTags`、`Niagara`、`AudioMixer`、`DeveloperSettings`

**地图与 GameMode**
- 默认地图：`/Game/Dorm/Maps/Lvl_Dorm`
- 编辑器启动地图：`/Game/Dorm/Maps/Lvl_Dorm_Overview`
- 默认 GameMode：`/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode`（C++ 侧 `AWake_TimeGameMode`）

**迁移重定向**：`TP_ThirdPerson*` → `Wake_Time*` 已存在，**不要新增或删除 redirect**。

**编辑器内 MCP 服务**：`http://127.0.0.1:8000/mcp`（`.mcp.json` / `.codex/config.toml` / `.cursor/mcp.json`），可在编辑器里查资产、看层级、跑 PIE、改蓝图。**能用它验证就不要靠猜。**

**现有 C++ 骨架**
```
Source/Wake_Time/
  Wake_TimeCharacter.{h,cpp}     // ACharacter + SpringArm + FollowCamera + EnhancedInput
  Wake_TimeGameMode.{h,cpp}
  Wake_TimePlayerController.{h,cpp}
  Variant_Combat/  Variant_Platforming/  Variant_SideScrolling/  AI/   // 模板参考，勿当产品代码
```
`AWake_TimeCharacter` 是 `UCLASS(abstract)`，具体角色走蓝图子类。扩展时**加组件、加接口**，不要复制新角色类。

---

## 2. 铁律（违反即回滚）

1. **不改已有资产的引用路径。** 不移动、不重命名、不删除任何已被场景或蓝图引用的 `.uasset` / `.umap`。发现命名不规范的旧资产**不要顺手修**，报告给用户。
2. **二进制资产只能通过编辑器或 unreal-mcp 修改。** 禁止用脚本、十六进制编辑器或任何二进制手段改 `.uasset` / `.umap`。
3. **不删除**任何文件、资产、配置项、日志分类；不执行 `git push --force`、不 rebase 别人的提交。
4. **不提交大二进制。** 克隆后先 `git lfs pull`；不要新增未经批准的模型/贴图/音频大文件。
5. **不碰引擎源码，不改 `.uproject` 的插件列表**（除非任务明确要求，且要在汇报里单独说明）。
6. **不改已有的迁移接线。** `Config/DefaultEngine.ini` 里的 `GameInstanceClass`、`SFInteraction` 碰撞通道与重定向、`UserInterfaceSettings` 已配好，改了会让交互/菜单/存档**静默失效**。
7. **不动 `Content/StoryFramework`。** 那是已迁移的框架快照，只读复用地使用，不改其内部逻辑、变量、默认值（要改先问用户）。
8. **不动 `Content/Dorm` 的导入资产。** 其规范见 `Docs/Dorm/README.md`；那是导入的美术资源，改名/移动会断链。
9. **蓝图里禁止 Tick。** 见 §7.1。需要高频逻辑就去 C++ 写基类，再派生蓝图子类。
10. **玩法逻辑写 C++，不写蓝图。** 蓝图只用于表现、连线、参数调优。见 §7。
11. **不新建第二套系统。** 角色、AI、感知、交互、存档、对话、UI 骨架都已存在或由框架提供。先找现有的，再谈新增。
12. **没编译通过、没跑过验证的改动，不算完成。** 见 §10。

---

## 3. 素材上传（美术代理重点）

### 3.1 放哪里

| 用途 | 路径 |
| --- | --- |
| 跨关卡复用的模型/材质/贴图 | `Content/assets/<类别>/` |
| 仅本关可用 | 该关卡目录（参考 `Content/Variant_Combat`） |
| 玩法相关（潜行） | `Content/Stealth/...` 或 `Content/Dorm/...` 对应子目录 |
| 导入的 Dorm 美术资源 | 已在 `Content/Dorm/`，**不要改动** |

不要新建与现有目录平行的"第二套资源根"。先看 `Content/` 顶层，跟着现有结构走。

### 3.2 命名（Epic 官方前缀，必须遵守）

`BP_` 蓝图 · `WBP_` 控件 · `CH_` 角色 · `SM_` 静态网格 · `SK_` 骨骼网格 · `M_` 材质 · `MI_` 材质实例 · `T_` 贴图 · `IA_` 输入动作 · `IMC_` 输入映射 · `DT_` 数据表 · `DA_` 数据资产 · `BT_` 行为树 · `BB_` 黑板 · `Lvl_` 关卡 · `A_`/`S_` 音频

### 3.3 导入流程

1. **先 `git lfs pull`**，确认工作区完整；否则你可能在残缺资源上操作。
2. 用编辑器 Import 导入，**不要**把文件直接丢进 `Content/` 再期待 UE 识别（用 File → Import，或拖入 Content Browser）。
3. 导入后立刻检查：材质是否报错、贴图是否丢、LOD/碰撞是否合理、Static Mesh 是否能正常显示。
4. **不要覆盖同名已有资产**——引用它的关卡和蓝图会一起被改。同名就换名字。
5. 单个文件 > 500 MB 或素材总量较大时，**先问**；不要自行决定提交。
6. 素材来源与授权由用户负责确认；不要自行从网络抓取资源塞进工程。

### 3.4 渲染相关（不要动）

Lumen、Virtual Shadow Maps、Substrate、Ray Tracing、DX12/SM6 是刻意开启的。**不要为了"性能"关闭或降级它们**；性能问题报告给用户，由用户决定。

### 3.5 美术不归代理管的判断

以下需要**先提问**，不要自作主张：美术风格、材质观感取舍、镜头语言、叙事文本定稿、动画曲线/状态机调参。

---

## 4. 关卡编辑（关卡代理重点）

1. **不要改默认地图/启动地图配置。** `GameDefaultMap`、`EditorStartupMap`、`GlobalDefaultGameMode` 已定，改动会影响所有人。需要新地图就新建。
2. **新关卡命名 `Lvl_<用途>`**，放到对应目录（宿舍相关放 `Content/Dorm/Maps/`）。
3. **不要删除 Outliner 里不属于你的 Actor。** 别人的布置可能是进行中的工作。
4. **不要重命名已存在的 `.umap`**（`GameDefaultMap` / `EditorStartupMap` 按路径引用）。
5. **World Settings 里不要改 GameMode 覆盖**，除非任务明确要求。
6. 有 World Partition / 外部 Actor（`__ExternalActors__`、`__ExternalObjects__`）时，**不要手动编辑这两个目录**，让编辑器管理。
7. **保存前自检**：Outliner 有没有误拖入的临时 Actor、有没有 Missing 引用（Content Browser 搜索 `Missing`）、灯光是否被意外清空。
8. **改动后必须说明验证方式**：在编辑器里打开到什么程度、PIE 看到什么、日志有无 Warning/Error。

---

## 5. 框架层使用规则（迁移已完成，2026-10-19）

框架内容已迁入 `Content/StoryFramework/`（849 个资产），路径保持 `/Game/StoryFramework/...` 不变。

**优先复用，不要重造：**

| 需要什么 | 先查 |
| --- | --- |
| 全局状态 / 服务入口 | `Core/SFGameInstance_BP` |
| 可交互物 | `Core/Blueprints/InteractableBase_BP` + `SFInteraction_BPI` |
| 对话 / 剧情 | `Core/Dialogue/DialogueGraphActor`（含 DialogueTables、HowToUse） |
| 存档 | `SaveGame/` |
| 菜单 / UI | `Menus/`、`Core/UserInterface/` |
| 集中数值配置 | `StoryFrameworkValues` |

**规则**
- 继承而非复制：需要特化就派生子类，不要复制一份框架资产再改。
- `/Game/StoryFramework/...` 路径**不改名**，改名会大面积断链。
- 框架资产内部逻辑、变量、默认值**不改**；确实需要改先问用户。
- 以下接线已配好，**不要动**：`GameInstanceClass`、`SFInteraction` 碰撞通道（`ECC_GameTraceChannel1`）、`FixedInteraction → SFInteraction` 重定向、`UserInterfaceSettings`（设计分辨率 1920×1080 / 最短边缩放 / 自定义光标）。

**已知历史问题（不是本工程引入，不要顺手修）**
- 约 25 处 `/Game/` 悬挂引用，集中在 `Core/Example`（示例内容）与 `Utility/SFTools_EUW`；其中 `Core/Blueprints/Structures/TransitionSettings_S` 指向不存在的 `/Game/Lens/Blueprints/Curves/EaseOut_FloatCurve`。
- `Core/Example/.../Notifies/OnStep_AN` 曾编译失败，用户已手工修复；**不要再动它**。
- 约 29 个框架资产与 `Content/Characters`、`Content/LevelPrototyping` 同名（包路径不同，非类冲突）。

---

## 6. 编码规范（C++）

- 遵循 Epic/UE 官方规范：`U/A/F/E` 前缀、PascalCase、布尔 `b` 前缀、`TObjectPtr<>` 持有 UObject、`TWeakObjectPtr`/`TSoftObjectPtr` 破解循环引用
- 头文件：`#pragma once`、前向声明替代 include、`.generated.h` 必须最后
- UPROPERTY 必须有明确分类与访问级别；**任何被 GC 持有的 UObject 引用都要 UPROPERTY**
- 不使用裸 `new`；用 `NewObject` / `CreateDefaultSubobject`
- 参数传递：`const FVector&`、`const TArray<X>&`；返回用移动或 `const&`
- 日志：统一用 `DECLARE_LOG_CATEGORY_EXTERN(LogWakeTime, Log, All)`，禁止 `UE_LOG(LogTemp, ...)` 留在提交里
- 校验：可恢复用 `ensure`、致命用 `check`；对外 API 入口做空指针防御
- 字符串：资产/标识符用 `FName`，UI 显示用 `FText`（走本地化），路径用 `FSoftObjectPath`
- 不使用 `Tick` 做周期逻辑：用 `FTimerHandle` / 定时器 / 事件驱动；确需 Tick 时在头文件注释写清理由与成本
- 暴露给蓝图：`UFUNCTION(BlueprintCallable)` / `BlueprintPure` / `BlueprintImplementableEvent`（表现钩子）/ `BlueprintNativeEvent`（可重写默认实现）
- 数值不要硬编码：进 `UDeveloperSettings` 或 DataAsset，代码里用默认值兜底
- 不写 null-check 掩盖错误；不写静默失败的分支
- 只写需要的 include；不引入新第三方库

---

## 7. C++ / 蓝图分工

| 放 C++ | 放蓝图 |
| --- | --- |
| 感知判定、警戒状态机、噪音传播 | HUD 视觉、动效、材质参数 |
| 行为树 Task/Service/Decorator 实现 | 行为树资产里的节点连线与参数 |
| 交互接口、门锁/钥匙规则 | 具体物件的可调参数、音效触发 |
| 存档字段与读写流程 | 存档槽 UI |
| 输入 Action 的响应逻辑 | IMC/IA 资产本身、按键重绑定 UI |
| 任何每帧/高频/数学密集计算 | 一次性表现、事件响应 |

原则：**逻辑可测试、可在版本控制里 review 的部分放 C++**；经常调、靠眼睛判断的部分放蓝图。蓝图里超过 ~5 个节点的分支逻辑，抽成 C++ `BlueprintCallable`。

### 7.1 蓝图禁用 Tick（硬性）

蓝图图中**禁止**出现：

- `Event Tick`（`ReceiveTick`）驱动的任何逻辑
- Timeline 的 Update 输出驱动玩法（表现类插值可用，但不能承载状态判断）
- `Delay` 自循环 / `While` 式轮询 / 每帧 `ForEachLoop` 遍历
- 靠 Overlap/BeginPlay 反复触发的"伪循环"轮询

**正确做法**（按优先级）：

1. 在 C++ 实现计算：`UActorComponent`、子系统、或 Actor 方法，再派生蓝图子类
2. 蓝图只暴露 `UPROPERTY(EditAnywhere)` 参数和 `BlueprintImplementableEvent` 表现钩子
3. 频率需求用 `FTimerManager`（0.1–0.2s）、事件驱动，或 `PrimaryComponentTick.bCanEverTick` + 自定义间隔
4. 确需每帧时在 C++ 侧裁剪：`TickGroup`、距离门限、可见性判断、`SetActorTickEnabled` 动态开关

遇到蓝图里已有的 Tick：**不要原地加逻辑**。先记录，再按"CPP 基类 + 蓝图子类"重构；无法一次完成就写明遗留项，不要假装完成。

检查方式：改动过的蓝图逐个打开确认无 Tick；批量排查用 unreal-mcp 遍历蓝图资产检查节点。

---

## 8. 输入

- 只用 Enhanced Input：`InputMappingContext` + `InputAction`，资产放 `Content/Input`
- 新增动作：在 `SetupPlayerInputComponent` 里绑定，`IMC` 挂载点复用现有逻辑（`Wake_TimePlayerController` / Character）
- 不硬编码键位、不直接读 `PlayerInput`；不新建第二套 InputComponent 体系
- 潜行相关动作（蹲伏、探头、快速投掷、交互、掩体）用统一绑定函数，并在 `DefaultInput.ini` 中与蓝图保持一致

---

## 9. AI：行为树优先

设计前提：**同屏敌人不超过 20 个**。

- **AI 行为统一使用行为树（Behavior Tree + Blackboard）**，不要新增 StateTree 的 AI 逻辑
- 优先用引擎自带节点（`MoveTo`、`Wait`、`Simple Parallel`、Blackboard 装饰器等）
- 自定义节点写 C++：`UBTTaskNode` / `UBTService` / `UBTDecorator`。**不用蓝图版 Task/Service**
- Blackboard 键集中定义，命名带语义：`TargetActor`、`LastKnownLocation`、`AlertLevel`、`PatrolIndex`
- 服务间隔 ≥ 0.2s；装饰器开 `Observer Aborts` 做条件中断，不要让树每帧空转
- 感知由 `UStealthPerceptionComponent` / `AIPerceptionComponent` 负责，行为树只消费结果，**不在节点里做 Trace**
- `StateTree` 插件保留启用，但仅用于**非 AI** 的流程状态（关卡流程、剧情阶段、玩家状态）
- 同屏 AI 数量上限做成 `UDeveloperSettings` 可调项
- AI 侧不得直接调用 UI；通过事件/委托向子系统广播，UI 自行订阅

---

## 10. 构建、验证与"完成"的定义

| 步骤 | 命令/方式 |
| --- | --- |
| 编译 | UBT 构建 `Wake_TimeEditor`（Win64 / Development），或编辑器 Live Coding |
| 资产与场景校验 | 现有 `Scripts/`（`validate_dorm.py`、`import_dorm.py` 等）按需复用 |
| 编辑器内验证 | `unreal-mcp`（`http://127.0.0.1:8000/mcp`）查资产、跑 PIE |
| 自动化测试 | `-ExecCmds="Automation RunTests Wake_Time;Quit"`（新测试放模块 `Private/Tests`） |
| 框架迁移校验 | `python check_framework_migration.py`（工作区根，需要时用） |

一次交付必须同时给出：

1. 编译通过（报错即回退，不要留半成品）
2. 变更文件清单（每个文件一句话说明）
3. 验证记录：怎么跑起来的、PIE 到什么现象、日志有无 Warning/Error
4. 蓝图改动说明：确认无 Tick；若重构了 Tick 逻辑，写清改前/改后
5. 未覆盖的边界与已知风险（诚实写，不要美化）

无法在本地验证时，明确写"未验证"，不要用推断代替结论。

---

## 11. 版本控制

- 人类直接提交 `master`；**AI 代理必须开分支并提 PR**
- 分支命名：`chatbox/<简短英文描述>`，如 `chatbox/import-dorm-props`
- 一个 PR 只做一件事；PR 描述写清动机、改动、验证方式
- 提交前：`git status` 确认没有误带 `Binaries/`、`Intermediate/`、`Saved/`、`DerivedDataCache/`（这些在 `.gitignore` 内，别用 `-f` 强推）
- 不 squash 别人的历史、不 force push、不改 LFS 配置
- 提交信息用祈使句；涉及代码改动时附 `Co-authored-by: Chatbox <chatbox@chatboxai.com>`
- 未来可能迁移 Perforce：**不要依赖 git 特有机制**（submodule、复杂 hook）
- 提交前确认 `git lfs pull` 已完成、LFS 对象已就位

---

## 12. 资产与目录规范

- 可跨关卡复用 → `Content/assets/<类别>/`；仅本关可用 → 该关卡目录
- 新玩法资产 → `Content/Stealth/...` 或 `Content/Dorm/...` 下对应子目录
- 命名遵循 Epic 官方规范（见 §3.2）
- `.uasset`/`.umap` 只能通过编辑器（或 unreal-mcp 的工具）修改
- 不动 `Content/Dorm` 的导入资产
- 不删除 `Content/Developers` 里他人的内容
- 大量新增素材时，在 PR 里列出清单与体积

---

## 13. 汇报格式（中文）

每轮结束用这个结构，不要写长篇流水账：

```
改动：<一句话目标>
文件：<路径> — <一句话>
行为：<玩家/AI/编辑器里可观察到的变化>
验证：<编译结果 / PIE 现象 / 日志 / 未验证>
风险：<已知边界、待确认项>
```

需要决策时，给出 2–3 个选项 + 你的推荐，不要只抛问题。

---

## 14. 快速排错

| 现象 | 常见原因 |
| --- | --- |
| 链接错误 `undefined symbol` | 模块依赖没加到 `Build.cs` |
| UHT 报错 `generated.h` | include 顺序错，或头文件里用了未声明类型 |
| 编辑器里类丢失 | 改了类名/模块却没重启编辑器，或 redirect 被删 |
| 蓝图编译后行为异常 | C++ 改了 `BlueprintImplementableEvent` 签名，蓝图未重新编译 |
| AI 不行动 | 行为树未绑定到 AIController、Blackboard 未设置、NavMesh 未生成 |
| 行为树节点不触发 | 装饰器 `Observer Aborts` 配置不当，或 Service 间隔过大 |
| 交互无反应 | `SFInteraction` 碰撞通道缺失（见 §5），Trace 静默退化为 Visibility |
| GameInstance 相关功能全挂 | `GameInstanceClass` 未指向 `SFGameInstance_BP` |
| 资产引用丢失 | 有人移动/改名了 `.uasset`（参见 §2 第 1 条） |
| 素材导入后显示异常 | 贴图 sRGB/压缩设置、材质域、Nanite 兼容性；先看 Content Browser 有无红色报错 |
| 关卡打开后一片黑 | 灯光被删、World Partition 未加载、Lumen 设置被改 |

---

**本文件的修改**：改动前先问用户。用户手动改过的内容，AI 不得回滚（见 §0）。
