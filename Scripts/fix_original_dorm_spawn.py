"""Save the original World Partition PlayerStart external actor explicitly."""
import unreal,json,time,traceback
from pathlib import Path
P=Path(unreal.Paths.project_dir()).resolve();L=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);A=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def fix():
 start=next(a for a in A.get_all_level_actors() if isinstance(a,unreal.PlayerStart));start.modify();start.set_actor_location(unreal.Vector(35,-65,105),False,False);start.set_actor_rotation(unreal.Rotator(0,-90,0),False)
 if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):raise RuntimeError('Could not save PlayerStart external package')
 L.save_current_level();L.load_level('/Game/ThirdPerson/Lvl_ThirdPerson')
 start=next(a for a in A.get_all_level_actors() if isinstance(a,unreal.PlayerStart));p=start.get_actor_location()
 if max(abs(x-y) for x,y in zip((p.x,p.y,p.z),(35,-65,105)))>.01:raise RuntimeError('PlayerStart was not saved')
 report=P/'Docs/Dorm/OriginalLevelValidation.json';r=json.loads(report.read_text(encoding='utf-8'));r['player_start_saved_location_cm']=[p.x,p.y,p.z];r['player_start_external_package_verified']=True;report.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
 camera=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='Dorm_CAM_00_Complete_Overview');L.pilot_level_actor(camera);A.set_selected_level_actors([])
 unreal.log('ORIGINAL_DORM_SPAWN_SAVED '+str(p))
if L.is_in_play_in_editor():
 L.editor_request_end_play()
 def tick(dt):
  if L.is_in_play_in_editor():return
  unreal.unregister_slate_post_tick_callback(handle)
  try:fix()
  except Exception:(P/'Saved/DormImport/SpawnFixError.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
 handle=unreal.register_slate_post_tick_callback(tick)
else:fix()
