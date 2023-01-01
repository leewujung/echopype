# Re-design the Convert class for echopype

## File conversion: UI
- Have a UI class to handle things for conversion: setting parameters and model type etc
    - combining the current `convert.py` with some functions in `convertbase.py`
    - but it would be nice to enable syntax like:
        ```python
        ec = echopype.Convert(filename)
        ec.set_param({'param1': value2, 'param2': value2, ...})
        ```
    - the params are things like: 
        - platform_name, platform_type, platform_code_ICES
        - echosounder model
        - xml_path for AZFP
    - `raw2nc()` --> `to_netcdf()` amd `raw2zarr()` --> `to_zarr()`
    - `combine_opt` should be passed through the UI
- Find the common set of variables for EK60/EK80/AZFP that needs to be in `__init__` of `ConvertBase`
    - currently quite a few are defined only in the child classes EK60/EK80 and but are resetted in `reset_var` in the parent class
- Remove `reset_vars()` because now the conversion of each file would be done by separate instances of, say, `ConvertEK60`, instead of within one instance of `ConvertEK60`.
    - pseudo code for `.to_netcdf()` under the hood:
        ```python
        # sequential or parallel conversion
        if sequential:
            for file in self.source_file:
                conversion
                convert_indiv_file()
        elif parallel:
                conversion
                # here using the dask syntax but may use something else
                delayed(convert_indiv_file())

        # combine files if needed
        if combine_opt:
            self._combine_files()  # all or GPS only
        ```
- Note GPS info is wrapped in the RAW datagram of each ping for EK60, but is stored in separate NME datagram for EK80. Therefore, for EK80, GPS data extraction can be a lot faster by bypassing all other datagrams. For EK60 it'll really just be not saving the backscatter data -- which is nice too.


### Class attributes
- `sonar_model`: type of echosounder
- `xml_file`: path to xml file (AZFP only)
    - users will get an error if try to set this directly for EK60 or EK80 data
- `source_file`: input file path or list of input file paths
- `output_file`: converted file path or list of converted file paths
- `_source_path`: for convenience only, the path is included in source_file already; user should not interact with this directly
- `_output_path`: for convenience only, the path is included in output_file already; , user should not interact with this directly
- `_conversion_params`: a dictionary of conversion parameters, the keys could be different for different echosounders. This dictionary is set by the `set_param` method.
    - need to make sure users cannot set these params directly and will get a message asking them to use `set_param` if they try.
- `data_type`: type of data to be converted into netcdf or zarr. 
    - default to 'all'
    - 'GPS' are valid for EK60 and EK80 to indicate only GPS related data (lat/lon and roll/heave/pitch) are exported.
    - 'XML' is valid for EK80 data only to indicate when only the XML condiguration header is exported.
- `combine_opt`
- `compress_opt`
- `source_timestamp_pattern`: regex pattern for timestamp encoded in filename
    - EK60 and EK80: `'(?P<survey>.+)?-?D(?P<date>\w{1,8})-T(?P<time>\w{1,6})-?(?P<postfix>\w+)?.raw'`
    - AZFP: **write this pattern!**
    
### Class methods
- `set_source()`
- `set_param()`
- `to_netcdf()` and `to_zarr()`, with options and default values: 
    - save_path
    - combine_opt=False
    - overwrite=False
    - compress=True
    - data_type='all', 'GPS' or 'CONFIG_XML'
- `_validate_path()` should be a function in the UI class instead of in `ConvertBase`
- `_convert_indiv_file()`: something like below
    ```python
    def convert_indiv_file(ff, path_to_converted_file, format):
    converter = ConvertEK60(ff)  # use echosounder-specific object
    converter.load_raw()
    converter.save(path_to_converted_file, format)
    ```
- `_combine_files()` for when `combine_opt=True`


### Use case

```python
ec = echopype.Convert()

# set source files
ec.set_source(
    files=[FILE1, FILE2, FILE3],  # file or list of files
    model='EK80',       # echosounder model
    # xml_path='ABC.xml'  # optional, for AZFP only
    )

# set parameters that may not already in source files
ec.set_param({
    'platform_name': 'OOI', 
    'platform_type': 'mooring'
    })

conversion
ec.to_netcdf()

conversion
ec.to_netcdf(combine=True, save_path='s3://AB/CDE')

# get GPS info only (EK60, EK80)
ec.to_netcdf(data_type='GPS')

# get configuration XML only (EK80)
ec.to_netcdf(data_type='CONFIG_XML')
```





## File conversion: conversion objects
- Add another level of inheritance for EK60 and EK80:
    - `ConvertBase` --> `ConvertEK` --> `ConvertEK60`/`ConvertEK80`
    - this will help us manage the overlapping components between EK60 and EK80
- Methods in ConvertXXX classes
    - `save()`: input arguments: file_format, save_path=None, overwrite=False, compress=True
        - this object should initiate a `SetGroups` object to save groups into netcdf or zarr
        - Refactor the `SetGroups` class to absorb the echosounder-specific dictionary construction operations under the following current methods:
            - `_set_toplevel_dict()`
            - `_set_env_dict()`
            - `_set_prov_dict()`
            - `_set_sonar_dict()`
            - `_set_platform_dict()`
            - `_set_nmea_dict()`
            - `_set_beam_dict()`
            - `_set_vendor_dict()`: not needed for EK60, rename for AZFP
            - `_set_groups()`: don't need this anymore
    - `load_raw()`: parse the raw data file (format: .RAW for EK60/EK80, .A10 for AZFP)
        - from: `load_ek60_raw` in EK60, `load_ek80_raw` in EK80, `_parse_raw()` in AZFP
    - `_copy_groups()`: the original `copyfiles()`, used to duplicate most groups in the file when a second has to be created when range_bin change over time
    - All echosounders:
        - `_print_status()`: add this for EK60 and EK80, now the printing command is embedded in `load_ek60_raw` and `load_ek80_raw`
        - `_check_env_param_uniqueness()`: currently only implemented for AZFP (`check_uniqueness()`), we need this for EK60 for the envionmental data wrapped within each RAW datagram
    - EK60 and EK80:
        - `_read_datagrams()`
        - `_append_channel_ping_data()`: currently only in EK60, need to add this for EK80 so that the long appending section in `_read_datagrams()` can be abstracted out to this function
        - `_split_by_range_group()`: currently only implemented in EK60
        - `_check_ping_channel_match()`: add this method to make sure that the number of RAW datagrams loaded are integer multiples of the number of channels.
        - `_clean_channel()`: add this to remove channels that are empty, _before_ constructing the group dictionaries
    - EK80:
        - `_sort_ch_bb_cw`: renamed from `_sort_ch_ids()`: sorts the channel ids into broadband and continuous wave channel ids
    - AZFP:
        - `loadAZFPxml()`
        - `_get_fields()`
        - `_split_header()`
        - `_add_counts()`
        - `_print_status()`
        - `_check_uniqueness()`
        - `_parse_raw()` --> change to `load_raw()`, it should be a public method
        - `_get_ping_time()`
        - `_calc_Sv_offset()`
        - `_set_vendor_specific_dict()` --> `_set_vendor_dict()`
    - Functions to remove: since now the conversion will only be for 1 file at a time within the ConvertXXX objects, these 2 functions can be absorbed into `save()`
        - `_export_nc()`
        - `_export_zarr()`

### Class attributes
- ConvertBase
    ```python
    # Attributes from convertUI
    self.source_file = files
    self.ui_param = params
    self.compress = compress
    self.overwrite = overwrite
    ```
- ConvertEK
    ```python
    # Attributes for parsing file
    self.config_datagram = None
    self.nmea_data = NMEAData()  # object for NMEA data
    self.metadata_dict = {}   # dictionary to store metadata
    self.power_dict = {}      # dictionary to store power data
    self.angle_dict = {}      # dictionary to store angle data
    self.ping_time = []       # list to store ping time
    self.timestamp_pattern = re.compile(regex)  # regex pattern used to grab datetime embedded in filename
    self.nmea_gps_sentence = nmea_gps_sentence  # select GPS datagram in _set_platform_dict()
    self.num_range_bin_groups = None    # number of range_bin groups
    # Methods
    def parse_raw()  # parse the source file
    def print()
    def _print_status()
    def _check_env_param_uniqueness()
    def _check_tx_param_uniqueness()
    def _read_datagrams()
    def _append_channel_ping_data()
    def _split_by_range_group()
    def _check_ping_channel_match()
    def _clean_channel()
    ```
- ConvertEK60
    ```python
    # Storage variables
    self.CON1_datagram = None    # storage for CON1 datagram for ME70
    self.tx_sig = {}   # dictionary to store transmit signal parameters and sample interval

    # Variables used in EK60 parsing

    ```
    - we shouldn't need `power_dict_split`, `angle_dict_split` and `ping_time_split`, and can just get the values from the original corressponding storage values `power_dict`, `angle_dict`, `ping_time`
    - `ping_slice` is not used, can safely remove
    - `metadata_dict`: renamed from `ping_data_dict` to store metadata
    - `num_range_bin_groups`: renamed from `range_lengths`: number of different range_bins
    - `timestamp_pattern`: will stay but will be set in the convert UI class
    - `nmea_gps_sentence`: will stay but will be set in the convert UI class
    - not sure why ine 219 would work since tx_num seems not have neen set here
    - `tx_sig`: need to figure out how to deal with the case when one of the parameters [pulse_length, transmit_power, bandwidth, sample_interval] change in the middle of the file: currently we do not deal with this case
- ConvertEK80
    ```python
    # Initialize file parsing storage variables
    self.complex_dict = {}  # dictionary to store complex data
    self.n_complex_dict = {}  # dictionary to store the number of beams in split-beam complex data
    self.environment = {}   # dictionary to store environment data
    self.parameters = defaultdict(dict)   # Dictionary to hold parameter data
    self.mru_data = defaultdict(list)     # Dictionary to store MRU data (heading, pitch, roll, heave)
    self.fil_coeffs = defaultdict(dict)   # Dictionary to store PC and WBT coefficients
    self.fil_df = defaultdict(dict)       # Dictionary to store filter decimation factors
    self.ch_ids = []                      # List of all channel ids
    self.recorded_ch_ids = []
    ```
    - `metadata_dict`: renamed from `ping_data_dict` to store metadata
    - line 89 block should use specific index assignment for each channel instead of doing .append
    - simplify the calls `current_parameters['channel_id']` to `ch_id = current_parameters['channel_id']` and then just use ch_id, to increase code readbility
    - line 184 block can be substitute by `self.parameters[ch_id] = defaultdict(list)`
    - not sure why line 204-205: seems like can just use `self.recorded_ch_ids`and get rid of `self.ch_ids`?




```python
x = SetGroups(ConvertEK60_object)
SetGroupsEK60
SetGroupsAZFP

x = SetGroupsEK60()
x.save_beam_group(dict )

```
