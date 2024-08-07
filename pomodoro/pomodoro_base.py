import bpy
from . import todo_base
from .util_funcs import *

BLINKING_INTERVAL = 0.25

class YfPomodoroSettings(bpy.types.PropertyGroup):
    long_break_interval: bpy.props.IntProperty(default=4,min=0, soft_max=15)
    pomodoro_length: bpy.props.IntProperty(default=25, min=1, update=callback_change_settings)
    short_break_length: bpy.props.IntProperty(default=5, min=1, update=callback_change_settings)
    long_break_length: bpy.props.IntProperty(default=15, min=1, update=callback_change_settings)

class YfPomodoroSettingsPanel(bpy.types.Panel):
    bl_label = "Settings"
    bl_idname = "yf.pomodoro_settings_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'YF'
    bl_parent_id = "yf.pomodoro_main_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.yf_pomodoro_settings
        
        row = layout.row()
        row.alignment = "LEFT"
        col = layout.column()
        col.prop(settings, "long_break_interval", text="Long Break Interval")
        col.prop(settings, "pomodoro_length", text="Pomodoro (mins)")
        col.prop(settings, "short_break_length", text="Short Break (mins)")
        col.prop(settings, "long_break_length", text="Long Break (mins)")
    
class YfPomodoroProperties(bpy.types.PropertyGroup):
    completed_count: bpy.props.IntProperty(default=0)
    short_break_count: bpy.props.IntProperty(default=0)
    cur_time: bpy.props.FloatProperty(default=25*60, update=ui_force_redraw_callback)
    is_running: bpy.props.BoolProperty(update=ui_force_redraw_callback)
    is_blinking: bpy.props.BoolProperty(update=ui_force_redraw_callback)

class YfPomodoroPanel(bpy.types.Panel):
    bl_idname = "yf.pomodoro_main_panel"
    bl_label = "POMODORO"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "YF"

    def draw(self, context):
        # You can set the property values that should be used when the user
        # presses the button in the UI.
        layout = self.layout
        scene = context.scene
        props = scene.yf_pomodoro_props
        settings = scene.yf_pomodoro_settings

        hrs, mins, secs = convert_seconds(props.cur_time)   

        row = layout.row()
        row.alignment = "CENTER"
        stage = get_current_stage(props.completed_count, txt=True)
        row.label(icon_value=custom_icons["tomato"].icon_id,text=f"#{props.completed_count//2} " + stage)

        row = layout.row()
        row.alignment = "CENTER"
        b0 = row.box()
        r = b0.row(align=True)

        for i,n in enumerate([mins, secs]):
            digits = number_to_digits(n)
            r.label(icon_value=custom_icons[f"num_{number_to_word(digits[0])}"].icon_id)
            r.label(icon_value=custom_icons[f"num_{number_to_word(digits[1])}"].icon_id)
            if i == 0:
                r.label(icon_value=custom_icons["colon"].icon_id)
        
        row = layout.row(align=True)
        row.alignment = "CENTER"
        if not props.cur_time == 0:
            row.operator("yf.start_op",
                         text="",
                         icon="PLAY" if not props.is_running else "PAUSE")
        row.operator("yf.skip_op", text="", icon="FF")
        row.operator("yf.reset_op", text="", icon="CANCEL")
        
        row = layout.row()
        
class StartOperator(bpy.types.Operator):
    bl_idname = "yf.start_op"
    bl_label = "Yf Start Op"
    def execute(self, context):
        scene = context.scene
        props = scene.yf_pomodoro_props
        if not props.is_running:
            start_counting()
        else:
            stop_counting()
        return {'FINISHED'}
    
class SkipOperator(bpy.types.Operator):
    bl_idname = "yf.skip_op"
    bl_label = ""
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        scene = context.scene
        props = scene.yf_pomodoro_props
        if get_current_stage(props.completed_count):
            props.short_break_count += 1
        props.completed_count += 1
        bpy.ops.yf.reset_op()
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.yf_pomodoro_props

        layout.label(text="SKIP?" if props.cur_time > 0 else "NEXT?")
        pass

class ResetOperator(bpy.types.Operator):
    """Really?"""
    bl_idname = "yf.reset_op"
    bl_label = "RESET this pomodoro?"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        scene = context.scene
        props = scene.yf_pomodoro_props
        settings = scene.yf_pomodoro_settings
        
        stop_counting()
        stop_blinking()

        stg = get_current_stage(props.completed_count)
        if stg==1 and props.short_break_count >= settings.long_break_interval+1:
            props.short_break_count = 0
            stg = 2
        
        t = (settings.pomodoro_length if stg == 0 
             else settings.short_break_length if stg == 1
             else settings.long_break_length) * 60 # seconds
        
        props.cur_time = t
        stop_counting()
        stop_blinking()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        pass  

def counting():
    print("counting")
    try:
        props = bpy.context.scene.yf_pomodoro_props
        props.cur_time -= 1.0
        if props.cur_time <= 0:
            props.cur_time = 0
            start_blinking()
            stop_counting()
            return 0.0
    except AttributeError:
        return 1.0
    return 1.0

def start_counting():
    bpy.app.timers.register(counting, first_interval=1.0)
    props = bpy.context.scene.yf_pomodoro_props
    props.is_running = True

def stop_counting():
    props = bpy.context.scene.yf_pomodoro_props
    props.is_running = False
    try:
        bpy.app.timers.unregister(counting)
    except ValueError:
        pass

def blinking():
    props = bpy.context.scene.yf_pomodoro_props
    props.is_blinking = not props.is_blinking
    return BLINKING_INTERVAL

def start_blinking():
    bpy.app.timers.register(blinking)

def stop_blinking():
    try:
        props = bpy.context.scene.yf_pomodoro_props
        props.is_blinking = False
        bpy.app.timers.unregister(blinking)
    except ValueError:
        pass

class YfPomodoroHeaderPopover(bpy.types.Panel):
    bl_label = ""
    bl_idname = "yf.pomodoro_header_popover"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.yf_pomodoro_props
        row = layout.row(align=True)
        row.alignment = "CENTER"
        if not props.cur_time == 0:
            row.operator("yf.start_op",
                         text="",
                         icon="PLAY" if not props.is_running else "PAUSE")
        row.operator("yf.skip_op", text="", icon="FF")
        row.operator("yf.reset_op", text="", icon="CANCEL")
        
def register():
    bpy.utils.register_class(YfPomodoroSettings)
    bpy.utils.register_class(YfPomodoroProperties)
    bpy.types.Scene.yf_pomodoro_props = bpy.props.PointerProperty(type=YfPomodoroProperties)
    bpy.types.Scene.yf_pomodoro_settings = bpy.props.PointerProperty(type=YfPomodoroSettings)
    bpy.utils.register_class(YfPomodoroPanel)
    bpy.utils.register_class(StartOperator)
    bpy.utils.register_class(SkipOperator)
    bpy.utils.register_class(ResetOperator)
    bpy.utils.register_class(YfPomodoroSettingsPanel)
    bpy.utils.register_class(YfPomodoroHeaderPopover)

def unregister():
    bpy.utils.unregister_class(YfPomodoroPanel)
    bpy.utils.unregister_class(StartOperator)
    bpy.utils.unregister_class(SkipOperator)
    bpy.utils.unregister_class(ResetOperator)
    bpy.utils.unregister_class(YfPomodoroSettings)
    bpy.utils.unregister_class(YfPomodoroProperties)
    bpy.utils.unregister_class(YfPomodoroSettingsPanel)
    bpy.utils.unregister_class(YfPomodoroHeaderPopover)
