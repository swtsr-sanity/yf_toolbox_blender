import bpy
import os, time

def number_to_word(number):
    number_words = {
        0: "zero",
        1: "one",
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
        7: "seven",
        8: "eight",
        9: "nine"
    }
    
    return number_words.get(number, "Invalid number")

def convert_seconds(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    return (hours, minutes, remaining_seconds)

def number_to_digits(number):
    digits = []
    
    # Handle the case where the number is zero
    if number == 0:
        return [0,0]
    
    while number > 0:
        # Extract the last digit using modulus operator
        digit = number % 10
        digits.append(digit)
        # Remove the last digit using integer division
        number = number // 10
    
    # Since the digits are collected in reverse order, reverse them before returning
    while len(digits) < 2:
        digits.append(0)
    digits.reverse()

    return digits

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

def ui_force_redraw_callback(self, context):
    if context.area:
        for region in context.area.regions:
            if region.type == "UI":
                region.tag_redraw()
    return None

def callback_change_settings(self, context):
    bpy.ops.yf.reset_op()

def get_current_stage(num, txt=False):
    result = 0 if num % 2 == 0 else 1
    if txt:
        return "WORK " if not result else "BREAK"
    return result

def seconds_to_time_string(seconds):
    # Calculate minutes and remaining seconds
    minutes, seconds = divmod(int(seconds), 60)
    # Format the time string
    time_string = f"{minutes:02d}:{seconds:02d}"
    return time_string

custom_icons = None
load_custom_icons()