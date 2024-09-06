import bpy
import re
from .. import __package__ as base_package

class YfToolbox_Operator_AddCopyXformConstraintDEFToORG(bpy.types.Operator):
    bl_idname = "yf.toolbox_rigging_op_def_to_org"
    bl_label = "Add \"Copy Transfor\" DEF to ORG "
    CONSTRAINT_NAME = "COPY XFORM DEF->TGT"

    @classmethod
    def description(cls, context, properties):
        return "Create Target(ORG) bones for Deform(DEF) bones, then add \"Copy Transform\" constraint on it"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == "ARMATURE"

    def execute(self, context):
        arm = bpy.context.active_object
        bones = arm.pose.bones
        edit_bones = arm.data.edit_bones

        start_mode = bpy.context.object.mode

        bpy.ops.object.mode_set(mode='EDIT')
        for bone in edit_bones:
            def_name = bone.name
            match = re.match(r'^(DEF_)(.*?)$', def_name)
            # if match found
            if match:
                #get pose bone by name
                def_bone = arm.pose.bones.get(def_name)
                #match group 1 is DEF. (from regex expression above)
                prefix = match.group(1)
                #match group 2 is everything else (from regex expression above)
                basename = match.group(2)
                org_name = f'ORG_{basename}'

            if not edit_bones.get(org_name):
                org_bone = arm.data.edit_bones.new(org_name)
                def_bone = arm.data.edit_bones.get(def_name)
                # Copy properties from the original bone
                org_bone.head = def_bone.head
                org_bone.tail = def_bone.tail
                org_bone.roll = def_bone.roll
                org_bone.use_connect = def_bone.use_connect
                org_bone.parent = def_bone.parent

        bpy.ops.object.mode_set(mode='POSE')
        # cycles through all pose bones
        for bone in bones:
            def_name = bone.name
            match = re.match(r'^(DEF_)(.*?)$', def_name)
            
            # if match found
            if match:
                #get pose bone by name
                def_bone = arm.pose.bones.get(def_name)
                #match group 1 is DEF. (from regex expression above)
                prefix = match.group(1)
                #match group 2 is everything else (from regex expression above)
                basename = match.group(2)
                #assemble target name by adding ORG. to the basename
                org_name = f'ORG_{basename}'
                #add copy tranforms constraint if it does
                constraint = def_bone.constraints.new('COPY_TRANSFORMS')
                #set the contraint target to be the armature
                constraint.target = arm
                #set the constraint subtarget (Bone) to be the target bone
                constraint.subtarget = org_name
            
        bpy.ops.object.mode_set(mode=start_mode)
        return {'FINISHED'}
    
class YfToolbox_Operator_AutoBoneCollections(bpy.types.Operator):
    bl_idname = "yf.toolbox_rigging_op_auto_bone_collections"
    bl_label = "Yf Auto Bone Collections"
    @classmethod
    def description(cls, context, properties):
        return "Automaticly assign bones to a bone collection by its prefix"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == "ARMATURE" and context.mode == "EDIT_ARMATURE"

    def execute(self, context):
        prefs = context.preferences.addons[base_package].preferences
        
        NAME_ROOT = prefs.prefix_root
        NAME_DEF = prefs.prefix_def

        arm = context.object.data
        self.remove_all_bcolls()

        ## PARSE ALL BONES
        _d = {}
        for bone in arm.edit_bones:
            bone.use_deform = False
            bname = self.parse_bone_name(bone.name)
            if bname:
                ## CREATE BONE COLLECTIONS
                _d.setdefault(bname.group, []).append(bone)
                ## PROP
                if bname.prop:
                    _d.setdefault(f"* {bname.prop}", []).append(bone)

            if not bname:
                # TODO: send warning
                if bone.name == NAME_ROOT:
                    _d[f"> {NAME_ROOT}"] = [bone]
        
        if NAME_DEF in _d.keys():
            for _b in _d[NAME_DEF]:
                _b.use_deform = True

        ## CREATE BONE COLLECTIONS
        for k in sorted(_d.keys()):
            for bone in _d[k]:
                self.get_bcoll(k).assign(bone)
        return {"FINISHED"}

    class BoneName:
        def __init__(self, _prefix, _name, _prop, _direction) -> None:
            self.prefix = _prefix
            self.name = _name
            self.prop = _prop
            self.direction = _direction

        @property
        def group(self):
            return self.prefix.split("-")[0]
        
        def __str__(self):
            return f'{self.prefix}_{self.name}{("_"+self.prop) if self.prop else ""}{("."+self.direction) if self.direction else ""}'

    def remove_all_bcolls(self):
        arm = bpy.context.object.data
        while arm.collections:
            for c in [_ for _ in arm.collections]:
                arm.collections.remove(c)

    def get_bcoll(self, name):
        arm = bpy.context.object.data
        bcoll = arm.collections.get(name)
        if not bcoll:
            bcoll = arm.collections.new(name)
        return bcoll
    
    def parse_bone_name(self, bone_name):
        pattern = r'^(?P<prefix>[^_]+)_(?P<name>[^\._]+)?(?:_(?P<prop>[^\._]+))?(?:\.(?P<direction>[^\.]+))?$'
        match = re.match(pattern, bone_name)
        if match:
            prefix = match.group('prefix')
            name = match.group('name')
            prop = match.group('prop')
            direction = match.group('direction')
            return self.BoneName(prefix, name, prop, direction)
        return None

class YfToolbox_Operator_CopyConstraintWithDrivers(bpy.types.Operator):
    bl_idname = "yf.toolbox_rigging_op_copy_constraints_with_drivers"
    bl_label = "Copy Constraint With Drivers"

    @classmethod
    def description(cls, context, properties):
        return "Do normal copy constraint and also copy drivers."

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == "ARMATURE" and bpy.context.mode == 'POSE'

    def execute(self, context):
        scene = context.scene
        props = scene.yf_rigging_prop_grp
        use_symmetry = props.copy_constraint_use_symmetry

        # Get the active object (assumed to be an armature)
        armature = bpy.context.active_object
        # Get selected bones in pose mode
        selected_bones = bpy.context.selected_pose_bones

        # Ensure there are at least two bones selected
        if len(selected_bones) <= 1:
            self.report({"ERROR"}, "Please select at least two bones.")
            return {'FINISHED'}
        
        # The last selected bone is the active one and will be the source of constraints and drivers
        source_bone = bpy.context.active_pose_bone
        
        # Iterate over the other selected bones
        for target_bone in selected_bones:
            if target_bone == source_bone:
                continue
            
            # Copy constraints
            for constraint in source_bone.constraints:
                # Generate a unique name for the constraint
                constraint_name = self.generate_constraint_name(source_bone, constraint)
                # Check if the constraint with this name already exists on the target bone
                existing_constraint = self.find_existing_constraint(target_bone, constraint_name)
                
                if existing_constraint:
                    # print(f"Constraint '{constraint_name}' already exists on bone '{target_bone.name}', updating it.")
                    new_constraint = existing_constraint
                else:
                    # print(f"Creating new constraint '{constraint_name}' on bone '{target_bone.name}'.")
                    new_constraint = target_bone.constraints.new(type=constraint.type)
                    new_constraint.name = constraint_name

                # Copy properties from the source constraint
                for attr in dir(constraint):
                    if attr.startswith("_") or attr in {'rna_type', 'bl_rna', 'name', 'type'}:
                        continue
                    
                    # Skip setting driver attributes
                    if "driver" in attr:
                        continue

                    try:
                        setattr(new_constraint, attr, getattr(constraint, attr))
                    except AttributeError:
                        pass  # Ignore attributes that cannot be copied directly

                # Copy the drivers for the new constraint
                # self.copy_drivers_for_constraint(armature, source_bone.name, target_bone.name, constraint.name, new_constraint.name, use_symmetry)
            print(f"Copied {'and symmetrized' if use_symmetry else ''} constraints and drivers from bone '{source_bone.name}' to bone '{target_bone.name}'.")

        return {"FINISHED"}

    # Function to symmetrize names, data paths, and expressions
    def symmetrize_name(self, name, do=False):
        if do:
            if '.L' in name:
                return name.replace('.L', '.R')
            elif '.R' in name:
                return name.replace('.R', '.L')
        return name

    # Generate a unique name for the constraint based on source bone and constraint type
    def generate_constraint_name(self, source_bone, constraint):
        return f"{constraint.type}_from_{source_bone.name}"
    
    # Function to find an existing constraint by name
    def find_existing_constraint(self, target_bone, constraint_name):
        for constraint in target_bone.constraints:
            if constraint.name == constraint_name:
                return constraint
        return None

    # Function to delete existing drivers and create new ones
    def copy_drivers_for_constraint(self, arm, source_bone_name, target_bone_name, source_constraint_name, target_constraint_name, symmetry=False):
        # Delete existing drivers for the target constraint
        """
        arr_mod = C.object.modifiers.new("Array", 'ARRAY')
        arr_mod.use_constant_offset = True
        fcurves = arr_mod.driver_add('constant_offset_displace', 1)
        """

        existing_drivers = [
            fcurve for fcurve in arm.animation_data.drivers
            if fcurve.data_path.startswith(f'pose.bones["{target_bone_name}"].constraints["{target_constraint_name}"]')
        ]
        for fcurve in existing_drivers:
            arm.animation_data.drivers.remove(fcurve)
        
        # TODO: use API to create driver
        # Copy the drivers from the source constraint to the target
        for fcurve in arm.animation_data.drivers:
            if fcurve.data_path.startswith(f'pose.bones["{source_bone_name}"].constraints["{source_constraint_name}"]'):
                new_data_path = self.symmetrize_name(fcurve.data_path.replace(source_bone_name, target_bone_name), symmetry)
                # Create a new driver for the target constraint
                try:
                    new_fcurve = arm.animation_data.drivers.new(data_path=new_data_path, index=fcurve.array_index)
                    new_fcurve.driver.type = fcurve.driver.type
                    new_fcurve.driver.expression = self.symmetrize_name(fcurve.driver.expression, symmetry)
                except RuntimeError:
                    continue

                # Copy and symmetrize driver variables
                for var in fcurve.driver.variables:
                    new_var = new_fcurve.driver.variables.new()
                    new_var.name = var.name
                    new_var.type = var.type
                    for i, target in enumerate(var.targets):
                        new_var.targets[i].id = target.id
                        new_var.targets[i].data_path = self.symmetrize_name(target.data_path, symmetry)
                        new_var.targets[i].bone_target = self.symmetrize_name(target.bone_target, symmetry)

                # Handle scripted expressions specifically
                if fcurve.driver.type == 'SCRIPTED':
                    new_fcurve.driver.expression = self.symmetrize_name(fcurve.driver.expression, symmetry)