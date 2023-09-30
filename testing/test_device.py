from src.device import Device
import pytest
from pathlib import Path
import shutil


# Fixtures
@pytest.fixture
def test_site_path() -> Path:
    return Path("./config/test_site")

@pytest.fixture
def sc_device_path(test_site_path: Path) -> Path:
    return test_site_path / "site-controller"

@pytest.fixture
def sc_config_path(sc_device_path: Path) -> Path:
    return sc_device_path / "config"

@pytest.fixture
def sc_tests_path(sc_device_path: Path) -> Path:
    return sc_device_path / "tests"

@pytest.fixture
def root_sc_device() -> Device:
    return Device("site-controller", "test_site")

# Actual testing

## test cases
## 1 - variant exists
## 2 - variant is root
## 3 no variant provided
@pytest.mark.parametrize( "device_info", [
    ({"type": "site-controller", "variant": "test_type"}),
    ({"type": "ess-controller" , "variant": "root"     }),
    ({"type": "twins"                                  }),
])
def test_initialize_device(device_info):
    device_type = device_info["type"]
    try:
        device_instance = Device(device_info["type"], "test_site", device_info["variant"])
    except KeyError:
        device_instance = Device(device_info["type"], "test_site")
    assert device_instance.get_type() == device_info["type"]
    assert device_instance.templates == []
    assert device_instance.get_directory() == Path(f"./config/test_site/{device_type}")
    if "variant" in device_info:
        assert device_instance.variant == device_info["variant"]
    else:
        assert device_instance.variant == "root"

def test_get_type(root_sc_device: Device):
    assert root_sc_device.get_type() == "site-controller"

def test_get_directory(root_sc_device: Device, sc_device_path: Path):
    assert root_sc_device.get_directory() == sc_device_path

# check that the 'config' and 'tests' directories are removed if they already exist and are empty    
def test_clear_prev_files_empty_dirs(sc_config_path: Path, sc_tests_path: Path, root_sc_device: Device):
    if sc_config_path.exists():
        shutil.rmtree(sc_config_path)
        sc_config_path.mkdir()
    if sc_tests_path.exists():
        shutil.rmtree(sc_tests_path)
        sc_tests_path.mkdir()
    root_sc_device.clear_prev_files()
    assert not sc_config_path.exists() and not sc_tests_path.exists()

# check that the 'config' and 'tests' directories are removed if they don't exist  
def test_clear_prev_files_dne(sc_config_path: Path, sc_tests_path: Path, root_sc_device: Device):
    if sc_config_path.exists():
        shutil.rmtree(sc_config_path)
    if sc_tests_path.exists():
        shutil.rmtree(sc_tests_path)
    root_sc_device.clear_prev_files()
    assert not sc_config_path.exists() and not sc_tests_path.exists()

# check that the 'config' and 'tests' directories are removed only 'config' exists  
def test_clear_prev_files_config_dne(sc_config_path: Path, sc_tests_path: Path, root_sc_device: Device):
    if sc_config_path.exists():
        shutil.rmtree(sc_config_path)
    if not sc_tests_path.exists():
        sc_tests_path.mkdir()
        with open("./config/test_site/site-controller/tests/test_test.json", "w") as file:
            file.write("test")  
    root_sc_device.clear_prev_files()
    assert not sc_config_path.exists() and not sc_tests_path.exists()

# check that the 'config' and 'tests' directories are removed if only 'tests' exists
def test_clear_prev_files_tests_dne(sc_config_path: Path, sc_tests_path: Path, root_sc_device: Device):
    if sc_tests_path.exists():
        shutil.rmtree(sc_tests_path)
    if not sc_config_path.exists():
        sc_config_path.mkdir()
        sc_config_sub_dir = sc_config_path / "site_controller"
        sc_config_sub_dir.mkdir()  
        with open("./config/test_site/site-controller/config/site_controller/assets.json", "w") as file:
            file.write("test")
    root_sc_device.clear_prev_files()
    assert not sc_config_path.exists() and not sc_tests_path.exists()

# check that the 'config' and 'tests' directories are removed if both directories exist and have files inside 
def test_clear_prev_files_exists(sc_config_path: Path, sc_tests_path: Path, root_sc_device: Device):    
    if not sc_config_path.exists():
        sc_config_path.mkdir()
        sub_cfg_dirs = ["site_controller", "ftd", "cloud_sync"]
        for sub_dir in sub_cfg_dirs:
            sc_config_sub_dir = sc_config_path / sub_dir
            sc_config_sub_dir.mkdir()
        with open("./config/test_site/site-controller/config/cloud_sync/cloud_sync.json", "w") as file:
            file.write("test")
        with open("./config/test_site/site-controller/config/site_controller/assets.json", "w") as file:
            file.write("test")
    if not sc_tests_path.exists():
        sc_tests_path.mkdir()
        with open("./config/test_site/site-controller/tests/test_test.json", "w") as file:
            file.write("test")    
    root_sc_device.clear_prev_files()
    assert not sc_config_path.exists() and not sc_tests_path.exists()

## test cases
## 0 - copy root files for an ESS Controller
## 1 - copy root files for a Site Controller
## 2 - copy root files for a TWINS machine
@pytest.mark.parametrize("device_type", [("ess-controller"), ("site-controller"), ("twins")])
def test__copy_root_files(device_type: str):
    device_path = Path(f"./config/test_site/{device_type}")
    test_path = device_path / "tests"
    cfg_path = device_path / "config"
    device_instance = Device(device_type, "test_site")
    src_path = Path(f"./{device_type}_variants/root")
    expected = list(src_path.glob("**/*.json"))
    if test_path.exists():
        shutil.rmtree(test_path)
    if cfg_path.exists():
        shutil.rmtree(cfg_path)
    device_instance._copy_root_files()
    if device_path.exists():
        assert len(expected) == len(list(device_path.glob("**/*.json")))
    else:
        assert False

# check that an error occurs if a variant does not exist in the device's variant folder
def test__copy_variant_files_invalid_variant():
    invalid_device = Device("site-controller", "test", "invalid_var")
    with pytest.raises(SystemExit) as se:
        invalid_device._copy_variant_files()
    assert se.type == SystemExit

## test cases
## 0 - copy root files for Site Controller
## 1 - copy root files for ESS Controller
## 2 - copy root files for TWINS machine
@pytest.mark.parametrize( "device_type", [("site-controller"), ("ess-controller"), ("twins")])
def test__copy_variant_files_root_variant(device_type: str):
    device_instance = Device(device_type, "test_site")
    orig_num_files_present = len(list(device_instance.get_directory().glob("**/*.json")))
    device_instance._copy_variant_files()
    assert len(list(device_instance.get_directory().glob("**/*.json"))) == orig_num_files_present

## test cases
## 0 - copy variant "test_type" files for Site Controller
## 1 - copy variant "root" files for ESS Controller (NO FILES COPIED)
## 2 - copy variant "2500kW" files for TWINS machine
@pytest.mark.parametrize("device_type, variant", [("site-controller", "test_type"), ("ess-controller", "root"), ("twins", "2500kW")])
def test__copy_variant_files(device_type: str, variant: str):
    device_instance = Device(device_type, "test_site", variant)
    src_path = Path(f"./{device_type}_variants/{variant}")
    cfg_path = device_instance.get_directory() / "config"
    test_path = device_instance.get_directory() / "tests"
    # no files will be copied over
    if src_path.name == "root":
        expected = 0
    else:
        expected = len(list(src_path.glob("**/*.json")))
    if cfg_path.exists():
        shutil.rmtree(cfg_path)  
    if test_path.exists():
        shutil.rmtree(test_path)
    device_instance._copy_variant_files()
    assert expected == len(list(device_instance.get_directory().glob("**/*.json")))

# check that all variant files are copied and do not overwrite other files currently existing in the device's
# 'config' and 'tests' directories
def test__copy_variant_files_sub_dirs_exists(sc_config_path: Path, sc_tests_path: Path):
    src_path = Path("./site-controller_variants/test_type")
    num_files_in_test_type = len(list(src_path.glob("**/*.json")))
    sc_test_type_device = Device("site-controller", "test_site", "test_type")
    if sc_config_path.exists():
        shutil.rmtree(sc_config_path)
    if sc_tests_path.exists():
        shutil.rmtree(sc_tests_path)
                
    sc_config_path.mkdir()
    sc_tests_path.mkdir()
    path = sc_config_path / "ftd"
    if not path.exists():
        path.mkdir()
        with open("./config/test_site/site-controller/config/ftd/ftd_2.json", "w") as file:
            file.write("test")
    path = sc_config_path / "metrics"
    if not path.exists():
        path.mkdir()
        with open("./config/test_site/site-controller/config/metrics/metrics.json", "w") as file:
            file.write("metrics test")
    
    sc_test_type_device._copy_variant_files()
    # added 2 for files created above
    assert len(list(sc_test_type_device.get_directory().glob("**/*.json"))) == num_files_in_test_type + 2

# check that all variant files are copied to the correct locations when the `config` and `tests` directories are empty
def test__copy_variant_files_sub_dirs_dne(sc_config_path: Path, sc_device_path: Path, sc_tests_path: Path):
    sc_test_type_device = Device("site-controller", "test_site", "test_type")
    src_path = Path("./site-controller_variants/test_type")
    expected = len(list(src_path.glob("**/*.json")))
    if sc_config_path.exists():
        shutil.rmtree(sc_config_path)
        sc_config_path.mkdir()
    if sc_tests_path.exists():
        shutil.rmtree(sc_tests_path)
        sc_tests_path.mkdir()
    sc_test_type_device._copy_variant_files()
    assert expected == len(list(sc_device_path.glob("**/*.json")))

# checks that all root and "test_type" variant files are copied to the site-controller's proper device folders
def test_copy_all_files(sc_config_path: Path, sc_tests_path: Path):
    var_cfg_path = Path("./site-controller_variants/test_type")
    root_path = Path("./site-controller_variants/root")
    var_test_type_test_path = var_cfg_path / "tests"
    var_root_test_path = root_path / "tests"    
    default_device = Device("site-controller", "test_site", "test_type")
    expected_test = len(list(var_test_type_test_path.glob("**/*.json"))) + len(list(var_root_test_path.glob("**/*.json")))
    expected_cfg = len(list(var_cfg_path.glob("**/*.json"))) + len(list(root_path.glob("**/*.json"))) - expected_test
    if sc_config_path.exists():
        shutil.rmtree(sc_config_path)
    if sc_tests_path.exists():
        shutil.rmtree(sc_tests_path)
    default_device.copy_all_files()
    assert expected_test == len(list(sc_tests_path.glob("**/*.json")))
    assert expected_cfg == len(list(sc_config_path.glob("**/*.json")))

## test cases
## 0 - 'path' field not present
## 1 - 'filename_pattern' field not present
## 2 - 'type' field in 'filename_pattern' not present
## 3 - 'filename_template_field' in 'filename_pattern' not present
## 4 - sequential type with no 'from' field in 'filename_pattern'
## 5 - sequential type with no 'to' field in 'filename_pattern'
## 6 - list type with no 'list' field in 'fieldname_pattern'
@pytest.mark.parametrize("template_obj", [
    ({                                                 "filename_pattern": {"type": "sequential", "filename_template": "test-{{target}}_modbus_server.json", "from": 1, "to": 4}}),
    ({"path": "modbus_server/test_modbus_server.json"                                                                                                                           }),
    ({"path": "modbus_server/test_modbus_server.json", "filename_pattern": {                      "filename_template": "test-{{target}}_modbus_server.json", "from": 1, "to": 4}}),
    ({"path": "modbus_server/test_modbus_server.json", "filename_pattern": {"type": "sequential",                                                            "from": 1, "to": 4}}),
    ({"path": "modbus_server/test_modbus_server.json", "filename_pattern": {"type": "sequential", "filename_template": "test-{{target}}_modbus_server.json",            "to": 4}}),
    ({"path": "modbus_server/test_modbus_server.json", "filename_pattern": {"type": "sequential", "filename_template": "test-{{target}}_modbus_server.json", "from": 1         }}),
    ({"path": "modbus_server/test_modbus_server.json", "filename_pattern": {"type": "list",       "filename_template": "test-{{target}}_modbus_server.json"                    }}),
])
def test_expand_templates_required_key_dne(root_sc_device: Device, template_obj):
    root_sc_device.templates = [template_obj]
    with pytest.raises(KeyError) as ke:
        root_sc_device.expand_templates()
    assert ke.type == KeyError

# check that an error is thrown if the pattern type of afound template is not "sequential" or "list"
def test_expand_templates_invalid_pattern_type(root_sc_device: Device):
    root_sc_device.templates = [{
        "path": "modbus_client/test_modbus_client.json",
        "filename_pattern": {"type": "something else", "filename_template": "ess-controller-{{target}}_site-controller_flexgen_modbus_server.json"}
    }]
    with pytest.raises(ValueError) as ve:
        root_sc_device.expand_templates()
    assert ve.type == ValueError

## test cases
## 0 - sequential template type
## 1 - list template type
## 2 - multiple templates to expand
## 3 - single template with templated replacements
@pytest.mark.parametrize("expected_files, template_objs", [
    (
        ["modbus_client/ess-controller-1_site-controller_flexgen_modbus_server.json", "modbus_client/ess-controller-2_site-controller_flexgen_modbus_server.json"],
        [
            {
                "path": "modbus_client/ess-controller_site-controller_flexgen_modbus_client.json",
                "filename_pattern": {"type": "sequential", "filename_template": "ess-controller-{{target}}_site-controller_flexgen_modbus_server.json", "from": 1, "to": 2}
            }
        ]
    ),
    (
        ["modbus_client/ess-controller-num1_site-controller_flexgen_modbus_server.json", "modbus_client/ess-controller-num2_site-controller_flexgen_modbus_server.json"],
        [
            {
                "path": "modbus_client/ess-controller_site-controller_flexgen_modbus_client.json",
                "filename_pattern": {"type": "list", "filename_template": "ess-controller-{{target}}_site-controller_flexgen_modbus_server.json", "list": ["num1", "num2"]}
            }
        ]
    ),
    (
        [
            "modbus_server/test-1_modbus_server.json",
            "modbus_server/test-2_modbus_server.json",
            "modbus_client/test_alpha_modbus_client.json",
            "modbus_client/test_beta_modbus_client.json",
            "modbus_client/test_gamma_modbus_client.json",
            "modbus_client/test_delta_modbus_client.json",
            "modbus_client/test-modbus_client_24.json",
            "modbus_client/test-modbus_client_25.json",
            "modbus_client/test-modbus_client_26.json",
            "modbus_client/test-modbus_client_27.json",
            "modbus_client/test-modbus_client_28.json",
            "modbus_client/test-modbus_client_29.json",
            "modbus_client/test-modbus_client_30.json",
        ],
        [
            {
                "path": "modbus_server/test_modbus_server.json", 
                "filename_pattern": {"type": "sequential", "filename_template": "test-{{target}}_modbus_server.json", "from": 1, "to": 2}
            },
            {
                "path": "modbus_client/test_modbus_client.json", 
                "filename_pattern": {"type": "list", "filename_template": "test_{{target}}_modbus_client.json", "list": ["alpha", "beta", "gamma", "delta"]}
            },
            {
                "path": "modbus_client/test_modbus_client_2.json", 
                "filename_pattern": {"type": "sequential", "filename_template": "test-modbus_client_{{target}}.json", "from": 24, "to": 30}
            }
        ]
    ),
    (
        ["modbus_client/ess-controller_site-controller_flexgen-1_modbus_client.json", "modbus_client/ess-controller_site-controller_flexgen-2_modbus_client.json"],
        [
            {
                "path": "modbus_client/ess-controller_site-controller_flexgen_modbus_client.json", 
                "filename_pattern": {
                    "type": "sequential", 
                    "filename_template": "ess-controller_site-controller_flexgen-{{target}}_modbus_client.json", 
                    "from": 1, "to": 2
                },
                "templated_replacements": [
                    {"target": "{{ESS_ID}}"}, 
                    {"target": "{{ESS_IP}}", "list": ["test_site-ess-controller-01", "test_site-ess-controller-02"]}, 
                    {"target": "{{FIRST_ESS_COMPONENT}}", "list": ["flexgen_ess_01a", "flexgen_ess_01b"]}, 
                    {"target": "{{SECOND_ESS_COMPONENT}}", "list": ["flexgen_ess_02a", "flexgen_ess_02b"]}
                ]
            }
        ]
    )
])
def test_expand_templates(expected_files: "list[Path]", template_objs: "list[dict]", sc_config_path: Path, root_sc_device: Device):
    # ensures the template file exists in the device's directory before expansion
    for template in template_objs:
        templated_file = sc_config_path / template["path"]
        if not templated_file.exists():
            templated_file.parent.mkdir(parents=True, exist_ok=True)
            with open(templated_file, "w") as file:
                file.write("testing")
    
    root_sc_device.templates = template_objs            
    root_sc_device.expand_templates()
    # checks that files were expanded with proper names
    for expanded_file in expected_files:
        full_expanded_filepath = sc_config_path / expanded_file
        if not full_expanded_filepath.exists():
            assert False, expanded_file
        else:
            full_expanded_filepath.unlink()
    # checks that the template file was deleted
    for templated_file in template_objs:
        full_templated_filepath = sc_config_path / template["path"]
        if full_templated_filepath.exists():
            assert False
    assert True