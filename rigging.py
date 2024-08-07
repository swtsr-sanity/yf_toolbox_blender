import bpy
import importlib
from . import yf_lib

class YfToolbox_Operator_LinkDEF2TGT(bpy.types.Operator):
    bl_idname = "yf.toolbox_rigging_op_link_tgt_to_def"
    bl_label = "LINK DEF -> TGT"
    CONSTRAINT_NAME = "COPY XFORM DEF->TGT"

    @classmethod
    def description(cls, context, properties):
        return "Create Target(TGT) bones for Deform(DEF) bones, then add \"Copy Transform\" constraint on it"

    def execute(self, context):
        obj_ = yf_lib.get_active_object()
        if not obj_ or obj_.type != 'ARMATURE':
            self.report("No armature is selected!")
            return {'FINISHED'}
        
        armature_ = obj_.data # type: bpy.types.Armature
        pose_ = obj_.pose

        start_mode = yf_lib.get_active_object_interaction_mode()
        # Enter EDIT mode if not
        if start_mode != 'EDIT':
            yf_lib.set_active_object_interaction_mode('EDIT')
        
        for bone in armature_.edit_bones:
            if bone.name.startswith('DEF_'):
                TGT_bone_name = 'TGT_' + bone.name[4:]
                # Check TGT_ bone is already there
                new_bone = armature_.edit_bones.get(TGT_bone_name)
                if not new_bone:
                    # Exisiting TGT is not found. Create the TGT
                    new_bone = armature_.edit_bones.new('TGT_' + bone.name[4:])
                    # Change the name prefix from 'DEF_' to 'TGT_'
                    new_bone.head = bone.head
                    new_bone.tail = bone.tail
                    new_bone.roll = bone.roll

        yf_lib.set_active_object_interaction_mode('POSE')

        for bone in pose_.bones:
            # Check if the bone name starts with 'DEF_'
            if bone.name.startswith('DEF_'):
                # Construct the corresponding target bone name
                tgt_bone_name = 'TGT_' + bone.name[4:]
                # Check if the corresponding target bone exists
                to_remove_constraints = filter(lambda x: x.name==self.CONSTRAINT_NAME or (x.target==obj_ and x.subtarget==tgt_bone_name), bone.constraints)
                for c in to_remove_constraints:
                    bone.constraints.remove(c)
                
                # Add a Copy Transforms constraint to the DEF_ bone
                copy_transforms = bone.constraints.new(type='COPY_TRANSFORMS')
                copy_transforms.name = self.CONSTRAINT_NAME
                # Set the target of the constraint to the armature and the target bone
                copy_transforms.target = obj_
                copy_transforms.subtarget = tgt_bone_name

        yf_lib.set_active_object_interaction_mode(start_mode)
        return {'FINISHED'}

class YfToolbox_Operator_AutoBoneCollection(bpy.types.Operator):
    bl_idname = "yf.toolbox_rigging_auto_bone_collection"
    bl_label = "Auto Bone Collection"

    @classmethod
    def description(cls, context, properties):
        return "Add bones to collections by their prefix"

    def execute(self, context):
        obj_ = yf_lib.get_active_object()
        armature_ = obj_.data # type: bpy.types.Armature
        if not obj_ or obj_.type != 'ARMATURE':
            self.report("No armature is selected!")
            return {'FINISHED'}
        
        start_mode = yf_lib.get_active_object_interaction_mode()
        # Enter EDIT mode if not
        if start_mode != 'EDIT':
            yf_lib.set_active_object_interaction_mode('EDIT')
        for collection in armature_.collections:
            for bone in armature_.edit_bones:
                if bone.name.startswith(f"{collection.name}_"):
                    collection.assign(bone)
                else:
                    collection.unassign(bone)

        return {'FINISHED'}

class YfToolbox_Panel_Rigging(bpy.types.Panel):
    bl_idname = "yf.toolbox_rigging_panel"
    bl_label = "RIGGING"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "YF"

    def draw(self, context):
        # You can set the property values that should be used when the user
        # presses the button in the UI.
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.operator("yf.toolbox_rigging_op_link_tgt_to_def",
                         text="LINK TGT -> DEF",
                         icon="DECORATE_LINKED")
        row = layout.row()
        row.operator("yf.toolbox_rigging_auto_bone_collection",
                         text="AUTO BONE COLLECTION",
                         icon="COLLECTION_NEW")

def register():
    bpy.utils.register_class(YfToolbox_Panel_Rigging)
    bpy.utils.register_class(YfToolbox_Operator_LinkDEF2TGT)
    bpy.utils.register_class(YfToolbox_Operator_AutoBoneCollection)

def unregister():
    bpy.utils.unregister_class(YfToolbox_Panel_Rigging)
    bpy.utils.unregister_class(YfToolbox_Operator_LinkDEF2TGT)
    bpy.utils.unregister_class(YfToolbox_Operator_AutoBoneCollection)

