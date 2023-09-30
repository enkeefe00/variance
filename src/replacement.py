from src.logger import logger
from abc import ABC, abstractmethod
from pathlib import Path
from re import compile

# Abstract class for ContentReplacement and TargetReplacement to inherit from
class Replacement(ABC):
    @abstractmethod
    def __init__(self, replacement_dict:dict) -> None:
        try:
            self._target = replacement_dict["target"]
        except KeyError as ke:
            raise KeyError(f"error when creating replacement object: {ke}")
        self.values = []
        self.files_to_check = []
    
    @abstractmethod
    def process_replacements(self):
        pass

class TemplatedReplacement(Replacement):
    def __init__(self, templated_replacement_dict:dict, files:"list[Path]") -> None:
        super().__init__(templated_replacement_dict)
        try:
            self.values = templated_replacement_dict["list"]
        except KeyError:
            # defaults to target being replaced sequentially starting at 1
            self.values = list(range(1, len(files)+1)) 
        self.files_to_check = files
    
    def process_replacements(self):
        target_pattern = compile(self._target)
        
        # checks that the number of values provided corresponds to the number of expanded templates
        if len(self.values) != len(self.files_to_check):
                raise ValueError("the number of values provided is not the same as the number of templates expanded. "
                                f"Number of provided values is {len(self.values)} and number of expanded templates is {len(self.files_to_check)}")
        
        # replaces all instances of target in each file with the appropriate list entry
        for replacement_value, replacement_filepath in zip(self.values, self.files_to_check):
            try:
                with open(replacement_filepath, "r") as replacement_file:
                    file_contents = replacement_file.read()
            except FileNotFoundError as fe:
                raise FileNotFoundError(f"{fe}: used in templated replacement {self._target}")
            # overwrites file with new replacements
            with open(replacement_filepath, "w") as replacement_file:
                new_file_contents = target_pattern.sub(str(replacement_value), file_contents)
                replacement_file.write(new_file_contents)
            logger.debug(f"        >>> Replaced {self._target} with {replacement_value} in {replacement_filepath.name}") 
        
class TargetReplacement(Replacement):
    def __init__(self, target_replacement:dict, site_dir:Path) -> None:
        super().__init__(target_replacement)
        self.values.append(target_replacement["value"])
        self._site_dir = site_dir
        files_set = set()
        inclusions = ["config/**/*.json"]
        exclusions = []
        
        try:
            inclusions = target_replacement["include"]
        except KeyError:
            logger.info(f"   >>> Did not find 'include' for replacement with target: '{self._target}'; will assume default configuration")
        try:
            # must always exclude variance.yml file
            exclusions = list(target_replacement["exclude"])
            exclusions.append("variance.yml")
        except KeyError:
            logger.info(f"   >>> Did not find 'exclude' for replacement with target: '{self._target}'; will assume default configuration")
        # aggregates full set of files to check for replacements
        for pathspec in inclusions:
            files_set.update(list(site_dir.glob(pathspec)))
        for pathspec in exclusions:
            files_set.difference_update(list(site_dir.glob(pathspec)))
        self.files_to_check = list(files_set)
    
    def process_replacements(self):
        target_pattern = compile(self._target)
        value = self.values[0]
        
        # iterates over all files to check and overwrites their contents
        for file in self.files_to_check:        
            if file.is_file():
                with open(file, "r") as replacement_file:
                    file_contents = replacement_file.read()
                with open(file, "w") as replacement_file:
                    new_file_contents = target_pattern.sub(value, file_contents)
                    replacement_file.write(new_file_contents)
                # only log if a replacement occured
                if new_file_contents != file_contents:
                    logger.debug("     >>> Replaced all '%s's in %s with '%s'", self._target, file, value)
            elif not file.is_dir():
                logger.warning(f" >>> {file} was not found")