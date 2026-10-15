"""Open the assembled dorm in a live UE editor and frame the layout camera."""
import unreal
L=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
L.load_level('/Game/Dorm/Maps/Lvl_Dorm_Overview')
A=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
camera=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='Dorm_CAM_00_Complete_Overview')
A.set_selected_level_actors([]);L.pilot_level_actor(camera)
unreal.log('DORM_SCENE_OPENED /Game/Dorm/Maps/Lvl_Dorm_Overview')
