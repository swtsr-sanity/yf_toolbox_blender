import bpy
import importlib
from . import yf_lib


def get_current_selected_armature(self):
    selected_objects = yf_lib.get_selected_objects()
    if len(selected_objects) > 1:
        self.report({"ERROR"}, "ONLY one armature at a time!")
        return None
    if len(selected_objects) == 0:
        self.report({"ERROR"}, "Select at least ONE armature")
        return None
    obj_ = selected_objects[-1]
    if not obj_ or obj_.type != 'ARMATURE':
        self.report({"ERROR"}, "No armature is selected!")
        return None
    return obj_

def get_n_panel_region(context):
    for area in context.screen.areas:
        # Check if the area type is the 3D Viewport
        if area.type == 'VIEW_3D':
            # Iterate over the regions in the 3D Viewport area
            for region in area.regions:
                # Look for the region of type 'UI', which is the N-panel
                if region.type == 'UI':
                    return region
    return None

class YfToolbox_Operator_LinkDEF2TGT(bpy.types.Operator):
    bl_idname = "yf.toolbox_rigging_op_link_tgt_to_def"
    bl_label = "DEF -> TGT"
    CONSTRAINT_NAME = "COPY XFORM DEF->TGT"

    @classmethod
    def description(cls, context, properties):
        return "Create Target(TGT) bones for Deform(DEF) bones, then add \"Copy Transform\" constraint on it"

    def execute(self, context):
        obj_ = get_current_selected_armature(self)
        if not obj_:
            return {"FINISHED"}
        
        armature_ = obj_.data # type: bpy.types.Armature
        pose_ = obj_.pose

        start_mode = yf_lib.get_active_object_interaction_mode()
        # Enter EDIT mode if not
        if start_mode != 'EDIT':
            yf_lib.set_active_object_interaction_mode('EDIT')
        

        def get_TGT_bone(_DEF_bone):
            if _DEF_bone.name == "ROOT":
                return None
            _TGT_bone_name = 'TGT_' + _DEF_bone.name[4:]
            _TGT_bone = armature_.edit_bones.get(_TGT_bone_name)
            if not _TGT_bone:
                # Exisiting TGT is not found. Create the TGT
                _TGT_bone = armature_.edit_bones.new('TGT_' + bone.name[4:])
                # Change the name prefix from 'DEF_' to 'TGT_'
                _TGT_bone.head = _DEF_bone.head
                _TGT_bone.tail = _DEF_bone.tail
                _TGT_bone.roll = _DEF_bone.roll
                if _DEF_bone.parent:
                    _TGT_parent_bone = get_TGT_bone(_DEF_bone.parent)
                    _TGT_bone.parent = _TGT_parent_bone
            return _TGT_bone

        for bone in armature_.edit_bones:
            if bone.name.startswith('DEF_'):
                new_bone = get_TGT_bone(bone)

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

class YfToolbox_Operator_CleanUp(bpy.types.Operator):
    bl_idname = "yf.toolbox_rigging_clean_up"
    bl_label = "CLEAN UP"

    @classmethod
    def description(cls, context, properties):
        return """This operator will do following tasks:
        1) Assign bones to collections (create if non-exist) by their prefix.
        2) Assign each collection a color by order.
        3) Set DEF bones to use "deform".
        4) Lock DEF bones' transformation, since they are dirven by TGT bones"""

    def execute(self, context):
        obj_ = get_current_selected_armature(self)
        if not obj_:
            return {"FINISHED"}
        
        armature_ = obj_.data # type: bpy.types.Armature
        pose_ = obj_.pose 
        
        start_mode = yf_lib.get_active_object_interaction_mode()
        # Enter EDIT mode if not
        if start_mode != 'EDIT':
            yf_lib.set_active_object_interaction_mode('EDIT')

        all_collections = yf_lib.get_all_collections(armature_)
        for bone in armature_.edit_bones:
            for collection_ in all_collections:
                collection_.unassign(bone)

        if armature_.collections:
            bpy.ops.armature.collection_remove_unused()

        CHILD_DEPTH = 1
        LEFT_SUFFIX = ".L"
        RIGHT_SUFFIX = ".R"
        for bone in armature_.edit_bones:
            bone_name_splitted = bone.name.split("_")
            bcoll_root_name = bone_name_splitted[0]
            
            bcoll_root = armature_.collections.get(bcoll_root_name)
            if not bcoll_root:
                bcoll_root = armature_.collections.new(bcoll_root_name)
            bcoll_root.assign(bone)

            if len(bone_name_splitted) >= 2:
                for bcoll_child_name in bone_name_splitted[1:1+CHILD_DEPTH]:
                    if bone.name.endswith(LEFT_SUFFIX) or bone.name.endswith(RIGHT_SUFFIX):
                        if "." in bcoll_child_name:
                            bcoll_child_name = bcoll_child_name[0:bcoll_child_name.index(".")]
                        direction = "L" if bone.name.endswith(LEFT_SUFFIX) else "R"
                        bcoll_child_name = f"{bcoll_child_name} - {direction}"

                    bcoll_child_name = f"({bcoll_root_name}) {bcoll_child_name}"
                    bcoll_child = bcoll_root.children.get(bcoll_child_name)
                    if not bcoll_child:
                        bcoll_child = armature_.collections.new(bcoll_child_name, parent=bcoll_root)
                    bcoll_child.assign(bone)

        # SORT ALL COLLECTION
        for bcoll in armature_.collections:
            i_ = 0
            while i_ < len(bcoll.children):
                j_ = i_ + 1
                while j_ < len(bcoll.children):
                    if bcoll.children[i_].name > bcoll.children[j_].name:
                        bcoll.children[j_].child_number=i_
                    j_ += 1
                i_ += 1

        # Set all bones' color
        for bone in armature_.edit_bones:
            for collection in bone.collections:
                bm_data_color = "DEFAULT"
                if hasattr(collection, "bm_data"):
                    bm_data_color = collection.bm_data.editColor
                if bm_data_color == "DEFAULT" or bone.color.palette != bm_data_color:
                    i_ = armature_.collections.find(collection.name) + 1
                    if i_ == 0: 
                        continue
                    bone.color.palette = f"THEME{i_:02d}"
                    if hasattr(collection, "bm_data"):
                        collection.bm_data.editColor = f"THEME{i_:02d}"
                        collection.bm_data.poseColor = f"DEFAULT"

        # Set obly DEF bone use deform
        for bone in armature_.edit_bones:
            if bone.name.startswith("DEF_"):
                bone.hide_select = True
            else:
                bone.use_deform = False
        
        # Set DEF bone lock transform
        for bone in pose_.bones:
            if bone.name.startswith("DEF_"):
                bone.lock_location = (True, True, True)
                bone.lock_rotation = (True, True, True)
                bone.lock_scale = (True, True, True)
            else:
                pass
        
        yf_lib.set_active_object_interaction_mode(start_mode)
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
                         text="TGT -> DEF",
                         icon="DECORATE_LINKED")
        row = layout.row()
        row.operator("yf.toolbox_rigging_clean_up",
                         text="CLEAN UP",
                         icon="BRUSH_DATA")
        


def register():
    bpy.utils.register_class(YfToolbox_Panel_Rigging)
    bpy.utils.register_class(YfToolbox_Operator_LinkDEF2TGT)
    bpy.utils.register_class(YfToolbox_Operator_CleanUp)

def unregister():
    bpy.utils.unregister_class(YfToolbox_Panel_Rigging)
    bpy.utils.unregister_class(YfToolbox_Operator_LinkDEF2TGT)
    bpy.utils.unregister_class(YfToolbox_Operator_CleanUp)

