"""Run with -ExecCmds=py <script>; allows editor ticks for shader compilation/capture."""
import unreal,time,json,traceback
from pathlib import Path
P=Path(unreal.Paths.project_dir()).resolve();OUT=P/'Docs/Dorm';OUT.mkdir(parents=True,exist_ok=True)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);levels.load_level('/Game/Dorm/Maps/Lvl_Dorm_Overview')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
camera=next(a for a in actors if isinstance(a,unreal.CameraActor) and a.get_actor_label()=='Dorm_CAM_00_Complete_Overview')
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(camera.get_actor_location(),camera.get_actor_rotation())
# Stable exposure for an architectural preview; does not change the level.
cam=camera.get_component_by_class(unreal.CameraComponent)
cam.set_editor_property('aspect_ratio',1600./1100.)
cam.set_editor_property('ortho_width',1700.)
pps=cam.get_editor_property('post_process_settings')
for k,v in [('override_auto_exposure_bias',True),('auto_exposure_bias',0.)]:pps.set_editor_property(k,v)
cam.set_editor_property('post_process_settings',pps);cam.set_editor_property('post_process_blend_weight',1.)
unreal.SystemLibrary.execute_console_command(None,'r.VSync 0')
unreal.SystemLibrary.execute_console_command(None,'t.MaxFPS 30')
unreal.SystemLibrary.execute_console_command(None,'r.ScreenPercentage 100')
unreal.SystemLibrary.execute_console_command(None,'r.TextureStreaming 0')
started=time.monotonic();state={'requested':False,'task':None};dest=OUT/'UE_Dorm_Overview.png';dest.unlink(missing_ok=True)
def tick(delta):
 try:
  elapsed=time.monotonic()-started
  if not state['requested'] and elapsed>45:
   if hasattr(unreal.SystemLibrary,'is_shader_compiling') and unreal.SystemLibrary.is_shader_compiling():return
   state['requested']=True
   state['task']=unreal.AutomationLibrary.take_high_res_screenshot(1600,1100,str(dest),camera=camera,delay=5.,force_game_view=True);unreal.log('DORM_PREVIEW_REQUESTED '+camera.get_actor_label())
  if state['task'] and state['task'].is_task_done() and dest.exists() and dest.stat().st_size>50000:
   unreal.log('DORM_PREVIEW_COMPLETE '+str(dest));unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
  elif elapsed>360:
   unreal.log_error('DORM_PREVIEW_TIMEOUT');unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
 except Exception:
  (OUT/'preview_error.txt').write_text(traceback.format_exc(),encoding='utf-8');unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
handle=unreal.register_slate_post_tick_callback(tick)
unreal.log('DORM_PREVIEW_STARTED')
