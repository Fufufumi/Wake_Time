"""Read back imported content, Blueprint parts and both maps inside UE."""
import unreal,json,math
from pathlib import Path
P=Path(unreal.Paths.project_dir()).resolve();D=json.loads((P/'SourceArt/Dorm/dorm_import.json').read_text(encoding='utf-8'));EA=unreal.EditorAssetLibrary
OUT=P/'Docs/Dorm';OUT.mkdir(parents=True,exist_ok=True)
r={'success':False,'assets':len(D['assets']),'meshes':0,'textures':0,'materials':0,'blueprints':[],'maps':[],'errors':[]}
def require(ok,msg):
 if not ok:r['errors'].append(msg)
def errv(a,b):return max(abs(x-y) for x,y in zip(a,b))
def vec(v):return [v.x,v.y,v.z]
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for k,v in D['meshes'].items():
 m=unreal.load_asset('/Game/Dorm/'+v['category']+'/Meshes/'+k);require(m is not None,'Missing mesh '+k)
 if not m:continue
 require(len(m.get_editor_property('static_materials'))==len(v['materials']),'Material slot count '+k)
 for i,mid in enumerate(v['materials']):require(m.get_material(i) is not None and m.get_material(i).get_name()==mid,'Material slot '+k+' '+str(i))
 box=m.get_bounding_box();require(errv(vec(box.min)+vec(box.max),v['bounds_min_cm']+v['bounds_max_cm'])<.08,'Bounds '+k);r['meshes']+=1
roles={}
def walk(s,role):
 if isinstance(s,dict):
  if 'texture' in s:roles.setdefault(s['texture'],set()).add(role)
  for v in s.values():walk(v,role)
 elif isinstance(s,list):
  for v in s:walk(v,role)
for k,v in D['materials'].items():
 m=unreal.load_asset('/Game/Dorm/Materials/'+k);require(m is not None,'Missing material '+k);r['materials']+=int(m is not None)
 for role,spec in v['graph'].items():walk(spec,role)
for k in D['textures']:
 t=unreal.load_asset('/Game/Dorm/Textures/'+k);require(t is not None,'Missing texture '+k)
 if not t:continue
 require(t.get_editor_property('srgb')==('Base Color' in roles[k]),'Texture sRGB '+k)
 if 'Normal' in roles[k]:require(t.get_editor_property('flip_green_channel') and t.get_editor_property('compression_settings')==unreal.TextureCompressionSettings.TC_NORMALMAP,'Normal GL to DX '+k)
 r['textures']+=1
for a in D['assets']:
 path='/Game/Dorm/'+a['category']+'/Blueprints/BP_'+a['id'].removeprefix('SM_').removeprefix('AS_');bp=unreal.load_asset(path)
 require(bp is not None,'Missing Blueprint '+a['id'])
 if not bp:continue
 cls=unreal.load_class(None,path+'.'+path.rsplit('/',1)[1]+'_C');require(cls is not None,'Blueprint class '+a['id'])
 if not cls:continue
 instance=actors.spawn_actor_from_class(cls,unreal.Vector(0,0,0),transient=True)
 comps=instance.get_components_by_class(unreal.StaticMeshComponent);require(len(comps)==sum('mesh' in x for x in a['objects']),'Blueprint part count '+a['id'])
 rows={x['name']:x for x in a['objects']};maxerr=0
 for comp in comps:
  tags=[str(t) for t in comp.get_editor_property('component_tags')];row=next((rows[t] for t in tags if t in rows),None)
  require(row is not None,'Blueprint source part tag '+a['id'])
  if row:
   e=errv(vec(comp.get_world_location()),row['world']['location']);maxerr=max(maxerr,e);require(e<.15,'Blueprint part transform '+a['id']+' '+row['name']+' '+str(e))
  require(comp.get_editor_property('static_mesh') is not None,'Blueprint mesh reference '+a['id'])
 actors.destroy_actor(instance);r['blueprints'].append({'asset':a['id'],'mesh_components':len(comps),'max_location_error_cm':maxerr})
for mapname in ['Lvl_Dorm','Lvl_Dorm_Overview']:
 require(levels.load_level('/Game/Dorm/Maps/'+mapname),'Open map '+mapname)
 loaded={a.get_actor_label().removeprefix('Dorm_'):a for a in actors.get_all_level_actors() if a.get_actor_label().startswith('Dorm_')}
 maxerr=0;meshcount=0
 for row in D['scene']['objects']:
  a=loaded.get(row['name']);require(a is not None,'Map actor '+mapname+' '+row['name'])
  if not a:continue
  e=errv(vec(a.get_actor_location()),row['world']['location']);maxerr=max(maxerr,e);require(e<.15,'Map transform '+mapname+' '+row['name']+' '+str(e))
  parent=a.get_attach_parent_actor();require((parent.get_actor_label()=='Dorm_'+row['parent']) if row['parent'] else parent is None,'Map hierarchy '+mapname+' '+row['name'])
  if 'mesh' in row:meshcount+=1
 require(meshcount==637,'Map mesh count '+mapname)
 # Apply corrected Blender camera basis and save viewport looking into the room.
 for c in D['scene']['cameras']:
  a=loaded.get(c['name'])
  if a:a.set_actor_rotation(unreal.Quat(*c['quaternion']).rotator(),False)
 cam=loaded.get('CAM_00_Complete_Overview')
 if cam:unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())
 levels.save_current_level();r['maps'].append({'name':mapname,'mesh_actors':meshcount,'max_location_error_cm':maxerr})
if EA.does_directory_exist('/Game/Dorm/_Pilot'):EA.delete_directory('/Game/Dorm/_Pilot')
r['success']=not r['errors'];(OUT/'Validation.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
api={'screenshot':unreal.AutomationLibrary.take_high_res_screenshot.__doc__,'viewport':unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info.__doc__}
(P/'Saved/DormImport/preview_api.json').write_text(json.dumps(api,indent=2),encoding='utf-8')
unreal.log('DORM_VALIDATE '+str(r['success'])+' '+str({k:r[k] for k in ['meshes','textures','materials']})+' errors='+str(len(r['errors'])))
if r['errors']:raise RuntimeError('\n'.join(r['errors'][:12]))
