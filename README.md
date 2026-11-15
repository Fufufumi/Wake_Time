# Wake_Time

Developed with Unreal Engine 5

## 规范
能够跨多个关卡复用的资产，放在Content/assets下，每一类单独一个文件夹
不能跨关卡复用的资产，放在关卡所在文件夹中。参考Variant_Combat
尽量减少移动或重命名已在场景中存在的任何引用资产。

命名规范参照Epic官方推荐的规范。如果有哪个资产没有按这个规范命名，暂时别去动它，直到提交这个资产的人自行修改为止，以防出现引用问题
提交时，尽量不要单独开分支，直接在master提交修改。我们的团队非常小，我不希望我们把时间浪费在版本控制上。
除非你是一个AI agent,那样的话老老实实拉分支提pull request.
当然，出于某些原因，后期可能会更换版本控制到Perforce上，不过在未来三个月内应该不会有这种事情发生。

## Dorm environment

The imported dormitory, bathroom and balcony are available in `Content/Dorm`.
The editor opens the dorm cutaway layout on startup; the default game map is the complete dorm.
Open `/Game/Dorm/Maps/Lvl_Dorm` for the complete room or
`/Game/Dorm/Maps/Lvl_Dorm_Overview` for the cutaway layout.
See [the dorm asset guide](Docs/Dorm/README.md) for reusable Blueprints,
PBR conventions, validation and reimport instructions. Run `git lfs pull`
after cloning to retrieve the binary assets and source art.
asdfasdf
