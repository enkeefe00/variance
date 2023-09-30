from src.device import Device
from src.site_obj import Site
from pathlib import Path
from json import load, dumps
from argparse import ArgumentParser
from logger import logger, log_levels


# Support for multiple types of ESS/Site Controller/TWINS devices
FLEXGEN_DEVICES = ["twins", "ess-controller", "site-controller", "fleet-manager", "powercloud"]

parser = ArgumentParser()
parser.add_argument("-l", "--log_level", default="warning", help="What level of logs to print to console")
log_level = vars(parser.parse_args())["log_level"]
## sets logging level of console logger
if log_level in log_levels:    
    logger.handlers[0].level = log_levels[log_level]
else:
    print(f"'{log_level}' is not a valid log level; console logging will be set to WARNING")

# Main code
site_dirs = Path("./config")
for site_dir in site_dirs.iterdir():
    # creates a Site obj
    logger.info(f"\n\n                                   ------{site_dir.name}------\n")
    if log_level != "debug" and log_level != "info":
        print(f"\n\n------{site_dir.name}------\n")
    current_site = Site(site_dir.name)
    current_site_id = current_site.get_id()
    logger.debug(f"  Retrieving {current_site_id}'s config file...")
    site_variant_cfg = current_site.get_config_file()
    
    site_test_dirs = []
    # iterates over devices found in site       
    for device_dir in site_dir.iterdir():
        if device_dir.name not in FLEXGEN_DEVICES:
            if device_dir.is_dir():
                logger.warning(f"'{device_dir.name}' is not a valid device type")
            continue
        current_device = Device(device_dir.name, site_dir.name)
        current_site.devices.append(current_device)
        current_device_type = current_device.get_type()
        current_device.clear_prev_files()
        
        # finds the appropriate variant device dir for current device
        variant_device_dir = Path(f"{current_device_type}_variants")
       
        # checks that device with no variants corresponds to a device variant folder with
        # ONLY a root directory
        if f"{device_dir.name}_variant" not in site_variant_cfg.keys():
            list_of_variants = list(variant_device_dir.iterdir())
            if len(list_of_variants) == 1:
                logger.warning(f"Assuming a root configuration for {current_site_id}'s {current_device_type}")
            else:
                logger.critical(f"{current_site_id}'s {current_device_type} has variants, but no variant key was found")
                exit(1)                
        else:
            current_device.variant = site_variant_cfg[f"{current_device_type}_variant"]
            
        current_device.copy_all_files()
        
        # runs templating first because there may be site-wide replacements in the templates
        if f"{current_device_type}_templates" in site_variant_cfg.keys():
            current_device.templates = site_variant_cfg[f"{current_device_type}_templates"]
            logger.debug(f"  >>> Expanding templates in {current_device.get_directory()}...")
            current_device.expand_templates()
            
        device_test_dir = device_dir / "tests"
        if device_test_dir.exists():
            site_test_dirs.append(device_test_dir)
        else:
            logger.info(f"   Found no tests for {current_site_id}'s {current_device_type}")
    
    if "replacements" in site_variant_cfg.keys():
        logger.debug(f"  Making replacements for {current_site_id}...")
        current_site.set_replacements(site_variant_cfg["replacements"])
        current_site.replace_all_targets()
        logger.info(f"   Finished making replacements for {current_site_id}")
    
    # iterates through ever test file to parse numerical expressions leftover from replacements
    for test_dir in site_test_dirs:
        logger.debug(f"   Iterating through {test_dir.parent} tests for '{current_site_id}'...")
        for testfile in test_dir.iterdir():        
            # parses numerical expressions in test files leftover from replacements
            logger.debug(f"  >>> Parsing numerical expressions in '{testfile.name}'...")
            try:
                with open(testfile, "r", encoding='utf-8') as json_file:
                    file_contents_json = load(json_file)
            except IOError as ioe:
                logger.critical(f"unable to read testfile '{testfile.name}: {ioe}")
                exit(1)
            parsed_file_contents = current_site.testfile_parsing_walker(file_contents_json)
            new_json_file = dumps(parsed_file_contents, indent=4)
            # overwrites file with parsed file contents
            with open(testfile, "w") as new_file:
                    new_file.write(new_json_file)
            logger.info(f"   >>> Finished parsing numerical expressions in '{testfile.name}'")

print("Finished!")