from src.replacement import TargetReplacement, TemplatedReplacement
import pytest
from pathlib import Path
from shutil import copy2


@pytest.fixture(scope="session")
def templated_replacement_test_dir_name():
    return "templated_replacement_testing"

@pytest.fixture(scope="session")
def target_replacement_test_dir_name():
    return "target_replacement_testing"

# Generates a list of all testing directories directly underneath the testing directory
@pytest.fixture(scope="session")
def testing_dirs(testing_path: Path) -> "list[Path]":
    testing_sub_dirs = []
    for test_filepath in testing_path.iterdir():
        if test_filepath.is_dir():
            testing_sub_dirs.append(test_filepath)
    return testing_sub_dirs

# Copies testing files/directories to a temporary directory so the original files aren't altered
@pytest.fixture(autouse=True, scope="session")
def setup_testdirs(tmp_dir: Path, testing_dirs: "list[Path]") -> None:
    for test_dir in testing_dirs:
        full_tmp_test_dir = tmp_dir / test_dir.name
        full_tmp_test_dir.mkdir()
        for test_file in test_dir.iterdir():
            copy2(test_file, full_tmp_test_dir)
    yield 
    for tmp_test_dir in tmp_dir.iterdir():
        for test_file_copy in tmp_test_dir.iterdir():
            test_file_copy.unlink()
        tmp_test_dir.rmdir()

# MAKE SURE ALL target_replacement VARIABLES ARE LISTS OF THE SAME LENGTH!
target_replacement_objs = [
        {"target": "{{SITE_ID}}"  , "value": "test_site"       , "include": ["single_target_replacement_file.json"                          ]                                       },
        {"target": "{{DNE}}"      , "value": "doesn't exist"   , "include": ["target_dne_replacement_file.json"                             ]                                       },
        {"target": "##INCLUSION##", "value": "included!"       , "include": ["target_inclusion_file_1.json" , "target_inclusion_file_2.json"]                                       },
        {"target": "{{EXCLUSION}}", "value": "excluded!"       ,                                                                               "exclude": ["target_exclusion*.json"]},
        {"target": "{{TARGET}}"   , "value": "target_replaced!", "include": ["a*.json"                                                      ], "exclude": ["ab.json"               ]},
        {"target": "{{SITE_ID}}"  , "value": "test_site"}   
]

target_replacement_changed_files = [
        ["single_target_replacement_file.json"                                             ],
        ["target_dne_replacement_file.json"                                                ],
        ["target_inclusion_file_1.json"        , "target_inclusion_file_2.json"            ],
        ["target_inclusion_file_1.json"        , "target_inclusion_file_2.json", "abc.json"],
        ["a.json"                              , "abc.json"                                ],
        ["target_inclusion_file_1.json"          , "target_exclusion_file_2.json"  , "abc.json"]
]

target_replacement_unchanged_files = [
        ["target_inclusion_file_1.json"                                              ],
        ["single_target_replacement_file.json"                                       ],
        ["a.json"                             , "single_target_replacement_file.json"],
        ["target_exclusion_file_1.json"       , "target_exclusion_file_2.json"       ],
        ["ab.json"                            , "target_exclusion_file_1.json"       ],
        []
]

# TemplatedReplacement Testing

## test cases
## 1 - replacement config has no list in templated replacement config
## 2 - replacement config has list of strings
## 3 - replacement config has list of integers
@pytest.mark.parametrize("templated_dict, files", [
    ({"target": "{{TEST_1}}"                      }, [Path("./config/test_1/file1"), Path("./config/test_1/file2")                               ] ),
    ({"target": "{{TEST_2}}", "list": ["01", "02"]}, [Path("./config/test_2/file1"), Path("./config/test_2/file2")                               ] ),
    ({"target": "{{TEST_3}}", "list": [24, 25, 26]}, [Path("./config/test_3/file1"), Path("./config/test_3/file2"), Path("./config/test_3/file3")] ),
])
def test_initialize_templated_replacement(templated_dict, files):
    replacement = TemplatedReplacement(templated_dict, files)
    assert replacement._target == templated_dict["target"]
    assert replacement.files_to_check == files
    if "list" in templated_dict:
        assert replacement.values == templated_dict["list"]
    else:
        assert replacement.values == list(range(1, len(files)+1))

## check that files have no targets leftover and have been replaced with the proper value         
def test_process_templated_replacement_with_list(tmp_dir: Path, templated_replacement_test_dir_name: str):
    files_to_check = [(tmp_dir / templated_replacement_test_dir_name / "templated_replacement_list_file_1.json"), 
                       (tmp_dir / templated_replacement_test_dir_name /"templated_replacement_list_file_2.json")] 
    templated_cfg = {"target": "{{ESS_ID}}", "list": ["alpha", "beta"]}
                 
    replacement = TemplatedReplacement(templated_cfg, files_to_check)
    replacement.process_replacements()
    for file, templated_value in zip(files_to_check, templated_cfg["list"]):
        with open(file, "r") as test_file:
            test_file_text = test_file.read()
        if test_file_text.find(templated_cfg["target"]) != -1:
            assert False
        elif test_file_text.find(templated_value) < 0:
            assert False
    assert True
 
 ## check that files have no targets leftover and have been replaced with the proper sequential value   
def test_process_templated_replacement_no_list(tmp_dir: Path, templated_replacement_test_dir_name: str):
    files_to_check = [(tmp_dir / templated_replacement_test_dir_name / "templated_replacement_file_1.json"), 
                       (tmp_dir / templated_replacement_test_dir_name /"templated_replacement_file_2.json")] 
    config = {"target": "{{ESS_IP}}"}   
    values_to_check_against = range(1, len(files_to_check)+1)
    
    replacement = TemplatedReplacement(config, files_to_check)
    replacement.process_replacements()
    for file, int_value in zip(files_to_check, list(values_to_check_against)):
        with open(file, "r") as test_file:
            test_file_text = test_file.read()
        if test_file_text.find(config["target"]) != -1:
            assert False, f"{test_file}'s text: {test_file_text}"
        elif test_file_text.find(str(int_value)) < 0:
            assert False, f"{test_file}'s text: {test_file_text}"
    assert True

## check that an error occurs if the number of replacements doesn't match the number of files to parse
def test_process_templated_replacement_bad_list_length(tmp_dir: Path, templated_replacement_test_dir_name: str):
    files_to_check = [(tmp_dir / templated_replacement_test_dir_name / "templated_replacement_list_file_1.json"), 
                       (tmp_dir / templated_replacement_test_dir_name /"templated_replacement_list_file_2.json")] 
    config = {"target": "{{ESS_ID}}", "list": ["item"]}  
      
    replacement = TemplatedReplacement(config, files_to_check)    
    with pytest.raises(ValueError) as ve:
        replacement.process_replacements()
    assert ve.type == ValueError

# TargetReplacement Testing

## test cases
## 0 - replacement config has no inclusions/exclusions and value is an int
## 1 - replacement config has no inclusions/exclusions and value is a str
## 2 - replacement config has no inclusions/exclusions and value is a negative int
## 3 - replacement config has no inclusions (multiple files to replace in) and has exclusions
## 4 - replacement config has inclusions, but no exclusions
## 5 - replacement config has a single entry for both "include" and "exclude"
## 6 - replacement config has no multiple entries for "exclude" and one for "include"
@pytest.mark.parametrize("target_dict, expected_files", [
    (
        {"target": "{{TEST_0}}", "value": "11"}, 
        ["a.json" , "abc.json" , "ab.json", "target_inclusion_file_1.json" , "target_inclusion_file_2.json" , "single_target_replacement_file.json", "target_dne_replacement_file.json", "target_exclusion_file_1.json" , "target_exclusion_file_2.json"]
    ),
    (
        {"target": "{{TEST_1}}", "value": "string"},
        ["a.json" , "abc.json" , "ab.json", "target_inclusion_file_1.json" , "target_inclusion_file_2.json" , "single_target_replacement_file.json", "target_dne_replacement_file.json", "target_exclusion_file_1.json" , "target_exclusion_file_2.json"]
    ),
    (
        {"target": "{{TEST_2}}", "value": "-25.0"},
        ["a.json" , "abc.json" , "ab.json", "target_inclusion_file_1.json" , "target_inclusion_file_2.json" , "single_target_replacement_file.json", "target_dne_replacement_file.json", "target_exclusion_file_1.json" , "target_exclusion_file_2.json"]
    ),
    (
        {"target": "{{TEST_3}}", "value": "42", "exclude": ["*.json"]}, 
        []
     ),
    (
        {"target": "{{TEST_4}}", "value": "42", "include": ["target_i*"]},
        ["target_inclusion_file_1.json" , "target_inclusion_file_2.json"]
     ),
    (
        {"target": "{{TEST_5}}", "value": "42", "include": ["target_i*"], "exclude": ["*2.json"]}, 
        ["target_inclusion_file_1.json"]
     ),
    (
        {"target": "{{TEST_6}}", "value": "42", "include": ["target_*" ], "exclude": ["target_inclusion_file_1.json", "target_dne_replacement_file.json", "target_ex*.json"]}, 
        ["target_inclusion_file_2.json"]
     )
])
def test_initialize_target_replacement(tmp_dir: Path, target_replacement_test_dir_name: str, target_dict: dict, expected_files: "list[str]"):
    replacement = TargetReplacement(target_dict, (tmp_dir / target_replacement_test_dir_name)) 
    assert replacement._target == target_dict["target"]
    assert replacement.values == [target_dict["value"]]
    if len(replacement.files_to_check) != len(expected_files):
        assert False, f"replacement files: {len(replacement.files_to_check)} vs. expected: {len(expected_files)}"
    for item in expected_files:
        if not (tmp_dir / target_replacement_test_dir_name / item) in replacement.files_to_check:
            assert False, f" looking for {(tmp_dir / target_replacement_test_dir_name / item)}"
    assert True

## test cases
## 0 - replacement config replaces in one file
## 1 - replacement config has a target that doesn't exist in the file
## 2 - replacement config replaces in multiple files with the "include" field
## 3 - replacement config contains pathsperc exclusions
## 4 - replacement config contains pathspec inclusions and exclusions
## 5 - replacement config has neither and "include" or "exclude" field
@pytest.mark.parametrize("target_dict, changed_files, unchanged_files", [
    (target_replacement_objs[0], target_replacement_changed_files[0], target_replacement_unchanged_files[0]),
    (target_replacement_objs[1], target_replacement_changed_files[1], target_replacement_unchanged_files[1]),
    (target_replacement_objs[2], target_replacement_changed_files[2], target_replacement_unchanged_files[2]),
    (target_replacement_objs[3], target_replacement_changed_files[3], target_replacement_unchanged_files[3]),
    (target_replacement_objs[4], target_replacement_changed_files[4], target_replacement_unchanged_files[4]),
    (target_replacement_objs[5], target_replacement_changed_files[5], target_replacement_unchanged_files[5])
])
def test_process_target_replacement(tmp_dir: Path, target_replacement_test_dir_name: str, target_dict: dict, changed_files, unchanged_files):        
    replacement = TargetReplacement(target_dict, (tmp_dir / target_replacement_test_dir_name))
    replacement.process_replacements()
    # check for positive replacements
    for file in changed_files:
        with open((tmp_dir / target_replacement_test_dir_name / file), "r") as test_file:
            test_file_text = test_file.read()
        if test_file_text.find(target_dict["target"]) != -1:
            assert False, f"{file}'s content: {test_file_text}" 
    #check for an absence of replacements
    for file in unchanged_files:
        with open((tmp_dir / target_replacement_test_dir_name / file), "r") as test_file:
            test_file_text = test_file.read()
        if test_file_text.find(target_dict["target"]) == -1:
            assert False, f"{file}'s content: {test_file_text}" 
    assert True