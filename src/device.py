from src.logger import logger
from pathlib import Path
from shutil import copy2, copytree, move, rmtree
from re import sub
from src.replacement import TemplatedReplacement


class Device():
    def __init__(self, device_type: str, site: str, variant="root" ) -> None:
        self._type = device_type
        self.templates = []
        self.variant = variant
        self._directory = Path(f"./config/{site}/{self._type}")
    
    def get_type(self) -> str:
        return self._type

    def get_directory(self) -> Path:
        return self._directory
    
    def clear_prev_files(self):
        cfg_dir = self._directory / "config"
        test_dir = self._directory / "tests"
        # removes config files
        if cfg_dir.exists():
            rmtree(cfg_dir)
            logger.info(f"\n                                   Old {self._directory.name} config files successfully removed")
        else:
            logger.info(f"\n                                   No old config files in '{self._directory.name}/config' to remove")
        # removes test files
        if test_dir.exists():
            rmtree(test_dir)
            logger.info(f"   Old {self._directory.name} test files successfully removed")
        else:
            logger.info(f"   No old test files in '{self._directory.name}/test' to remove")
    
    def _copy_root_files(self)-> None:
        # moves all root device files to device config directory
        dest_cfg_dir = self._directory / "config"
        device_root_dir = Path(f"./{self._type}_variants/root")
        copytree(device_root_dir, dest_cfg_dir, dirs_exist_ok=True)
        
        # moves 'tests' folder in 'config' (if present) to same level as 'config'
        cfg_test_dir = dest_cfg_dir / "tests"
        if cfg_test_dir.exists():
            logger.debug(f"     >>> Found tests in root files, moving out of '{cfg_test_dir}")
            dest_test_dir = self._directory / "tests"
            move(cfg_test_dir, dest_test_dir)
    
    def _copy_variant_files(self)-> None:
        variant_dir = Path(f"./{self._type}_variants/{self.variant}")  
        # validates device variant
        if not variant_dir.exists():
            logger.critical(f"'{self._type}' is not a valid variant: the {variant_dir} dir does not exist")
            exit(1)
        elif self.variant == "root":
            # No variant key found so only root structure needed
            return
        
        variant_sub_dirs = variant_dir.iterdir()
        # copies contents of each variant subdirectory to the device's corresponding subdirectory
        for sub_dir in variant_sub_dirs:        
            # puts tests in 'tests' folder on same level as destination config folder
            if sub_dir.name == "tests":
                dest_sub_dir = self._directory / "tests"
                logger.debug(f"     >>> Found tests in variant files, moving all files to '{dest_sub_dir}'")
            else: 
                dest_sub_dir = self._directory / "config" / sub_dir.name
            copytree(sub_dir, dest_sub_dir, dirs_exist_ok=True)
    
    # Copies files from root folder and specified variant folder
    def copy_all_files(self)-> None: 
        logger.debug("  >>> Copying over root files...")
        self._copy_root_files()
        logger.info("   >>> Copied over root files")        
        logger.debug(f"  >>> Copying over variant files for variant {self._type}...")
        self._copy_variant_files()
        logger.info(f"   >>> Copied over variant files for variant {self._type}")

    def expand_templates(self):
        # looks for '{{target}}' in filename when expanding templates
        filename_replacement_target = "{{target}}"
        
        for template_entry in self.templates:
            # looks for required fields in templates field
            try:
                pattern = template_entry["filename_pattern"]
                full_template_path = self._directory / "config" / str(template_entry["path"])
                filename = pattern["filename_template"]
                pattern_type = pattern["type"]
            except KeyError as ke:
                raise KeyError(ke)
            
            # validates that the template file exists
            if not full_template_path.is_file():
                raise FileNotFoundError(f"template file '{full_template_path}' DNE or is not a file")
            
            # determines the list of values to be used in templating
            logger.debug(f"     >>> Expanding template {filename}...")
            generated_filenames = []
            if pattern_type == "sequential":
                try:
                    start = pattern["from"]
                    stop = pattern ["to"]
                except KeyError as ke:
                    raise KeyError(f"error getting pattern type of sequential template {filename}: {ke}")
                values_list = range(start, stop + 1)
            elif pattern_type == "list":
                try:
                    list_values = pattern["list"]
                except KeyError as ke:
                    raise KeyError(f"error getting pattern type of list template {filename}: {ke}")
                values_list = list_values
            else:
                raise ValueError(f"pattern type {pattern_type} is not suppported")
            
            for value in values_list:
                # generates new file name with substituted value
                new_filename = sub(filename_replacement_target, str(value), filename)
                # copies file with new file name in the same directory
                new_filename_path = full_template_path.with_name(new_filename)
                copy2(full_template_path, new_filename_path)
                generated_filenames.append(new_filename_path)
                logger.debug(f"        >>> Expanded template to '{new_filename_path.name}'")
                    
            if "templated_replacements" in template_entry.keys():
                for templated_replacement in template_entry["templated_replacements"]:
                    replacement = TemplatedReplacement(templated_replacement, generated_filenames)
                    replacement.process_replacements()
                    
            # deletes template file after succesful expansion and replacement
            full_template_path.unlink()
            logger.info(f"      >>> Template expansion complete. Removed {full_template_path.name}")