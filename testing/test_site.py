from src.site_obj import Site
import pytest
from pathlib import Path
from shutil import rmtree
from re import compile, Pattern
from src.replacement import TargetReplacement


# Fixtures
@pytest.fixture()
def test_site():
    site = Site("test_site_obj")
    yield site
    rmtree(site.get_directory())

@pytest.fixture
def template_pattern():
    return compile(r"(?:((?:-)?(?:\d*[.])?\d+)(?:\*))?((?:\d+)(?:[.]\d+)?)")

@pytest.fixture
def avr_pattern():
    return compile(r"(?:100)([+-])(?:((?:\d*.)(?:\d+))(?:\*))?(\d+)(?:(?:\*\()(\d+)([+-])(\d+)(?:\)))?")

# Actual testing

## test cases
## 0 - site directory DNE
## 1 - site directory already exists
@pytest.mark.parametrize("site_ID", [("new_site"), ("test_site")])
def test_initialize_site(site_ID):
    site = Site(site_ID)
    assert site._directory.exists()
    assert (site._directory / "variance.yml").exists()
    if site._directory.name == "new_site":
        rmtree(site._directory)
    
def test_get_id(test_site: Site):
    assert test_site.get_id() == "test_site_obj"

def test_get_devices(test_site: Site):
    assert test_site.get_devices() == []
    
def test_get_replacements(test_site: Site):
    assert test_site.get_replacements() == []
    
def test_get_directory(test_site: Site):
    test_site_dir = Path("./config/test_site_obj")
    assert test_site.get_directory() == test_site_dir
    assert test_site_dir.exists()

def test_config_file_created(test_site: Site):
    assert Path(test_site.get_directory() / "variance.yml").exists()

def test_set_id(test_site: Site):
    old_dir = Path("./config/test_site_obj")
    new_dir = Path("./config/TESTSITEOBJ")
    
    test_site.set_id("TESTSITEOBJ")
    
    assert not old_dir.exists()
    assert test_site.get_directory() == new_dir

# check that the replacement config list got turned into a list of correct TargetReplacements
def test_set_replacements(test_site: Site):
    test_site.set_replacements([{"target": "{{test_target}}", "value": "testing"}])
    expected_replacement = TargetReplacement({"target": "{{test_target}}", "value": "testing"}, test_site.get_directory())
    assert expected_replacement._target == (test_site.get_replacements())[0]._target
    assert expected_replacement.values == (test_site.get_replacements())[0].values
    
def test_get_config_file_exists(test_site: Site):
    assert test_site.get_config_file() != {}

## check that when looking for a config file that dne, an empty dictionary is returned
def test_get_config_file_dne():
    test_site = Site("config_test_site")
    (test_site.get_directory() / "variance.yml").unlink()
    assert test_site.get_config_file() == {}
    test_site.get_directory().rmdir()

## test cases
## 0 - no match found in search string
## 1 - positive coefficient and parsable expression in search string
## 2 - negative coefficient and parsable expression found in search string
## 3 - no coefficient and parsable expression found in search string
## 4 - invalid expression found
@pytest.mark.parametrize("search_string, expected_result", [
    ("This is not a match: ##ESS"        , None     ),
    (".75*2000"                          , "1500.0" ),
    ("-.75*2000"                         , "-1500.0"),
    ("Issue a 2000.5 discharge command"  , "2000.5" ),
    ("Issue a .75+11.6 discharge command", "75"     )
])
def test__evaluate_normal_expressions(search_string: str, expected_result: str, test_site: Site, template_pattern: Pattern):
    match = template_pattern.search(search_string)
    result = test_site._evaluate_normal_expressions(match)
    assert result == expected_result

## test cases
## 0 - invalid AVR expression
## 1 - difference of percentages
## 2 - sum of percentages
## 3 - sum of voltages
## 4 - difference of voltages
## 5 - no voltage deadband present or parentheses
## 6 - no voltage deadband present with parentheses
@pytest.mark.parametrize("search_string, expected_result", [
    ("-.5*5"              , None      ),
    ("100-.5*5"           , "97.5"    ),
    ("100+.5*5"           , "102.5"   ),
    ("100-.5*5*(12000+0)" , "11700.0" ),
    ("100-.5*5*(12000+50)", "11748.75"),
    ("100-.5*5*12000"     , "97.5"    ),
    ("100-.5*5*(12000)"   , "97.5"    )
])
def test__evaluate_avr_expressions(search_string: str, expected_result: str, test_site: Site, avr_pattern: Pattern):
    match = avr_pattern.search(search_string)
    result = test_site._evaluate_avr_expressions(match)
    assert result == expected_result
    
## test cases
## 0 - object has an unreplaced wildcard
## 1 - object is a dictionary
## 2 - object is a list
## 3 - object is a nested dictionary
## 4 - object is a nested list
## 5 - object is a nested list/dictionary
## 6 - object has non-string entries
@pytest.mark.parametrize("search_obj, expected_result", [
    ({"{{WILDCARD}}": "17*5"   },                                                                  {"{{WILDCARD}}": 85.0      }                                                                 ),
    ({"stuff"       : "4 = 2*2"},                                                                  ({"stuff"      : "4 = 4.0"})                                                                 ),
    (["eleven", "ten", "2.5*4" ],                                                                  ["eleven", "ten", 10.0     ]                                                                 ),
    ({"stuff"       : {"more_stuff": "issue a 7.5*10 kW cmd"}},                                    {"stuff": {"more_stuff": "issue a 75.0 kW cmd"}}                                             ),
    ([[["12*6 is 72", "stuff"], "item_2", "item_3"], []],                                          [[["72.0 is 72", "stuff"], "item_2", "item_3"], []]                                          ),
    ([{}, {"more_stuff": "4*5.5"}, "stuff", ["a", "b"]],                                           [{}, {"more_stuff": 22.0}, "stuff", ["a", "b"]]                                              ),
    ([{"bool": True, "other_bool": False, "num": 2}, {"stuff": "Life is 7*6", "string": "hello"}], [{"bool": True, "other_bool": False, "num": 2}, {"stuff": "Life is 42.0", "string": "hello"}])
])
def test_testfile_parsing_walker(search_obj, expected_result, test_site: Site):
    result = test_site.testfile_parsing_walker(search_obj)
    assert result == expected_result