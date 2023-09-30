# Introduction
Maintaining configurations for all the sites a customer has can be extremely tedious and can introduce human error when attempting to “copy-paste” changes made in one site’s configurations to another site. Additionally, most site configurations can be categorized into sub-types where each sub-type only differs by a few changes like rated power, site name, and IP addresses. Variance is a way to minimize human error and centralize configuration storage in release branches by storing the templated configurations, customizing them based on site specific data, and then populating the appropriate site/device folder in the current branch of integration_dev with the site specific configs and/or tests.

## Terminology
Throughout this documentation, certain terms will be used to describe the various files and directories used in Variance. In reference to Figure 1 below, the following terms are defined with examples:

**overarching `/config`** - the very top level config directory in an integration_dev repository

**site directory** - any folder directly under the overarching `config/`; typically corresponds to a site ID (e.g. `flextown/`, `site_id/`, `durham/`, etc.)

**device directory** - the `fleet-manager/`, `site-controller/`, `ess-controller/`, and `twins/` directories directly under a site directory

**device variant directory** - the directory at the same level as the overarching config/ that contains all information about a specific device type’s variants (i.e. `site-controller_variants/`, `ess-controller_variants/`, `fleet-manager_variants/`, `twins_variants/`)

**variant type directory** - all the folders directly under the device variant directories, except for `root/` (e.g. `var_1/`, `ess_type_1/`, `ess_type_2/`)

**target** - the keyword to be replaced in a target replacement sequence

# File Structure

**Figure 1**
```
config/
   data-center/
     fleet-manager/
     dnp3_client/
     variance.yml
   site-name/
     variance.yml
     site-controller/
       config/
       tests/
     ess-controller/
       config/
       tests/
       ...
     twins/
       config/
  ...
site-controller_variants
  root/
    process_1/
      process_1_run.json
    ...
  var_1/
    site_controller/
  ...
ess-controller_variants
  root/
  ess_type_1/
  ess_type_2/
  ...
twins_variants
  root/
fleet-manager_variants
  root/
```

**NOTE**: The `variance.yml` file is the configuration file for the tool and will be discussed later in the Configuration section.

Each major device type has a device variants directory that contains a complete set of configurations for that type. The direct sub-folders of this variants folder can be split into two categories: the `root/` folder which contains all of the common config files across each variant and specific variant type directories (named as the user chooses) which contain the configuration files specific to that variant. In other words: **A COMPLETE SET OF CONFIGURATIONS CAN ONLY BE CREATED USING THE ROOT FILES IN COMBINATION WITH ONE VARIANT’S FILES**. If a device type only has one “type” or variant of configurations, then only the `root/` directory is used and it must contain a full set of configurations. Both the `root/` and variant type directories contain all the necessary sub-folders and sub-files for that device type’s configuration and the folders/files present depend on whether or not they are shared across all variants.

**WARNING**: A `root/` directory is required in every device type’s variants folder, even if there are not variants present

## Example
For example, let’s say we have a customer in North Carolina with one Fleet Manager and two sites each with a single Site Controller. The only differences between the two sites are that Site 1 (Sheep Pasture Site) has a power rating of 2500 kW and has one ESS Controller while Site 2 (Wolfpack Site) has a power rating of 5000 kW and has two ESS Controllers. A majority of the Site Controller configuration files will be the same across the two sites, but certain fields may differ slightly.  Figure 2 is a visual representation of how these sites would be categorized in Variance and Figure 3 is what the `site-controller_variants/` folder might look like.

**Figure 2**
![Example Diagaram](C:\Users\Emily\Repositories\variance\example_diagram.png)

**Figure 3**
```
site-controller_variants/
    root/
        dts/
        ftd/
        scheduler/
        modbus_client/
            ess_1_modbus_client.json
        site_controller/
            assets.json
            sequences.json
        web_ui/
        ...
    2500kW/
        site_controller/
            variables.json
    5000kW/
        site_controller/
            variables.json
        modbus_client/
            ess_2_modbus_client.json
```

# Execution

Variance can be added as a submodule in any integration_dev branch using the following command:

```
git submodule add git@github.com:flexgen-power/variance.git
git submodule update --init
```
**WARNING**: Variance must be executed at the integration_dev repository level

To run Variance with a default configuration only printing warnings to the console:

`python3 variance/variance.py` or `./variance/variance.elf`

Variance can also be ran with a `-l`` flag followed by any one of the following options to indicate the lowest level of logging that will appear on the console: *“debug”, “info”, “warning”, “error”, “critical”*

The execution of Variance can be categorized into four major steps detailed in sections below:

1. Clearing out and Copying Files
2. Template Expansion
3. Target Replacements
4. Numerical Regular Expression Parsing

## 1. Clearing out and Copying Files
The first step Variance takes is to iterate through each device in each site directory inside of the overarching `config/`` and remove the previous configuration and testing files (if there are any). Using the Variance configuration file in the site directory, the root and appropriate variant files are copied into the correct folder in each device directory.

## 2. Template Expansion
If template expansion is indicated in the configuration file, a templated file is in the device configuration. This templated file is then copied multiple times, according to the templating pattern in the configuration file, and if indicated, keywords inside the copies are assigned values based on the templating pattern. This is a way to generate the same file multiple times with minor differences.

## 3. Target Replacement
If replacements are indicated in the configuration file, the next step in Variance is to replace the targets in with the specified value listed in the configuration. Variance will compute the set of all files to be parsed using the include and exclude fields. This is a simple find and replace functionality for configuration and testing files.

## 4. Numerical Regular Expression Parsing
Variance then automatically iterates through all of the device’s testing files and evaluates specific mathematical expressions (e.g. simple multiplication, the formula for Active Voltage Regulation). The tool uses regular expressions to do evaluations that can result in either string or numerical values based upon the surrounding context.

# Configuration
Each site directory typically has a Variance configuration file named `variance.yml.` 

**WARNING**: A configuration file is only **UNNECESSARY** if there are no device type variants **and** the root configuration has no templating or replacements needed for a working configuration

The configuration file has three main optional fields as described below:

- **<device_type>_variant** (string) - indicates the variant folder to supplement the root configuration files

**WARNING**: The `variant` field is only optional IF there are no device variants (only a root/ folder)

- **<device_type>_templates** (list) - a list of templating objects used to generate multiple copies of the same file with slight differences  
    - **path** (string) - the full relative path to the file underneath the device type’s config/ directory (REQUIRED)
    - **filename_pattern** (dict) - an object containing details on how to template the generated files (REQUIRED)
        - **type** (string) -  can be either “sequential” or “list” (REQUIRED)
        - **filename_template** (string) - the variable name of the to-be generated files. The provided filename must include a replacement token which is designated by the string {{target}}. This token determines where in the filename, the unique identifier for each generated file will be inserted. (REQUIRED)
        - **from** (int) - the starting number for sequential filename pattern types (REQUIRED for sequential)
        - **to** (int) - the ending number for sequential filename pattern types (REQUIRED for sequential)
        - **list** (list[string]) - the list of values to use for list filename pattern types (REQUIRED for list)
    - **content_replacements** (list) - a list of dictionary objects containing target keys inside of the templated file’s contents
        - **target** (string) - the string key to replace in the templated files (REQUIRED)
        - **list** (list[string]) - the list of values to be used to replace the above target

**NOTE**: If there is no list field in a `content_replacements` sub-object, the list is assumed to be a sequential list of numbers the same length as the number of files to be generated

**WARNING**: The list field in a `content_replacements` sub-object must be the same length as the number of templated files to be generated

 - **replacements** (list) - a list of objects detailing certain strings in a specific file that should be replaced with another specified value
    - **target** (string) - the string key to replace in the specified files (REQUIRED)
    - **value** (string) - the value to replace the above string key with (REQUIRED)
    - **include** (list[string]) - a list of pathspecs to define files/directory groupings to include in the search for the above target  
    - **exclude** (list[string]) - a list of pathspecs to define files/directory groupings to NOT include in the search for the above target

**NOTE**: `include` will default to [“**/*”], which includes all files in the site’s directory. `exclude` will default to [“variance.yml”] to exclude the site directory’s config file

**NOTE**: For more information on pathspecs and using them with “Glob,” see GitHub’s [pathspec documentation](https://git-scm.com/docs/gitglossary#Documentation/gitglossary.txt-aiddefpathspecapathspec) and this [Example Glob Tester](https://globster.xyz/)

## Example Config
**NOTE**: Templating keys typically use the *{{key_string_here}}* format to prevent undesired replacements

```
site-controller_variant: test_type
ess-controller_variant: ess-type-2

site-controller_templates:
  - path: modbus_client/ess-controller_site-controller_flexgen_modbus_client.json
    filename_pattern:
      type: sequential
      filename_template: ess-controller_site-controller_flexgen-{{target}}_modbus_client.json
      from: 1
      to: 2
    content_replacements:
      - target: "{{ESS_ID}}"
      - target: "{{ESS_IP}}"
        list:
          - "test_site-ess-controller-01"
          - "test_site-ess-controller-02"
      - target: "{{FIRST_ESS_COMPONENT}}"
        list:
          - "flexgen_ess_01"
          - "flexgen_ess_03"
      - target: "{{SECOND_ESS_COMPONENT}}"
        list:
          - "flexgen_ess_02"
          - "flexgen_ess_04"

replacements:
  - target: "{{SITE_ID}}"
    value:  test_site
  - target: "{{EMC_ID}}"
    value:  test_emc
    include:
      - "site-controller/*"
    exclude:
      - "site_controller/site_controller/*"
  - target: "{{EMC_NAME}}"
    value:  TEST EMC
  - target: "{{SITE_NAME}}"
    value:  TEST SITE
  - target: "{{ACUVIM_IP}}"
    value:  test_site-twins-01
  - target: "{{RTAC_IP}}"
    value:  test_site-twins-01
  - target: "{{ACROMAG_IP}}"
    value:  test_site-twins-01
  - target: "{{LOWER_ACTIVE_POI}}"
    value: "-2500"
```

This variance file specifies the following:

- The site’s site-controller is a `test_type` variant and should be loaded with the root & `test_type` site-controller_variant configs, in that order.
- The site’s ess-controller is a `ess-type-2` variant and should be loaded with the root & `ess-type-2` ess-controller_variant configs.
- Site Controller will have a template (`modbus_client/ess-controller_site-controller_flexgen_modbus_client.json`) expanded to two files.
    - `ess-controller_site-controller_flexgen-1_modbus_client.json` will have:
        - {{ESS_ID}} replaced with 1
        - {{ESS_IP}} replaced with 'test_site-ess-controller-01'
        - {{FIRST_ESS_COMPONENT}} replaced with 'flexgen_ess_01'
        - {{SECOND_ESS_COMPONENT}} replaced with 'flexgen_ess_02'
    - `ess-controller_site-controller_flexgen-2_modbus_client.json` will have:
        - {{ESS_ID}} replaced with 2
        - {{ESS_IP}} replaced with `test_site-ess-controller-02`
        - {{FIRST_ESS_COMPONENT}} replaced with 'flexgen_ess_03'
        - {{SECOND_ESS_COMPONENT}} replaced with 'flexgen_ess_04'
- Files matching `site-controller/*` but not `site-controller/site-controller/*` will have {{EMC_ID}} replaced with 'test_emc'.
    - `config/test_site/site-controller/file_1.json` would be included in the replacement.
    - `config/test_site/site-controller/site-controller/file_1.json` would NOT be included in the replacement.
    - `config/test_site/site-controller/modbus_client/client.json` would NOT be included in the replacement.
- All files would have the following replacements made:
    - {{SITE_ID}} → `test_site`
    - {{EMC_NAME}} → `TEST_EMC`
    - {{SITE_NAME}} → `TEST_SITE`
    - {{ACUVIM_IP}} → `test_site-twins-01`
    - {{RTAC_IP}} → `test_site-twins-01`
    - {{ACROMAG_IP}} → `test_site-twins-01`
    - {{LOWER_ACTIVE_POI}} → -2500