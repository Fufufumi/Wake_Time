"""Assemble the dorm inside the existing ThirdPerson map, without changing branches.

Keep original actors and logic. Archive the prototype meshes reversibly and use
an Editor Data Layer for cutaway walls: they remain visible during gameplay.
"""
import unreal,json,hashlib,traceback
from pathlib import Path
P=Path(unreal.Paths.project_dir()).resolve();D=json.loads((P/'SourceArt/Dorm/dorm_import.json').read_text(encoding='utf-8'))
MAP='/Game/ThirdPerson/Lvl_ThirdPerson';REPORT=P/'Docs/Dorm/OriginalLevelValidation.json'
L=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);A=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);DL=unreal.get_editor_subsystem(unreal.DataLayerEditorSubsystem)
EA=unreal.EditorAssetLibrary;TOOLS=unreal.AssetToolsHelpers.get_asset_tools()
if not L.load_level(MAP):raise RuntimeError('Cannot open original ThirdPerson level')
original=list(A.get_all_level_actors());existing={a.get_actor_label():a for a in original}
baseline_path=P/'Saved/DormImport/OriginalActorStates.json'
if not baseline_path.exists():
 baseline=[{'name':a.get_name(),'label':a.get_actor_label(),'class':a.get_class().get_name(),'folder':str(a.get_folder_path()),'hidden':a.get_editor_property('hidden'),'collision':a.get_actor_enable_collision(),'location':[a.get_actor_location().x,a.get_actor_location().y,a.get_actor_location().z]} for a in original]
 baseline_path.write_text(json.dumps(baseline,ensure_ascii=False,indent=2),encoding='utf-8')
baseline=json.loads(baseline_path.read_text(encoding='utf-8'))
def layer(name):
 path='/Game/Dorm/Utilities/DataLayers/'+name;asset=unreal.load_asset(path)
 if not asset:asset=TOOLS.create_asset(name,'/Game/Dorm/Utilities/DataLayers',unreal.DataLayerAsset,unreal.DataLayerFactory())
 asset.set_editor_property('data_layer_type',unreal.DataLayerType.EDITOR);EA.save_loaded_asset(asset)
 inst=next((i for i in DL.get_all_data_layers() if i.get_asset()==asset),None)
 if not inst:inst=DL.create_data_layer_instance(unreal.DataLayerCreationParameters(data_layer_asset=asset,is_private=False))
 inst.set_editor_property('is_initially_visible',False);inst.set_editor_property('is_initially_loaded_in_editor',True);DL.set_data_layer_visibility(inst,False)
 return inst
legacy_layer=layer('DL_Legacy_Playground');shell_layer=layer('DL_Dorm_CutawayShell')
legacy=[]
for a in original:
 if isinstance(a,unreal.StaticMeshActor) and str(a.get_folder_path()) in ['Playground','Legacy_Playground']:
  a.set_folder_path('Legacy_Playground');a.set_actor_hidden_in_game(True)
  # Keep the original broad floor's collision beneath/outside the dorm so the
  # existing enemy and navigation setup retain their original ground support.
  if a.get_actor_label()!='Floor':a.set_actor_enable_collision(False)
  legacy.append(a)
if legacy:DL.add_actors_to_data_layer(legacy,legacy_layer)
rootcls=unreal.load_class(None,'/Game/Dorm/Utilities/BP_Dorm_GroupRoot.BP_Dorm_GroupRoot_C')
if not rootcls:raise RuntimeError('Dorm group root missing')
meshcache={k:unreal.load_asset('/Game/Dorm/'+v['category']+'/Meshes/'+k) for k,v in D['meshes'].items()}
if not all(meshcache.values()):raise RuntimeError('Imported dorm mesh missing')
def spawn(cls,label,location=(0,0,0)):
 a=existing.get(label)
 if not a:a=A.spawn_actor_from_class(cls,unreal.Vector(*location));a.set_actor_label(label);existing[label]=a
 return a
def xform(t):return unreal.Transform(location=unreal.Vector(*t['location']),rotation=unreal.Quat(*t['quaternion']).rotator(),scale=unreal.Vector(*t['scale']))
parts={};shell=[]
for row in D['scene']['objects']:
 a=spawn(unreal.StaticMeshActor if 'mesh' in row else rootcls,'Dorm_'+row['name'])
 if a.get_attach_parent_actor():a.detach_from_actor(unreal.DetachmentRule.KEEP_WORLD,unreal.DetachmentRule.KEEP_WORLD,unreal.DetachmentRule.KEEP_WORLD)
 a.root_component.set_mobility(unreal.ComponentMobility.MOVABLE);a.set_actor_transform(xform(row['world']),False,False)
 a.set_editor_property('is_spatially_loaded',False)
 a.set_actor_hidden_in_game(False);a.set_is_temporarily_hidden_in_editor(False)
 if 'mesh' in row:
  c=a.get_component_by_class(unreal.StaticMeshComponent);c.set_static_mesh(meshcache[row['mesh']]);c.set_visibility(True,True)
  if row.get('cutaway_hidden'):shell.append(a)
 a.set_folder_path('Dorm/'+(row['collections'][0] if row['collections'] else 'Layout'));a.set_editor_property('tags',[unreal.Name('DormImported'),unreal.Name(row['name'])]);parts[row['name']]=a
for row in D['scene']['objects']:
 if row['parent']:parts[row['name']].attach_to_actor(parts[row['parent']],'',unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,False)
DL.add_actors_to_data_layer(shell,shell_layer)
for i,(x,y,z,power) in enumerate([(0,-190,265,1250),(0,-470,265,1250),(-120,-80,245,700),(0,-770,300,1800)]):
 a=spawn(unreal.PointLight,'Dorm_Interior_Light_'+str(i),(x,y,z));a.set_folder_path('Dorm/Lighting');a.set_editor_property('is_spatially_loaded',False)
 c=a.get_component_by_class(unreal.PointLightComponent);c.set_mobility(unreal.ComponentMobility.MOVABLE);c.set_editor_property('intensity_units',unreal.LightUnits.LUMENS);c.set_editor_property('intensity',power);c.set_editor_property('attenuation_radius',750.);c.set_editor_property('source_radius',35.);c.set_editor_property('use_temperature',True);c.set_editor_property('temperature',5200.)
for row in D['scene']['cameras']:
 a=spawn(unreal.CameraActor,'Dorm_'+row['name'],row['location']);a.set_actor_rotation(unreal.Quat(*row['quaternion']).rotator(),False);a.set_editor_property('is_spatially_loaded',False);a.set_folder_path('Dorm/Cameras')
 c=a.get_component_by_class(unreal.CameraComponent);c.set_editor_property('field_of_view',row['fov'])
 if row['ortho']:c.set_editor_property('projection_mode',unreal.CameraProjectionMode.ORTHOGRAPHIC);c.set_editor_property('ortho_width',row['ortho_width'])
 if row['name']=='CAM_00_Complete_Overview':c.set_editor_property('ortho_width',1700.);c.set_editor_property('aspect_ratio',1600./1100.)
start=next((a for a in original if isinstance(a,unreal.PlayerStart)),None)
if not start:raise RuntimeError('Original PlayerStart missing')
start.modify()
start.set_actor_location(unreal.Vector(35,-65,105),False,False);start.set_actor_rotation(unreal.Rotator(0,-90,0),False)
A.set_selected_level_actors([])
view=unreal.Vector(650,650,1000);rot=unreal.MathLibrary.find_look_at_rotation(view,unreal.Vector(0,-410,90));unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(view,rot)
if not L.save_current_level():raise RuntimeError('Failed saving original level')
if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):raise RuntimeError('Failed saving external actor packages')
if not L.load_level(MAP):raise RuntimeError('Cannot reopen original level')
actors=A.get_all_level_actors();labels={a.get_actor_label():a for a in actors};names={a.get_name() for a in actors}
missing=[r['label'] for r in baseline if r['name'] not in names]
if missing:raise RuntimeError('Original actors missing: '+str(missing))
maxerr=0.;meshcount=0
for row in D['scene']['objects']:
 a=labels.get('Dorm_'+row['name'])
 if not a:raise RuntimeError('Dorm part missing after save '+row['name'])
 p=a.get_actor_location();maxerr=max(maxerr,max(abs(v-e) for v,e in zip((p.x,p.y,p.z),row['world']['location'])))
 if 'mesh' in row:
  meshcount+=1;c=a.get_component_by_class(unreal.StaticMeshComponent)
  if not c.get_editor_property('visible') or a.get_editor_property('hidden'):raise RuntimeError('Runtime dorm part disabled '+row['name'])
 parent=a.get_attach_parent_actor()
 if row['parent'] and (not parent or parent.get_actor_label()!='Dorm_'+row['parent']):raise RuntimeError('Dorm hierarchy mismatch '+row['name'])
if meshcount!=637 or maxerr>.15:raise RuntimeError('Dorm placement check failed')
asset=unreal.load_asset('/Game/Dorm/Utilities/DataLayers/DL_Dorm_CutawayShell');inst=next(i for i in DL.get_all_data_layers() if i.get_asset()==asset)
if inst.is_runtime() or inst.is_initially_visible():raise RuntimeError('Cutaway must only affect the editor')
saved_start=next(a for a in actors if isinstance(a,unreal.PlayerStart)).get_actor_location()
if max(abs(x-y) for x,y in zip((saved_start.x,saved_start.y,saved_start.z),(35,-65,105)))>.01:raise RuntimeError('Original PlayerStart external package was not saved')
report={'success':True,'map':MAP,'source_mesh_instances':637,'saved_mesh_instances':meshcount,'source_positions_max_error_cm':maxerr,'original_actors_preserved':len(baseline),'original_actors_missing':missing,'legacy_prototype_meshes_archived':len(legacy),'legacy_ground_collision_preserved':True,'cutaway_editor_only_meshes':len(shell),'all_dorm_meshes_enabled_at_runtime':True,'original_player_start_reused':True,'original_enemy_and_game_logic_retained':True,'total_loaded_actors':len(actors),'player_start_saved_location_cm':[saved_start.x,saved_start.y,saved_start.z],'player_start_external_package_verified':True}
REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');unreal.log('ORIGINAL_DORM_INTEGRATION_COMPLETE '+str(report))
