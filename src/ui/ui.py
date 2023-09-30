import PySimpleGUI as sg
from pathlib import Path
import argparse


FLEXGEN_DEVICES = ["twins", "ess-controller", "site-controller", "fleet-manager", "powercloud"]
flexgen_light_theme = {
        'BACKGROUND': '#ffffff',
        'TEXT': '#000000',
        'INPUT': '#113C63',
        'TEXT_INPUT': '#ffffff',
        'SCROLL': '#00da45',
        'BUTTON': ('#ffffff', "#00dcf9"),
        'PROGRESS': ('#ffffff', "#00dcf9"),
        'BORDER': 1,
        'SLIDER_DEPTH': 0,
        'PROGRESS_DEPTH': 0
    }
flexgen_dark_theme = {
        'BACKGROUND': '#000000',
        'TEXT': '#ffffff',
        'INPUT': '#00da45',
        'TEXT_INPUT': '#000000',
        'SCROLL': '#00dcf9',
        'BUTTON': ('#000000', "#00dcf9"),
        'PROGRESS': ('#000000', "#00da45"),
        'BORDER': 1,
        'SLIDER_DEPTH': 0,
        'PROGRESS_DEPTH': 0
    }

def text_list_to_list(text_list: str) -> list:
    comma_separated_list = text_list.split(",")
    return [variant.strip() for variant in comma_separated_list]

def create_initial_window(flexgen_devices: "list[str]", theme: str) -> sg.Window:
    sg.theme(theme)
    titlebar_color = '#113C63'
    icon_path = 'FlexGen_LightX.png'
    if theme == 'FlexGen Dark':
        titlebar_color = '#00da45'        
        icon_path = 'FlexGen_DarkX.png'
        
    layout = [[sg.Text('Select all device types being used:', justification="left", expand_x=True)]]
    for device_type in flexgen_devices:
        layout.append([sg.Checkbox(text=device_type, key=f"{device_type}_CHECKBX", enable_events=True)])
        layout.append([sg.Text(text=f"{device_type} variants: ", key=f"{device_type}_TEXT", visible=False), 
                       sg.Input(default_text=f"Enter a comma separated list", key=f"{device_type}_IN", visible=False, font='Arial 10 italic')])
    layout.append([sg.Button(button_text="Enter", key="ENTER", visible=False), 
                   sg.Text(text="At least one device must be selected!", background_color='yellow', key="ERRORS", visible=False, font='Arial 10 bold', text_color='black')])
    
    return sg.Window('Variance Setup', layout, resizable=True, use_custom_titlebar=True, disable_minimize=True, titlebar_icon=icon_path, titlebar_background_color=titlebar_color) 

def process_window_events(window: sg.Window, flexgen_devices: "list[str]") -> dict:       
    first_time_checkbox_checked = True
    at_least_one_checkbox_checked = False
    device_variants = {}
    
    while True:                           
        event, values = window.read() 
        if event == sg.WIN_CLOSED:
            break
        elif event == "ENTER":
            window["ERRORS"].update(visible=False)
            for device_type_event in flexgen_devices:
                if values[f"{device_type_event}_CHECKBX"] == True:
                    device_variants[device_type_event] = text_list_to_list(values[f"{device_type_event}_IN"])
                    at_least_one_checkbox_checked = True
            if not at_least_one_checkbox_checked:
                window["ERRORS"].update(visible=True)
            else:
                break
                  
        device_type_event = event.split("_")[0]
        if device_type_event in flexgen_devices:            
            window["ERRORS"].update(visible=False)
            window[f"{device_type_event}_TEXT"].update(visible=values[event])
            window[f"{device_type_event}_IN"].update(visible=values[event])   
            if first_time_checkbox_checked:
                window["ENTER"].update(visible=True)
                     
    window.close()
    return device_variants  

def create_device_variants_folders(used_devices: dict):
    for device_type in list(used_devices.keys()):
        variant_folder = Path(f"{device_type}_variants")
        variant_folder.mkdir(exist_ok=True)
        (variant_folder/ "root").mkdir(exist_ok=True)        
        print(f"Created {device_type}'s root directory and device variant folder")

def create_variant_type_folders(device_variants: dict): 
    for device_type in list(device_variants.keys()):
        list_of_variants = device_variants[device_type]
        if list_of_variants == [f"Enter a comma separated list"]:
            # default text wasn't changed
            return
        for variant in list_of_variants:
            Path(f"{device_type}_variants/{variant}").mkdir(exist_ok=True)
            print(f"Created {variant} directory under {device_type}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dark_mode", action="store_true", help="Enables dark mode")
    sg.theme_add_new('FlexGen Dark', flexgen_dark_theme)
    sg.theme_add_new('FlexGen Light', flexgen_light_theme)
    darkmode = vars(parser.parse_args())["dark_mode"]    
    theme = 'FlexGen Light'
    if darkmode:
        theme = 'FlexGen Dark'
        
    initial_window = create_initial_window(FLEXGEN_DEVICES, theme)
    device_variants = process_window_events(initial_window, FLEXGEN_DEVICES)
    create_device_variants_folders(device_variants)
    create_variant_type_folders(device_variants)