import bpy
import importlib
from . import yf_lib
from pprint import pprint


LEFT_SUFFIX = ".L"
RIGHT_SUFFIX = ".R"


PREFIX_ROOT = "ROOT"
PREFIX_MCH = "MCH"
PREFIX_DEF = "DEF"
PREFIX_VIS = "VIS"
PREFIX_CTRL = "CTRL"
PREFIX_ORG = "ORG"

BPREFIXES = [PREFIX_ROOT, PREFIX_MCH, PREFIX_DEF, PREFIX_VIS, PREFIX_CTRL, PREFIX_ORG]

prefix_colors = {
    PREFIX_ROOT: "THEME02",
    PREFIX_MCH: "THEME03",
    PREFIX_DEF: "THEME04",
    PREFIX_ORG: "THEME05",
    PREFIX_VIS: "THEME06",
}


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

def remove_shorter_keys(d):
    # Sort keys by length in descending order
    sorted_keys = sorted(d, key=len, reverse=True)
    unique_dict = {}
    
    for key in sorted_keys:
        value = d[key]
        # Add the key-value pair to unique_dict if the value is not already in unique_dict
        if value not in unique_dict.values():
            unique_dict[key] = value
    
    return unique_dict

class YfToolbox_Operator_LinkDEF2TGT(bpy.types.Operator):
    bl_idname = "yf.toolbox_rigging_op_link_tgt_to_def"
    bl_label = "DEF -> ORG"
    CONSTRAINT_NAME = "COPY XFORM DEF->TGT"

    @classmethod
    def description(cls, context, properties):
        return "Create Target(ORG) bones for Deform(DEF) bones, then add \"Copy Transform\" constraint on it"

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
            if _DEF_bone.name == PREFIX_ROOT:
                return None
            _TGT_bone_name = PREFIX_ORG + _DEF_bone.name[4:]
            _TGT_bone = armature_.edit_bones.get(_TGT_bone_name)
            if not _TGT_bone:
                # Exisiting TGT is not found. Create the TGT
                _TGT_bone = armature_.edit_bones.new(PREFIX_ORG + bone.name[4:])
                # Change the name prefix from PREFIX_DEF to PREFIX_ORG
                _TGT_bone.head = _DEF_bone.head
                _TGT_bone.tail = _DEF_bone.tail
                _TGT_bone.roll = _DEF_bone.roll
                if _DEF_bone.parent:
                    _TGT_parent_bone = get_TGT_bone(_DEF_bone.parent)
                    _TGT_bone.parent = _TGT_parent_bone
            return _TGT_bone

        for bone in armature_.edit_bones:
            if bone.name.startswith(PREFIX_DEF):
                new_bone = get_TGT_bone(bone)

        yf_lib.set_active_object_interaction_mode('POSE')

        for bone in pose_.bones:
            # Check if the bone name starts with PREFIX_DEF
            if bone.name.startswith(PREFIX_DEF):
                # Construct the corresponding target bone name
                tgt_bone_name = PREFIX_ORG + bone.name[4:]
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

        all_collections = yf_lib.get_all_bcolls(armature_)

        # Use WHILE loop to clear all collections,
        # because when the parent collection is removed,
        # its child will not be removed with it.
        while armature_.collections:
            for _c in [_ for _ in armature_.collections]:
                armature_.collections.remove(_c)

        CHILD_DEPTH = 1

        # Figure out all bones' collection 
        dict_bcolls = {}
        for bone in armature_.edit_bones:
            bname_parts = bone.name.split("_")

            # Don't create hierarchy for bones having these prefixes
            if bname_parts[0] in [PREFIX_DEF, PREFIX_MCH, PREFIX_ORG, PREFIX_ROOT, PREFIX_VIS]:
                bname_parts = [bname_parts[0]] 

            for i in range(len(bname_parts)):
                part_ = bname_parts[i]
                if LEFT_SUFFIX in part_ or RIGHT_SUFFIX in part_:
                    # DEF_HAND.L will be put into DEF_HAND - L
                    # At the same time, DEF_HAND.L will also be put into DEF_HAND
                    dict_bcolls.setdefault("_".join(bname_parts[0:i] + [bname_parts[i].split(".")[0]]), []).append(bone)
                
                dict_bcolls.setdefault("_".join(bname_parts[0:i+1]), []).append(bone)
        # If DEF_HAND and DEF_HAND_PALM contains the same bones,
        # then the collection with longer name will be removed.
        dict_bcolls = remove_shorter_keys(dict_bcolls)

        def find_parent_collection(collection_name, all_collections):
            # Split the new collection name into parts based on underscores
            parts = collection_name.split("_")
            bcoll_names = {c_.name: c_ for c_ in all_collections}

            if collection_name.endswith(LEFT_SUFFIX) or collection_name.endswith(RIGHT_SUFFIX):
                parent_name = collection_name.removesuffix(LEFT_SUFFIX).removesuffix(RIGHT_SUFFIX)
                print(parent_name)
                if parent_name in bcoll_names:
                    return bcoll_names[parent_name]

            # Try to find a parent by gradually reducing the parts
            for i in range(len(parts)-1, 0, -1):
                parent_name = "_".join(parts[:i])
                if parent_name in bcoll_names:
                    return bcoll_names[parent_name]

            return None

        for k in sorted(dict_bcolls.keys()):
            v = dict_bcolls[k]
            if len(v) >= 1:
                # TODO: Wait for blender to fix children collections
                # bcoll_parent = find_parent_collection(k, yf_lib.get_all_bcolls(armature_))
                # bcoll = armature_.collections.new(k, parent=bcoll_parent)
                bcoll = armature_.collections.new(k.removeprefix(PREFIX_CTRL+"_"))
                for b_ in v:
                    bcoll.assign(b_)

        # Set all bones' color
        for k, v in dict_bcolls.items():
            collection = armature_.collections.get(k)
            if not collection:
                continue
            bm_data_color = "DEFAULT"
            if hasattr(collection, "bm_data"):
                bm_data_color = collection.bm_data.editColor
            if bm_data_color == "DEFAULT" or bone.color.palette != bm_data_color:
                color_ = "DEFAULT"
                for prefix_ in prefix_colors:
                    if prefix_ in k:
                        for bone_ in v:
                            bone_.color.palette = prefix_colors[prefix_]
                            color_ = prefix_colors[prefix_]

                if hasattr(collection, "bm_data"):
                    # collection.bm_data.editColor = f"THEME{i_:02d}"
                    collection.bm_data.editColor = color_
                    collection.bm_data.poseColor = f"DEFAULT"

        # Set only DEF bone use deform
        # Set 
        for bone in armature_.edit_bones:
            if bone.name.startswith(PREFIX_DEF) or \
                bone.name.startswith(PREFIX_VIS):
                bone.hide_select = True
                for bcoll in bone.collections:
                    if hasattr(bcoll, "bm_data"):
                        bcoll.bm_data.is_lock = True
            else:
                bone.use_deform = False
        
        # Set DEF bone lock transform
        for bone in pose_.bones:
            if bone.name.startswith(PREFIX_DEF):
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
                         text="ORG -> DEF",
                         icon="DECORATE_LINKED")
        row = layout.row()
        row.operator("yf.toolbox_rigging_clean_up",
                         text="CLEAN UP",
                         icon="BRUSH_DATA")
        

classes = (YfToolbox_Panel_Rigging, YfToolbox_Operator_LinkDEF2TGT, YfToolbox_Operator_CleanUp)

register, unregister = bpy.utils.register_classes_factory(classes)
