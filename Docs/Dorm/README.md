# 宿舍场景与资产库

宿舍室内、入口卫生间及阳台已从当前 Blender 场景导入 UE 5.8。内容统一位于 `/Game/Dorm`。编辑器启动时打开宿舍剖视地编；运行默认进入完整宿舍，游戏模式沿用项目已有设置。

## 打开场景

- `/Game/Dorm/Maps/Lvl_Dorm`：包含完整墙体、天花板、宿舍、卫生间和阳台。
- `/Game/Dorm/Maps/Lvl_Dorm_Overview`：沿用 Blender 剖视层隐藏遮挡墙及顶棚，方便检查地编。
- 剖视遮挡通过组件可见性保存在关卡中，关闭并重新打开编辑器后仍保持生效。完整地图保留全部 637 个网格实例；剖视地图显示 545 个，隐藏 92 个遮挡部件。
- 地图内保留四个床位、门窗、半开储物柜和其内部陈设、纯白马赛克墙及入口行李箱的位置。
- `Dorm_PlayerStart` 位于宿舍入口。角色与游戏规则沿用项目已有设置。

## 资产组织

77 个资产条目各有一个可拖入关卡的 `BP_Dorm_*` 组合，位于对应分类目录的 `Blueprints` 下。146 个去重网格位于分类目录的 `Meshes`，105 个材质位于 `Materials`，288 张贴图位于 `Textures`。关卡内有 637 个网格实例、46 个层级节点。

活动部件保留独立网格、本地转轴与父子层级；门把手、马桶盖、柜门、抽屉、电脑屏幕等可分别调整。Blueprint 是资源组合，尚未接入玩家输入、开关动画或水流等游戏逻辑。Blender 自定义属性与驱动表达式保存在 `SourceArt/Dorm/dorm_import.json`，方便后续绑定。

UE 的运行时静态网格会三角化。此导入不会改变宿舍资产库中的四边面 BLEND/FBX 母版。

## 材质与尺寸

- 米转换为厘米，坐标 `(x, y, z)` 转换为 `(x, -y, z)`；每个网格均与源网格边界校验。
- Base Color 使用 sRGB；Metallic / Roughness / 打包通道使用线性采样。
- NormalGL 使用法线压缩并翻转绿色通道，适配 UE 的 DirectX 法线方向。
- 保留书本、水瓶等颜色变体、玻璃透明材质与纯白马赛克贴图。
- 静态网格使用复杂网格作为查询碰撞，以保留门洞、窗洞和中空结构。未启用刚体模拟；如需物理模拟，应为对应部件制作简单碰撞。

## 来源与重导入

当前源场景：`dorm/scene/Dorm_RoomLayout.blend`；当前资产目录：`dorm/asset/manifest.json`。生成来源包括 Hyper3D、功能拆件及人工布线整理；沿用资产库已有来源记录，不将全部网格标为 Hyper 原生输出。

`SourceArt/Dorm` 包含本轮规范化 FBX、贴图和导入清单，重导入无需访问原始 E 盘目录。`Scripts/import_dorm.py` 可在启用 PythonScriptPlugin 与 EditorScriptingUtilities 的 UE 编辑器中运行；`Scripts/validate_dorm.py` 执行尺寸、材质、Blueprint 拆件和关卡层级检查。

首次导入命令（将 UE 安装目录替换为本机实际路径）：

```powershell
$editor = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$project = (Resolve-Path '.\Wake_Time.uproject').Path
$script = (Resolve-Path '.\Scripts\import_dorm.py').Path
& $editor $project "-ExecutePythonScript=$script" '-EnablePlugins=PythonScriptPlugin,EditorScriptingUtilities' -unattended -nop4 -NullRHI
```

重导入会更新 Dorm 网格、材质与两个 Dorm 关卡，并保留已存在 Blueprint 的手工编辑。对 Blueprint 结构进行源端修改后，应先备份手工编辑，再删除对应组合进行重建。其他项目内容不会被此脚本重导入。

## Git LFS

`Content/**`、宿舍 FBX 与贴图均通过 Git LFS 管理。克隆后执行 `git lfs pull`，再用 UE 5.8 打开项目。不要提交 `Saved`、`Intermediate`、`DerivedDataCache` 或本机二进制缓存。

详细回读结果见 [Validation.json](Validation.json)。
