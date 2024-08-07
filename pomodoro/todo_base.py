import bpy

# Define a property group for the to-do list items
class ToDoItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Task Name", default="")
    done: bpy.props.BoolProperty(name="Done", default=False)

# Define the UIList class to display the to-do items
class OBJECT_UL_todo_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        # We could write some code to decide which icon to use here...
        # custom_icon = 'OBJECT_DATAMODE' if item.done else 'OBJECT_DATA'
        custom_icon = 'CHECKBOX_HLT' if item.done else 'CHECKBOX_DEHLT'
        layout.prop(item, "done", text="")
        layout.prop(item, "name", text="", emboss=False)

class OBJECT_OT_add_todo_item(bpy.types.Operator):
    bl_idname = "object.add_todo_item"
    bl_label = "Add To-Do Item"
    
    def execute(self, context):
        new_item = context.scene.todo_list.add()
        new_item.name = "New Task"
        context.scene.todo_index = len(context.scene.todo_list) - 1
        return {'FINISHED'}

# Define the operator to remove a to-do item
class OBJECT_OT_remove_todo_item(bpy.types.Operator):
    bl_idname = "object.remove_todo_item"
    bl_label = "Remove To-Do Item"
    
    @classmethod
    def poll(cls, context):
        return context.scene.todo_list

    def execute(self, context):
        todo_list = context.scene.todo_list
        index = context.scene.todo_index

        todo_list.remove(index)
        context.scene.todo_index = min(max(0, index - 1), len(todo_list) - 1)
        return {'FINISHED'}

class OBJECT_PT_todo_list(bpy.types.Panel):
    bl_label = "To-Do List"
    bl_idname = "OBJECT_PT_todo_list"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    bl_parent_id = "yf.pomodoro_main_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        row = layout.row()
        layout.template_list("OBJECT_UL_todo_list", "", scene, "todo_list", scene, "todo_index")
        row = layout.row(align=True)
        row.operator("object.add_todo_item", icon='ADD', text="")
        row.operator("object.remove_todo_item", icon='REMOVE', text="")
        
def register():
    bpy.utils.register_class(ToDoItem)
    bpy.types.Scene.todo_list = bpy.props.CollectionProperty(type=ToDoItem)
    bpy.types.Scene.todo_index = bpy.props.IntProperty(name="To-Do Index", default=0)
    bpy.utils.register_class(OBJECT_UL_todo_list)
    bpy.utils.register_class(OBJECT_OT_add_todo_item)
    bpy.utils.register_class(OBJECT_OT_remove_todo_item)
    bpy.utils.register_class(OBJECT_PT_todo_list)
    
def unregister():
    del bpy.types.Scene.todo_list
    del bpy.types.Scene.todo_index
    bpy.utils.unregister_class(ToDoItem)
    bpy.utils.unregister_class(OBJECT_UL_todo_list)
    bpy.utils.unregister_class(OBJECT_OT_add_todo_item)
    bpy.utils.unregister_class(OBJECT_OT_remove_todo_item)
    bpy.utils.unregister_class(OBJECT_PT_todo_list)