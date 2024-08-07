bl_info = {
    "name": "Yf's Easy Timelapse",
    "blender": (2, 80, 0),
    "category": "3D View",
    "version": (1, 0, 0),
    "description": "XXOO",
}
import bpy, os, time

custom_icons= None

def get_blend_file_name():
    file_path = bpy.data.filepath
    file_name = os.path.basename(file_path)


def get_image_folder():
    file_path = bpy.data.filepath
    file_name = get_blend_file_name()
    return os.path.join(os.path.dirname(file_path), "yf","timelapsy", file_name)


def get_blend_file_name():
    return os.path.basename(bpy.data.filepath)


def get_addon_filepath():
    return os.path.dirname(bpy.path.abspath(__file__)) + os.sep


def load_custom_icons():
    import bpy.utils.previews
    # Custom Icon
    if not hasattr(bpy.utils, 'previews'): return
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    folder = get_addon_filepath() + 'icons' + os.sep

    for f in os.listdir(folder):
        icon_name = f.replace('_icon.png', '')
        custom_icons.load(icon_name, folder + f, 'IMAGE')


class YfTimelapsyHeaderPopover(bpy.types.Panel):
    bl_label = ""
    bl_idname = "yf.timelapsy_header_popover"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        row = layout.row(align=True)
        row.prop(scene, "yf_timelapsy_screenshot_interval", text="Interval (sec)")
        row = layout.row(align=True)
        row.operator("yf.timelapsy_generate_video", text="Generate Video", icon="RESTRICT_RENDER_OFF")


class YfTimelapsyStartOperator(bpy.types.Operator):
    bl_label="Yf Timelapsy Start"
    bl_idname = "yf.timelapsy_start_op"
    def execute(self, context):
        scene = context.scene
        is_recording = scene.yf_timelapsy_is_recording
        scene.yf_timelapsy_is_recording = not scene.yf_timelapsy_is_recording
        if not is_recording:
            if not bpy.data.is_saved:
                bpy.ops.wm.save_mainfile("INVOKE_DEFAULT")
            bpy.app.timers.register(render_image)
        else:
            try:
                bpy.app.timers.unregister(render_image)
            except ValueError:
                # print("function is not registered yet")
                pass
        return {'FINISHED'}
    

class YfTimelapsyGenerateVideo(bpy.types.Operator):
    bl_idname = "yf.timelapsy_generate_video"
    bl_label = "Generate Timelapsy Video"
    bl_options = {'REGISTER', 'UNDO'}
    
    directory: bpy.props.StringProperty(name="Directory",description="Choose a directory",subtype='DIR_PATH')
    
    def execute(self, context):
        if not bpy.data.is_saved:
            return {'FINISHED'}
        # Print the selected directory to the console (for debugging)
        image_dir = get_image_folder()
        # print("[Timelapsy] Image dir: " + image_dir)
        output_filepath = os.path.join(self.directory, "Timelapsy_" + get_blend_file_name()+"_")

        # Get the list of PNG images in the directory
        image_files = sorted([f for f in os.listdir(image_dir) if f.endswith('.png')])
        # print(image_files)

        # Start a new scene or clear the current VSE
        
        old_scene = bpy.context.scene
        if 'Yf_Timelapsy' in bpy.data.scenes:
            temp_scene = bpy.data.scenes['Yf_Timelapsy']
        else:
            # Create a new scene
            bpy.ops.scene.new(type='NEW')
            # Get the newly created scene
            temp_scene = bpy.context.scene
            # Optionally set the name of the new scene
            temp_scene.name = "Yf_Timelapsy"
        
        temp_scene.sequence_editor_clear()

        # Set the render resolution, frame rate, and other settings
        bpy.context.scene.render.resolution_x = 1920
        bpy.context.scene.render.resolution_y = 1080
        bpy.context.scene.render.fps = 30

        # Set the render output format to FFmpeg video
        bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
        bpy.context.scene.render.ffmpeg.format = 'MPEG4'
        bpy.context.scene.render.ffmpeg.codec = 'H264'
        bpy.context.scene.render.ffmpeg.video_bitrate = 8000
        bpy.context.scene.render.ffmpeg.minrate = 0
        bpy.context.scene.render.ffmpeg.maxrate = 9000

        # Set the output filepath
        bpy.context.scene.render.filepath = output_filepath

        # Create a new video sequence editor (VSE) context
        if not temp_scene.sequence_editor:
            temp_scene.sequence_editor_create()

        # Change context to the Video Sequence Editor
        old_area_type = bpy.context.area.type
        bpy.context.area.type = 'SEQUENCE_EDITOR'

        # Add the image sequence strip to the VSE
        bpy.ops.sequencer.image_strip_add(
            directory=image_dir,
            files=[{"name": f} for f in image_files],
            relative_path=False,
            frame_start=1
        )

        # Set the end frame to match the length of the image sequence
        bpy.context.scene.frame_end = len(image_files)

        # Render the animation to create the video
        bpy.ops.render.render(animation=True)
        
        bpy.context.window.scene = old_scene
        bpy.context.area.type = old_area_type
        self.report({"INFO"}, f"The Video is saved to {output_filepath}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        if not bpy.data.is_saved:
            self.report({'ERROR'}, "Blender file not saved.")
            return {'CANCELLED'}
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        



def draw_menu(self, context):
    layout = self.layout
    c = layout.column()
    b = c.box()
    scene = context.scene
    is_recording = scene.yf_timelapsy_is_recording
    r = b.row(align=True)
    # r.label()
    r.operator("yf.timelapsy_start_op",icon_value=custom_icons["idle" if not is_recording else "recording"].icon_id, text="")
    r.popover("yf.timelapsy_header_popover")


# Set the interval in seconds
def render_image():
    if not bpy.data.is_saved or not bpy.types.Scene.yf_timelapsy_is_recording:
        return 0.0
    images_folder_path = get_image_folder()
    
    if not os.path.exists(images_folder_path):
        os.makedirs(images_folder_path)

    bpy.context.scene.yf_timelapsy_cur_screenshot_num += 1
    num = bpy.context.scene.yf_timelapsy_cur_screenshot_num
    interval = bpy.context.scene.yf_timelapsy_screenshot_interval

    # Extract the file name from the filepath
    file_name = get_blend_file_name()
    output_file_path = os.path.join(images_folder_path, f"{file_name}_screenshot_{num}.png")

    # Execute the screenshot operator
    bpy.ops.screen.screenshot(filepath=output_file_path, check_existing=False)
    # print("[Timelapsy] Take screenshot " + time.asctime())
    return interval

from bpy.app.handlers import persistent
@persistent
def yf_timelapsy_on_file_read(dummy):
    # print("[Timelapsy] New File is read")
    if bpy.context.scene.yf_timelapsy_is_recording:
        bpy.app.timers.register(render_image)
    # Get the max index of image and update
    image_dir = get_image_folder()
    # Get the list of PNG images in the directory
    image_files = sorted([f for f in os.listdir(image_dir) if f.endswith('.png')])
    if len(image_files) == 0:
        bpy.context.scene.yf_timelapsy_cur_screenshot_num = 1
    else:
        bpy.context.scene.yf_timelapsy_cur_screenshot_num = int(image_files[-1].split('_')[-1].split('.')[0])

def register():
    custom_icons = None
    load_custom_icons()

    bpy.types.VIEW3D_MT_editor_menus.append(draw_menu)
    bpy.types.Scene.yf_timelapsy_cur_screenshot_num = bpy.props.IntProperty(default=0)
    bpy.types.Scene.yf_timelapsy_is_recording = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.yf_timelapsy_screenshot_interval = bpy.props.IntProperty(default=10, min=1)
    bpy.utils.register_class(YfTimelapsyStartOperator)
    bpy.utils.register_class(YfTimelapsyHeaderPopover)
    bpy.utils.register_class(YfTimelapsyGenerateVideo)
    
    bpy.app.handlers.load_post.append(yf_timelapsy_on_file_read)
    
    


def unregister():
    # print("[Timelapsy] unregister")
    bpy.utils.unregister_class(YfTimelapsyHeaderPopover)
    bpy.utils.unregister_class(YfTimelapsyStartOperator)
    bpy.utils.unregister_class(YfTimelapsyGenerateVideo)
    
    bpy.types.VIEW3D_MT_editor_menus.remove(draw_menu)

    if yf_timelapsy_on_file_read in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(yf_timelapsy_on_file_read)
    
