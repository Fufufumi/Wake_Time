"""Persist the dorm cutaway visibility, frame it, and verify both saved maps."""
import unreal,json,math
from pathlib import Path
P=Path(unreal.Paths.project_dir()).resolve();D=json.loads((P/'SourceArt/Dorm/dorm_import.json').read_text(encoding='utf-8'))
L=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);A=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report={'success':False,'maps':[],'errors':[]}
for name in ['Lvl_Dorm','Lvl_Dorm_Overview']:
 path='/Game/Dorm/Maps/'+name
 if not L.load_level(path):raise RuntimeError('Unable to open '+path)
 actors={a.get_actor_label().removeprefix('Dorm_'):a for a in A.get_all_level_actors() if a.get_actor_label().startswith('Dorm_')}
 hidden=0;initially_visible_hidden=0
 for row in D['scene']['objects']:
  a=actors.get(row['name'])
  if not a:raise RuntimeError('Missing dorm layout part '+row['name'])
  cut=name.endswith('_Overview') and row.get('cutaway_hidden',False)
  if 'mesh' in row:
   c=a.get_component_by_class(unreal.StaticMeshComponent)
   if cut and c.get_editor_property('visible'):initially_visible_hidden+=1
   c.set_visibility(not cut,True);hidden+=int(cut)
  a.set_actor_hidden_in_game(cut);a.set_is_temporarily_hidden_in_editor(False)
 camera=actors['CAM_00_Complete_Overview'];cam=camera.get_component_by_class(unreal.CameraComponent)
 cam.set_editor_property('ortho_width',1700.);cam.set_editor_property('aspect_ratio',1600./1100.)
 viewloc=unreal.Vector(650.,650.,1000.);viewrot=unreal.MathLibrary.find_look_at_rotation(viewloc,unreal.Vector(0,-410,90))
 unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(viewloc,viewrot)
 A.set_selected_level_actors([])
 if not L.save_current_level():raise RuntimeError('Unable to save '+path)
 # Reopening the saved map verifies persistent visibility in the normal editor.
 if not L.load_level(path):raise RuntimeError('Unable to reopen '+path)
 actors={a.get_actor_label().removeprefix('Dorm_'):a for a in A.get_all_level_actors() if a.get_actor_label().startswith('Dorm_')}
 maximum=0.;meshcount=0;visible=0
 for row in D['scene']['objects']:
  a=actors[row['name']];loc=a.get_actor_location();maximum=max(maximum,max(abs(v-e) for v,e in zip((loc.x,loc.y,loc.z),row['world']['location'])))
  if 'mesh' not in row:continue
  meshcount+=1;c=a.get_component_by_class(unreal.StaticMeshComponent);expected=not(name.endswith('_Overview') and row.get('cutaway_hidden',False))
  if c.get_editor_property('visible')!=expected:raise RuntimeError('Persistent visibility mismatch '+row['name'])
  visible+=int(c.get_editor_property('visible'))
 if meshcount!=637 or maximum>.15:raise RuntimeError('Dorm scene placement mismatch '+name)
 report['maps'].append({'map':path,'mesh_instances':meshcount,'visible_mesh_instances':visible,'cutaway_mesh_instances':hidden,'previously_visible_cutaway_meshes':initially_visible_hidden,'max_position_error_cm':maximum,'persistent_visibility_verified':True})
report['success']=True
(P/'Docs/Dorm/SceneSetupValidation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
unreal.log('DORM_SCENE_SETUP_COMPLETE '+str(report))
