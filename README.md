# Wake_Time

Developed with Unreal Engine 5

## Dorm environment

The imported dormitory, bathroom and balcony are available in `Content/Dorm`.
The dorm is assembled directly in the original `/Game/ThirdPerson/Lvl_ThirdPerson` map,
which remains the editor startup map and default game map. Original actors and gameplay
logic are retained; the prototype geometry is archived in the `Legacy_Playground` folder.
Open `/Game/Dorm/Maps/Lvl_Dorm` for the complete room or
`/Game/Dorm/Maps/Lvl_Dorm_Overview` for the cutaway layout.
See [the dorm asset guide](Docs/Dorm/README.md) for reusable Blueprints,
PBR conventions, validation and reimport instructions. Run `git lfs pull`
after cloning to retrieve the binary assets and source art.
