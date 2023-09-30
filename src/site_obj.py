from logger import logger
from pathlib import Path
from shutil import copytree, rmtree
from re import Match, compile, match
from yaml import safe_load, safe_dump
from src.replacement import TargetReplacement


class Site():
    def __init__(self, site_id: str) -> None:
        self._id = site_id
        self.devices = [] 
        self.replacements = []
        self._directory = Path(f"./config/{site_id}")
        config_filepath = self._directory / "variance.yml"
        
        # creates site directory if it DNE
        if not self._directory.is_dir():
            self._directory.mkdir()
        # creates variance config file if it DNE
        if not config_filepath.exists():
            with open(config_filepath, 'w') as new_file:
                safe_dump("", new_file)
    
    def get_id(self) -> str:
        return self._id
    
    def get_devices(self) -> list:
        return self.devices
    
    def get_replacements(self) -> "list[TargetReplacement]":
        return self.replacements
    
    def get_directory(self) -> Path:
        return self._directory
    
    def set_id(self, new_site_id:str) -> None:
        self._id = new_site_id
        old_site_directory = self._directory
        self._directory = Path(f"./config/{new_site_id}")
        # copies all existing files to new_site_id directory
        copytree(old_site_directory, self._directory, dirs_exist_ok=True)
        rmtree(old_site_directory)
    
    def set_replacements(self, replacements_list: "list[dict]") -> None:
        for replacement_dict in replacements_list:
            self.replacements.append(TargetReplacement(replacement_dict, self._directory))
    
    def get_config_file(self)-> dict:
        config_filepath = self._directory / "variance.yml"
        if config_filepath.is_file():
            with open(config_filepath, 'r') as variance_cfg:
                return safe_load(variance_cfg)
        else:
            logger.warning(f"no config file was found for {self._directory.name}")
            return {}     
    
    def replace_all_targets(self) -> None:
        for replacement in self.replacements:
            replacement.process_replacements()
    
    @staticmethod
    def _evaluate_avr_expressions(match: Match) -> str:
        # only evaluates expressions if there is a match
        if match:
            # required in match
            first_sign = match.group(1)
            coefficient = match.group(2)
            # required in match
            droop_percent = match.group(3)
            poi_voltage = match.group(4)
            # required if both poi_voltage and deadband_voltage present
            second_sign = match.group(5)
            deadband_voltage = match.group(6)
            
            if coefficient:
                droop_percent = float(coefficient)*float(droop_percent)
            if first_sign == "+":
                percentage = 100+float(droop_percent)
            else:
                percentage = 100-float(droop_percent)
            
            # calculates the actual voltage command if deadband and POI voltage are provided
            if poi_voltage != None and deadband_voltage != None:
                if second_sign == "+":
                    voltage_sum = int(poi_voltage) + int(deadband_voltage)
                else:
                    voltage_sum = int(poi_voltage) - int(deadband_voltage)
                return str((percentage/100)*voltage_sum)
            
            # only evaluates the percentage of the voltage command
            return str(percentage)
        
    @staticmethod
    def _evaluate_normal_expressions(match: Match) -> str:
        if match:
            coefficient = match.group(1)
            variable_value = match.group(2)            
            if coefficient:
                return str(float(coefficient) * float(variable_value))
            else:
                return variable_value
        
    def testfile_parsing_walker(self, obj):
        template_pattern = compile(r"(?:((?:-)?(?:\d*[.])?\d+)(?:\*))?((?:\d+)(?:[.]\d+)?)")
        avr_pattern = compile(r"(?:100)([+-])(?:((?:\d*.)(?:\d+))(?:\*))?(\d+)(?:(?:\*\()(\d+)([+-])(\d+)(?:\)))?")
        replacement_pattern = compile(r"{{\w+}}")
        
        # iterates through each dictionary value
        if type(obj) == dict:
            replacement_dict = {}
            for key in obj:
                entry = obj[key]
                replacement_dict[key] = self.testfile_parsing_walker(entry)
            return replacement_dict
        # iterates through each list item
        elif type(obj) == list:
            index = 0
            replacement_list = [None] * len(obj)
            for entry in obj:
                replacement_list[index] = self.testfile_parsing_walker(entry)
                index = index + 1
            return replacement_list
        elif type(obj) == str:
            obj_to_try = obj
            ## first, looks for un-replaced wildcards
            found_wildcard = match(replacement_pattern, obj_to_try)
            if found_wildcard != None:
                logger.warning(f"   >>> Found an unreplaced wildcard '{found_wildcard.string}'")
                
            ## next, tries special case for AVR
            avr_replacement = avr_pattern.sub(self._evaluate_avr_expressions, obj_to_try)
            if avr_replacement != obj:
                ## checks if the entire string was a numerical expression
                try:
                    avr_replacement = float(avr_replacement)
                    return avr_replacement
                except ValueError:
                    obj_to_try = avr_replacement
                    
            replacement = template_pattern.sub(self._evaluate_normal_expressions, obj_to_try)
            if replacement != obj_to_try:    
                ## checks if the entire string was a numerical expression            
                try:
                    replacement = float(replacement)
                except ValueError:
                    pass
            return replacement
        # doesn't attempt to iterate over or replace other types
        else:
            return obj