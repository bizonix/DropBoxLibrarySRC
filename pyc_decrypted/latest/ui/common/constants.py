#Embedded file name: ui/common/constants.py
colors = {'black': (0, 0, 0, 255),
 'clear': (0, 0, 0, 0),
 'disabled_text': (127, 127, 127, 255),
 'example_text': (102, 102, 102, 255),
 'image_outline': (127, 127, 127, 255),
 'link': (0, 119, 204, 255),
 'notification_background': (0, 0, 0, 165),
 'notification_border': (36, 154, 255, 51),
 'notification_border_hover': (36, 154, 255, 100),
 'plan_choice_text': (0, 119, 204, 255),
 'plan_choice_hover_background': (244, 250, 255, 170),
 'plan_choice_hover_foreground': (198, 216, 228, 170),
 'plan_choice_selected_background': (235, 245, 255, 250),
 'plan_choice_selected_foreground': (0, 119, 204, 255),
 'default_hover_color': (244, 250, 255, 154),
 'default_hover_border_color': (198, 216, 228, 255),
 'default_selected_color': (235, 245, 255, 255),
 'default_selected_border_color': (0, 119, 204, 255),
 'preferences_selection': (168, 215, 248, 255),
 'setup_wizard_background': (255, 255, 255, 150),
 'setup_wizard_border': (127, 127, 127, 255),
 'text_error': (180, 4, 13, 255),
 'white': (255, 255, 255, 255),
 'gray': (187, 187, 187, 255),
 'camera_font': (0, 76, 135, 255),
 'screenshots_header_font': (0, 126, 230, 255),
 'screenshots_subheader_font': (51, 51, 51, 255),
 'photo_gallery_header': (0, 126, 230, 255),
 'photo_gallery_subheader': (51, 51, 51, 255),
 'fine_print': (132, 132, 132, 255),
 'line_windows': (204, 204, 204, 255)}
password_strength_colors = [(200, 200, 200, 0),
 (200, 24, 24, 0),
 (255, 172, 29, 0),
 (166, 192, 96, 0),
 (39, 179, 15, 0)]
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = SECONDS_PER_HOUR * 24

class ResizeMethod(object):
    FIT = 1
    SCRATCH = 2
    CROP = 3
