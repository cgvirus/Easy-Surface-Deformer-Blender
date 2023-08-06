# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
	"name": "Easy Surface Deformer",
	"description": "Assign Surface Deformer easily",
	"author": "Fahad Hasan Pathik CGVIRUS",
	"version": (1, 0),
	"blender": (3, 60, 0),
	"category": "Object",
	"wiki_url": "https://github.com/cgvirus/Easy-Surface-Deformer-Blender"
}

import bpy
from bpy.types import Operator, Panel
bpy.types.Scene.target = bpy.props.PointerProperty(type=bpy.types.Object)



class instanceInCollection(bpy.types.Operator):
	"""Create instace of body in a sperate collection"""
	bl_idname = "easysdf.instance_collection"
	bl_label = "Instance Collection"

	def instance_in_collection(self,context):

		active_obj = bpy.context.active_object
		
		linked_name = "SDF_REF_" + active_obj.name
		found_instance = bpy.context.scene.objects.get(linked_name)

		if not found_instance:

			linked_obj = active_obj.copy()
			bpy.context.collection.objects.link(linked_obj)
			linked_obj.name = linked_name

			col = bpy.data.collections.new(name="SDF_REF_Collection")
			bpy.context.scene.collection.children.link(col)
			vlayer = bpy.context.view_layer.layer_collection.children.get(col.name)
			col.hide_render = True
			# col.hide_viewport = True
			vlayer.hide_viewport = True

			if linked_obj.name not in col.objects:

				for other_col in linked_obj.users_collection:
					other_col.objects.unlink(linked_obj)

				col.objects.link(linked_obj)

			mask_mods = [mod for mod in linked_obj.modifiers if mod.type == 'MASK' and \
						mod.name != 'Hide helpers']
			if mask_mods:
				for mods in mask_mods:
					linked_obj.modifiers.remove(mods)

	def execute(self, context):

		try:
			self.instance_in_collection(context)
			return {'FINISHED'}
		except:
			return {'CANCELLED'}


class bindSurfaceDeform(bpy.types.Operator):
	"""Bind objects to body"""
	bl_idname = "easysdf.bind_surface"
	bl_label = "Bind Surface Deform"
	

	def bind_surface_deform(self,context):

		target_obj =  bpy.context.scene.target
		selected_objs = bpy.context.selected_objects
		target_obj.data.shape_keys.use_relative = False


		objs = [o for o in selected_objs
			if o.type == 'MESH'
			and o is not target_obj
			]

		for obj in objs:
			if obj.modifiers.get('SDF_Deformer') == None:
				mod = obj.modifiers.new("SDF_Deformer", 'SURFACE_DEFORM')
				mod.target = target_obj
				with bpy.context.temp_override(object=obj):
					bpy.ops.object.surfacedeform_bind(
						modifier=mod.name
						)

		target_obj.data.shape_keys.use_relative = True
		
	def execute(self, context):

		try:
			self.bind_surface_deform(context)
			return {'FINISHED'}
		except:
			return {'CANCELLED'}


class removeSurfaceDeform(bpy.types.Operator):

	"""Unbind objects from body"""
	bl_idname = "easysdf.remove_bind_surface"
	bl_label = "Remove Surface Deform"

	def remove_surface_deform(self,context):

		selected_objs = bpy.context.selected_objects

		for obj in selected_objs:
			if obj.type == 'MESH' and obj.modifiers.get('SDF_Deformer')!= None:
				mod = obj.modifiers.get('SDF_Deformer')
				if mod.type == 'SURFACE_DEFORM':
					obj.modifiers.remove(mod)

	def execute(self, context):
		try:
			self.remove_surface_deform(context)
			return {'FINISHED'}
		except:
			return {'CANCELLED'}


class applySurfaceDeform(bpy.types.Operator):

	"""Apply Surface Deformer"""
	bl_idname = "easysdf.apply_bind_surface"
	bl_label = "Apply Surface Deform"


	def apply_surface_deform(self,context):

		selected_objs = bpy.context.selected_objects
		active_obj = bpy.context.active_object

		for obj in selected_objs:
			if obj.type == 'MESH' and obj.modifiers.get('SDF_Deformer')!= None:
				bpy.context.view_layer.objects.active = obj
				mod = obj.modifiers.get('SDF_Deformer')
				if mod.type == 'SURFACE_DEFORM':
					bpy.ops.object.modifier_apply(modifier=mod.name)

		bpy.context.view_layer.objects.active = active_obj


	def execute(self, context):
		try:
			self.apply_surface_deform(context)
			return {'FINISHED'}
		except:
			return {'CANCELLED'}
		
class applyShapeKey(bpy.types.Operator):

	"""Apply Deformer as shape key"""
	bl_idname = "easysdf.apply_shape_key"
	bl_label = "Apply SDF Shape Key"


	def apply_shape_key(self,context):

		target_obj = bpy.context.scene.target
		selected_objs = bpy.context.selected_objects
		target_key_len = len(target_obj.data.shape_keys.key_blocks)
		target_obj.data.shape_keys.use_relative = False
		target_obj.show_only_shape_key = True


		objs = [o for o in selected_objs
				if o.type == 'MESH'
				and o is not target_obj]
		

		for obj in objs:

			if obj.data.shape_keys == None:
				obj.shape_key_add(name="Basis",from_mix=False)


			for n in range (1,target_key_len):

				obj_keylen = len(obj.data.shape_keys.key_blocks)
				target_obj.active_shape_key_index = n
				target_shapekey_name = target_obj.active_shape_key.name + "_SDF"
				target_shapekey_value = target_obj.active_shape_key.value
				target_shapekey_isMute = target_obj.active_shape_key.mute

				if obj.data.shape_keys.key_blocks.get(target_shapekey_name) == None and \
					not target_shapekey_isMute:

					if obj.type == 'MESH' and obj.modifiers.get('SDF_Deformer')!= None:
						bpy.context.view_layer.objects.active = obj
						mod = obj.modifiers.get('SDF_Deformer')
					if mod.type == 'SURFACE_DEFORM':
						bpy.ops.object.modifier_apply_as_shapekey(keep_modifier = True,modifier = mod.name)
					
					obj.active_shape_key_index = obj_keylen
					obj.active_shape_key.value = target_shapekey_value
					obj.active_shape_key.name = target_shapekey_name
					key = obj.data.shape_keys.key_blocks[target_shapekey_name]
					key.driver_remove("value") #to delete duplicates
					key.driver_remove("slider_min") #to delete duplicates
					key.driver_remove("slider_max") #to delete duplicates


		target_obj.data.shape_keys.use_relative = True
		target_obj.show_only_shape_key = False


	def execute(self, context):
		try:
			bindSurfaceDeform.bind_surface_deform(self,context)
			self.apply_shape_key(context)
			removeSurfaceDeform.remove_surface_deform(self,context)
			return {'FINISHED'}
		except:
			return {'CANCELLED'}
		


class LinkShapeKey(bpy.types.Operator):

	"""Link shape keys with driver"""
	bl_idname = "easysdf.link_shape_key"
	bl_label = "Link SDF shape keys as drivers"


	def create_driver(self,context,obj,target_obj,target_shapekey_name,targetprop:str):
		#Driver add
		key = obj.data.shape_keys.key_blocks[target_shapekey_name]
		key.driver_remove(targetprop) #to delete duplicates
		driver = key.driver_add(targetprop)
		driver.driver.type = 'AVERAGE'
		newVar = driver.driver.variables.new()
		newVar.name = "SDF_var"
		newVar.type = 'SINGLE_PROP'
		newVar.targets[0].id_type = 'KEY'
		newVar.targets[0].id = target_obj.data.shape_keys
		newVar.targets[0].data_path = 'key_blocks["'+ target_obj.active_shape_key.name +'"].'+targetprop


	def link_driver(self,context):

		target_obj = bpy.context.scene.target
		selected_objs = bpy.context.selected_objects
		target_key_len = len(target_obj.data.shape_keys.key_blocks)


		objs = [o for o in selected_objs
				if o.type == 'MESH'
				and o is not target_obj]
		

		for obj in objs:

			if obj.data.shape_keys == None:
				obj.shape_key_add(name="Basis",from_mix=False)


			for n in range (1,target_key_len):

				obj_keylen = len(obj.data.shape_keys.key_blocks)
				target_obj.active_shape_key_index = n
				target_shapekey_name = target_obj.active_shape_key.name + "_SDF"
				target_shapekey_value = target_obj.active_shape_key.value

				if obj.data.shape_keys.key_blocks.get(target_shapekey_name) != None:

					self.create_driver(context,obj,target_obj,target_shapekey_name,"value")
					self.create_driver(context,obj,target_obj,target_shapekey_name,"slider_min")
					self.create_driver(context,obj,target_obj,target_shapekey_name,"slider_max")
					
					obj.active_shape_key_index = obj_keylen




	def execute(self, context):
		try:
			self.link_driver(context)
			return {'FINISHED'}
		except:
			return {'CANCELLED'}
		


#UI


class easySurfaceDeform_UI(bpy.types.Panel):

	bl_label = "Easy Surface Deform"
	bl_idname = "VIEW3D_PT_EasySdf"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Tools"


	def draw(self, context):
		layout = self.layout

		layout.operator("easysdf.instance_collection", text="create instance collection")
		layout.prop_search(context.scene, "target", context.scene, "objects", text="Select Target")
		layout.operator("easysdf.bind_surface", text="bind objects")
		layout.operator("easysdf.remove_bind_surface", text="remove binding")
		layout.operator("easysdf.apply_bind_surface", text="apply binding")

		

class SDF_ShapeKey_UI(bpy.types.Panel):

	bl_label = "Easy SDF Shape Keys"
	bl_idname = "VIEW3D_PT_EasySdfShapeKey"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Tools"


	def draw(self, context):
		layout = self.layout
		layout.operator("easysdf.apply_shape_key", text="apply shape key")
		layout.operator("easysdf.link_shape_key", text="link shape key")
		bpy.types.DATA_PT_shape_keys.draw(self, context)





classes = (
	instanceInCollection,
	bindSurfaceDeform,
	removeSurfaceDeform,
	applySurfaceDeform,
	easySurfaceDeform_UI,
	applyShapeKey,
	LinkShapeKey,
	SDF_ShapeKey_UI
)

def register():

	from bpy.utils import register_class
	
	for c in classes:
		bpy.utils.register_class(c)

def unregister():
	
	from bpy.utils import unregister_class
	
	# remove operator and preferences
	for c in reversed(classes):
		bpy.utils.unregister_class(c)



if __name__ == "__main__":
	register()