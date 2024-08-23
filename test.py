import bpy
import string
import random
import re
from pprint import pprint


def generate_random_string(length=6):
    # Define the characters to use (digits and letters)
    characters = string.ascii_letters + string.digits
    # Generate a random string of the specified length
    random_string = ''.join(random.choices(characters, k=length))
    return random_string

def get_constraint_code(_name):
    pattern = r"yf\[(.+)\]"
    match = re.match(pattern, _name.split('_')[-1])
    if match:
        return match.group(1)
    return None

def shorten_cname(cname, total_length=63, min_length=11):
    # Calculate the available space for cname
    available_space = total_length - min_length
    # Check if the length of cname needs to be shortened
    if len(cname) > available_space:
        # Calculate the maximum allowed length for the shortened cname
        max_length_for_cname = available_space - 3  # Subtracting 3 for the "..."
        # Calculate the amount to keep from the beginning and end
        start_length = (max_length_for_cname - 2) // 2  # -2 for balanced truncation
        end_length = start_length
        # Shorten the cname and insert "..."
        cname = cname[:start_length] + "..." + cname[-end_length:]
    return cname

def copy_constraint_attributes(source_bone, source_constraint, target_bone, target_constraint, symmetrize=False):
    # List of attributes to exclude (Blender internal or special attributes)
    exclude_attrs = {'rna_type', 'bl_rna', 'name', 'type', 'is_valid'}
    
    # Get all attributes of the source constraint
    for attr in dir(source_constraint):
        if attr.startswith("__") or attr in exclude_attrs:
            continue
        # Get the value of the attribute from the source constraint
        value = getattr(source_constraint, attr)
        # Try to set the value on the target constraint
        try:
            setattr(target_constraint, attr, value)
        except AttributeError:
            # print(f"Cannot set attribute '{attr}'")
            pass

    for fcurve in armature.animation_data.drivers:
        if fcurve.data_path.startswith(f'pose.bones["{source_bone.name}"].constraints["{source_constraint.name}"]'):
            # Symmetrize the driver data path
            new_data_path = fcurve.data_path.replace(source_bone.name, target_bone.name)
            new_data_path = symmetrize_name(new_data_path) if symmetrize else new_data_path
            # Create a new driver for the target constraint

            new_fcurve = armature.animation_data.drivers.find(new_data_path, index=fcurve.array_index)
            if not new_fcurve:
                print("no this fcurve, create!")
                new_fcurve = armature.animation_data.drivers.new(data_path=new_data_path, index=fcurve.array_index)
            new_fcurve.driver.type = fcurve.driver.type


            # Copy and symmetrize driver variables
            for var in fcurve.driver.variables:
                new_var = None
                for _ in new_fcurve.driver.variables:
                    if _.name == var.name and _.type == var.type:
                        new_var = _
                if not new_var:
                    new_var = new_fcurve.driver.variables.new()
                new_var.name = var.name
                new_var.type = var.type
                for i, target in enumerate(var.targets):
                    for attr in dir(target):
                        if attr not in ['__doc__', '__module__', '__slots__', 'bl_rna',  'fallback_value', 'id_type', 'is_fallback_used', 'rna_type', 'use_fallback_value']:
                            value = getattr(target, attr)
                            setattr(new_var.targets[i], attr, symmetrize_name(value) if symmetrize else value)
                    # new_var.targets[i].id = target.id
                    # new_var.targets[i].data_path = symmetrize_name(target.data_path) if symmetrize else target.data_path
                    # new_var.targets[i].bone_target = symmetrize_name(target.bone_target) if symmetrize else target.bone_target
                    # new_var.targets

            # Handle scripted expressions specifically
            if fcurve.driver.type == 'SCRIPTED':
                new_fcurve.driver.expression = symmetrize_name(fcurve.driver.expression) if symmetrize else fcurve.driver.expression
                print(fcurve.driver.expression)

        fcurve.update()

def get_constraint_properties(constraint):
    prop_dict = {}
    for prop in dir(constraint):
        if not prop.startswith("__") and not callable(getattr(constraint, prop)):
            prop_dict[prop] = getattr(constraint, prop)
    return prop_dict

def symmetrize_name(name):
    if not name:
        return name
    
    if '.L' in name:
        return name.replace('.L', '.R')
    elif '.R' in name:
        return name.replace('.R', '.L')
    return name

def copy_constraint_with_driver():
    armature = bpy.context.object

    selected_bones = bpy.context.selected_pose_bones
    armature = bpy.context.object
    if armature.type != 'ARMATURE':
        print("No armature selected.")

    if len(selected_bones) < 2:
        print("Select at least 2 bones.")

    source_bone = selected_bones[0]
    for target_bone in selected_bones[1:]:
        for source_constraint in source_bone.constraints:
            cname, ccode = source_constraint.name, get_constraint_code(source_constraint.name)
            
            if not ccode:
                cname, ccode = source_constraint.name, generate_random_string(length=9)
                cname = shorten_cname(cname, min_length=len(ccode)+len("_yf[]"))
                source_constraint.name = f"{cname}_yf[{ccode}]"
            # pprint(get_constraint_properties(source_constraint))
            if cname not in target_bone.constraints:
                target_bone.constraints.copy(source_constraint)
            
            copy_constraint_attributes(source_bone, source_constraint, target_bone, target_bone.constraints[cname], symmetrize=)
            