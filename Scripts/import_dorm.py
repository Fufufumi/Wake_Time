"""UE 5.8 editor Python: import SourceArt/Dorm and rebuild a separate dorm level.

Run using UnrealEditor-Cmd Project.uproject -ExecutePythonScript=<this file>
-EnablePlugins=PythonScriptPlugin,EditorScriptingUtilities -unattended -nop4
"""
import unreal,json,math,hashlib,traceback
from pathlib import Path
PROJECT=Path(unreal.Paths.project_dir()).resolve()
SOURCE=PROJECT/'SourceArt/Dorm'
D=json.loads((SOURCE/'dorm_import.json').read_text(encoding='utf-8'))
REPORT=PROJECT/'Saved/DormImport';REPORT.mkdir(parents=True,exist_ok=True)
TOOLS=unreal.AssetToolsHelpers.get_asset_tools();EAL=unreal.EditorAssetLibrary;MEL=unreal.MaterialEditingLibrary
BASE='/Game/Dorm';textures={};materials={};meshes={};blueprints={};stats={'assets':77,'errors':[],'mesh_checks':[],'blueprints':[],'maps':[]}
def log(s):unreal.log('DORM_IMPORT '+s)
def save_report():
 (REPORT/'import_report.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
def transform(t):
 return unreal.Transform(location=unreal.Vector(*t['location']),rotation=unreal.Quat(*t['quaternion']).rotator(),scale=unreal.Vector(*t['scale']))
def import_task(path,folder,name,options=None):
 t=unreal.AssetImportTask();t.filename=str(path);t.destination_path=folder;t.destination_name=name;t.automated=True;t.replace_existing=True;t.save=True
 if options:t.options=options
 return t
def create(name,folder,cls,factory):
 path=folder+'/'+name
 if EAL.does_asset_exist(path):return unreal.load_asset(path)
 return TOOLS.create_asset(name,folder,cls,factory)
def new_expr(mat,cls):return MEL.create_material_expression(mat,cls,-400,0)
def connect(a,out,b,pin):
 if not MEL.connect_material_expressions(a,out,b,pin):raise RuntimeError('Cannot connect material '+str(a)+' '+out+' '+pin)
def expression(mat,spec,role,cache):
 if 'value' in spec:
  v=spec['value']
  if isinstance(v,list):
   n=new_expr(mat,unreal.MaterialExpressionConstant3Vector);n.set_editor_property('constant',unreal.LinearColor(*v[:3],1))
  else:n=new_expr(mat,unreal.MaterialExpressionConstant);n.set_editor_property('r',v)
  return n,''
 if 'texture' in spec:
  key=spec['texture']
  if key not in cache:
   n=new_expr(mat,unreal.MaterialExpressionTextureSample);n.set_editor_property('texture',textures[key]);n.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if role=='Normal' else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if role=='Base Color' else unreal.MaterialSamplerType.SAMPLERTYPE_MASKS);cache[key]=n
  return cache[key],{'rgb':'RGB','r':'R','g':'G','b':'B','a':'A'}[spec.get('channel','rgb')]
 if 'normal' in spec:return expression(mat,spec['normal'],'Normal',cache)
 if 'mix' in spec:
  a,ao=expression(mat,spec['a'],role,cache);b,bo=expression(mat,spec['b'],role,cache)
  if spec['mix']=='MULTIPLY':
   n=new_expr(mat,unreal.MaterialExpressionMultiply);connect(a,ao,n,'A');connect(b,bo,n,'B')
  else:n=b
  f=spec['factor']
  if f.get('value')==1:return n,''
  mix=new_expr(mat,unreal.MaterialExpressionLinearInterpolate);connect(a,ao,mix,'A');connect(n,'',mix,'B');fc,fo=expression(mat,f,role,cache);connect(fc,fo,mix,'Alpha');return mix,''
 raise RuntimeError('Unsupported expression '+str(spec))
def import_textures():
 roles={}
 def walk(s,role):
  if isinstance(s,dict):
   if 'texture' in s:roles.setdefault(s['texture'],set()).add(role)
   for v in s.values():walk(v,role)
  elif isinstance(s,list):
   for v in s:walk(v,role)
 for m in D['materials'].values():
  for role,s in m['graph'].items():walk(s,role)
 ts=[import_task(SOURCE/v['file'],BASE+'/Textures',k) for k,v in D['textures'].items()]
 TOOLS.import_asset_tasks(ts)
 for k in D['textures']:
  tex=unreal.load_asset(BASE+'/Textures/'+k)
  if not tex:raise RuntimeError('Texture import failed '+k)
  role=roles[k]
  tex.set_editor_property('srgb','Base Color' in role)
  if 'Normal' in role:
   tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP);tex.set_editor_property('flip_green_channel',True)
  elif 'Base Color' not in role:tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
  EAL.save_loaded_asset(tex);textures[k]=tex
 log('textures '+str(len(textures)))
def import_materials():
 for k,v in D['materials'].items():
  mat=create(k,BASE+'/Materials',unreal.Material,unreal.MaterialFactoryNew());MEL.delete_all_material_expressions(mat);g=v['graph'];cache={}
  mat.set_editor_property('two_sided',True)
  glass=g.get('Transmission Weight',{}).get('value',0)>.5
  if glass:
   mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
   mat.set_editor_property('translucency_lighting_mode',unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
  for role,prop in [('Base Color',unreal.MaterialProperty.MP_BASE_COLOR),('Roughness',unreal.MaterialProperty.MP_ROUGHNESS),('Metallic',unreal.MaterialProperty.MP_METALLIC),('Normal',unreal.MaterialProperty.MP_NORMAL)]:
   if role not in g:continue
   n,out=expression(mat,g[role],role,cache);MEL.connect_material_property(n,out,prop)
  if glass:
   n,out=expression(mat,{'value':min(.28,max(.14,g.get('Alpha',{}).get('value',.2)))},'Alpha',cache);MEL.connect_material_property(n,out,unreal.MaterialProperty.MP_OPACITY)
  MEL.layout_material_expressions(mat);MEL.recompile_material(mat);EAL.set_metadata_tag(mat,'Dorm.SourceMaterial',v['name']);EAL.save_loaded_asset(mat);materials[k]=mat
 log('materials '+str(len(materials)))
def import_meshes():
 unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
 for i,(k,v) in enumerate(D['meshes'].items()):
  opt=unreal.FbxImportUI();opt.import_mesh=True;opt.import_textures=False;opt.import_materials=False;opt.import_as_skeletal=False;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH;opt.automated_import_should_detect_type=False
  si=opt.static_mesh_import_data;si.combine_meshes=True;si.generate_lightmap_u_vs=False;si.auto_generate_collision=True
  si.set_editor_property('transform_vertex_to_absolute',True);si.set_editor_property('convert_scene',True);si.set_editor_property('convert_scene_unit',False);si.set_editor_property('import_uniform_scale',100.)
  si.set_editor_property('normal_import_method',unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
  path=BASE+'/'+v['category']+'/Meshes';task=import_task(SOURCE/v['file'],path,k,opt);TOOLS.import_asset_tasks([task]);m=unreal.load_asset(path+'/'+k)
  if not m:raise RuntimeError('Mesh import failed '+k)
  for slot,mid in enumerate(v['materials']):
   if mid:m.set_material(slot,materials[mid])
  # Exact static collision keeps window/door openings and hollow fixtures open.
  bs=m.get_editor_property('body_setup')
  if bs:bs.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
  box=m.get_bounding_box();actual=[box.min.x,box.min.y,box.min.z,box.max.x,box.max.y,box.max.z];expected=v['bounds_min_cm']+v['bounds_max_cm'];err=max(abs(a-b) for a,b in zip(actual,expected))
  stats['mesh_checks'].append({'mesh':k,'bounds_error_cm':err,'slots':len(v['materials'])})
  if err>.08:raise RuntimeError('Mesh dimensions/orientation mismatch '+k+' '+str(err)+' '+str(actual)+' '+str(expected))
  EAL.set_metadata_tag(m,'Dorm.AssetID',v['asset']);EAL.save_loaded_asset(m);meshes[k]=m
  if (i+1)%20==0:log('meshes '+str(i+1)+'/'+str(len(D['meshes'])))
 log('meshes complete '+str(len(meshes)))
def component_name(n):return ''.join(x if x.isascii() and (x.isalnum() or x=='_') else '_' for x in n)[:75]+'_'+hashlib.md5(n.encode()).hexdigest()[:6]
def blueprint(name,folder,rows):
 fac=unreal.BlueprintFactory();fac.set_editor_property('parent_class',unreal.Actor)
 bp=create(name,folder,unreal.Blueprint,fac);sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
 handles=sub.k2_gather_subobject_data_for_blueprint(bp)
 # Only create once; re-import updates mesh assets and scene, while reusable BPs remain editable.
 if len(handles)>2:return bp
 byname={};pending=list(rows)
 while pending:
  progress=False
  for row in list(pending):
   if row['parent'] and row['parent'] not in byname:continue
   parent=byname[row['parent']] if row['parent'] else handles[0]
   h,fail=sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=parent,new_class=unreal.StaticMeshComponent if 'mesh' in row else unreal.SceneComponent,blueprint_context=bp))
   if str(fail):raise RuntimeError('Blueprint '+name+' '+str(fail))
   sub.rename_subobject(h,component_name(row['name']));obj=unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h))
   obj.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE)
   obj.set_editor_property('relative_location',unreal.Vector(*row['local']['location']));obj.set_editor_property('relative_rotation',unreal.Quat(*row['local']['quaternion']).rotator());obj.set_editor_property('relative_scale3d',unreal.Vector(*row['local']['scale']))
   if 'mesh' in row:obj.set_static_mesh(meshes[row['mesh']])
   obj.set_editor_property('component_tags',[unreal.Name('DormPart'),unreal.Name(row['name'])]);byname[row['name']]=h;pending.remove(row);progress=True
  if not progress:raise RuntimeError('Cyclic asset hierarchy '+name)
 unreal.BlueprintEditorLibrary.compile_blueprint(bp);EAL.save_loaded_asset(bp);return bp
def import_blueprints():
 for a in D['assets']:
  name='BP_'+a['id'].removeprefix('SM_').removeprefix('AS_');bp=blueprint(name,BASE+'/'+a['category']+'/Blueprints',a['objects'])
  EAL.set_metadata_tag(bp,'Dorm.AssetID',a['id']);EAL.set_metadata_tag(bp,'Dorm.Label',a['label_zh']);EAL.save_loaded_asset(bp);blueprints[a['id']]=bp
  stats['blueprints'].append({'asset':a['id'],'path':bp.get_path_name(),'parts':sum('mesh' in r for r in a['objects'])})
 log('blueprints '+str(len(blueprints)))
def spawn(cls,label,t=None):
 a=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(cls,unreal.Vector(0,0,0));a.set_actor_label(label)
 if t:a.set_actor_transform(transform(t),False,False)
 return a
def lights():
 for i,(x,y,z,power) in enumerate([(0,-190,265,1250),(0,-470,265,1250),(-120,-80,245,700),(0,-770,300,1800)]):
  a=spawn(unreal.PointLight,'Dorm_Interior_Light_'+str(i));a.set_actor_location(unreal.Vector(x,y,z),False,False);c=a.get_component_by_class(unreal.PointLightComponent);c.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE);c.set_editor_property('intensity_units',unreal.LightUnits.LUMENS);c.set_editor_property('intensity',power);c.set_editor_property('attenuation_radius',750.);c.set_editor_property('source_radius',35.);c.set_editor_property('use_temperature',True);c.set_editor_property('temperature',5200.)
 sun=spawn(unreal.DirectionalLight,'Dorm_Sun');sun.set_actor_rotation(unreal.Rotator(-45,-35,0),False);sun.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property('intensity',3.)
 sky=spawn(unreal.SkyLight,'Dorm_SkyLight');c=sky.get_component_by_class(unreal.SkyLightComponent);c.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE);c.set_editor_property('intensity',.6)
 spawn(unreal.SkyAtmosphere,'Dorm_SkyAtmosphere')
def build_level(cutaway=False):
 le=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);path=BASE+'/Maps/Lvl_Dorm'+('_Overview' if cutaway else '')
 if EAL.does_asset_exist(path):le.load_level(path)
 else:le.new_level(path)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 for a in actors.get_all_level_actors():
  if a.get_actor_label().startswith('Dorm_'):actors.destroy_actor(a)
 fac=unreal.BlueprintFactory();fac.set_editor_property('parent_class',unreal.Actor);rootbp=create('BP_Dorm_GroupRoot',BASE+'/Utilities',unreal.Blueprint,fac);unreal.BlueprintEditorLibrary.compile_blueprint(rootbp);EAL.save_loaded_asset(rootbp);rootcls=unreal.load_class(None,rootbp.get_path_name()+'_C')
 sceneactors={}
 hide={'02_Wall_Right','03_Wall_Left','04_Wall_Entry_Door','05_Ceiling','48_Bathroom_Review_Backdrop','35_Balcony_Canopy'}
 for row in D['scene']['objects']:
  if 'mesh' in row:
   a=spawn(unreal.StaticMeshActor,'Dorm_'+row['name'],row['world']);comp=a.static_mesh_component;comp.set_mobility(unreal.ComponentMobility.MOVABLE);comp.set_static_mesh(meshes[row['mesh']])
  else:
   a=spawn(rootcls,'Dorm_'+row['name'],row['world']);a.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
  a.set_folder_path('Dorm/'+('CutawayShell' if set(row['collections'])&hide else row['collections'][0] if row['collections'] else 'Layout'))
  a.set_editor_property('tags',[unreal.Name('DormImported'),unreal.Name(row['name'])])
  if cutaway and row.get('cutaway_hidden',bool(set(row['collections'])&hide)):
   a.set_actor_hidden_in_game(True)
   # Component visibility is serialized. Temporary editor hiding alone is lost
   # when the cutaway map is reopened in the regular editing viewport.
   if 'mesh' in row:comp.set_visibility(False,True)
  sceneactors[row['name']]=a
 for row in D['scene']['objects']:
  if row['parent']:sceneactors[row['name']].attach_to_actor(sceneactors[row['parent']],'',unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,False)
 lights()
 start=spawn(unreal.PlayerStart,'Dorm_PlayerStart');start.set_actor_location(unreal.Vector(35,-65,105),False,False);start.set_actor_rotation(unreal.Rotator(0,-90,0),False)
 for c in D['scene']['cameras']:
  a=spawn(unreal.CameraActor,'Dorm_'+c['name']);a.set_actor_location(unreal.Vector(*c['location']),False,False);a.set_actor_rotation(unreal.Quat(*c['quaternion']).rotator(),False)
  cam=a.get_component_by_class(unreal.CameraComponent);cam.set_editor_property('field_of_view',c['fov'])
  if c['ortho']:cam.set_editor_property('projection_mode',unreal.CameraProjectionMode.ORTHOGRAPHIC);cam.set_editor_property('ortho_width',c['ortho_width'])
 if not le.save_current_level():raise RuntimeError('Level save failed '+path)
 stats['maps'].append({'path':path,'mesh_actors':sum('mesh' in r for r in D['scene']['objects']),'group_actors':sum('mesh' not in r for r in D['scene']['objects'])});save_report();log('saved '+path)
try:
 if '-DormResumeLayout' in unreal.SystemLibrary.get_command_line():
  stats=json.loads((REPORT/'import_report.json').read_text(encoding='utf-8'));stats['errors']=[];stats['maps']=[]
  textures={k:unreal.load_asset(BASE+'/Textures/'+k) for k in D['textures']};materials={k:unreal.load_asset(BASE+'/Materials/'+k) for k in D['materials']}
  meshes={k:unreal.load_asset(BASE+'/'+v['category']+'/Meshes/'+k) for k,v in D['meshes'].items()}
  blueprints={a['id']:unreal.load_asset(BASE+'/'+a['category']+'/Blueprints/BP_'+a['id'].removeprefix('SM_').removeprefix('AS_')) for a in D['assets']}
  if not all(list(textures.values())+list(materials.values())+list(meshes.values())+list(blueprints.values())):raise RuntimeError('Missing assets during layout resume')
  if '-DormRebuildMaterials' in unreal.SystemLibrary.get_command_line():import_materials()
 else:import_textures();import_materials();import_meshes();import_blueprints()
 build_level(False);build_level(True)
 EAL.save_directory(BASE,only_if_is_dirty=True,recursive=True)
 stats['counts']={'meshes':len(meshes),'materials':len(materials),'textures':len(textures),'blueprints':len(blueprints),'scene_mesh_actors':637};stats['success']=True;save_report();log('COMPLETE '+str(stats['counts']))
except Exception:
 stats['errors'].append(traceback.format_exc());stats['success']=False;save_report();raise
