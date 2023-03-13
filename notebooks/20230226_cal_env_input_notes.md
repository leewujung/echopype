
## 2023/02/26: cal/env params overhaul
- for the `EnvParams` class in `env_params_old.py`: seems better to shelf it for now
- clean up code for env and cal params from user inputs or data files

### Cal params
- [x] move `equivalent_beam_angle` to be part of `params_from_beam` in `cal_params.get_cal_params_EK()`
- [x] simplify all `cal_params.py` and `env_params.py` syntax re getting params from user dict or data file
- [x] factor out the input checking component in `calibrate::api()`
    - also check if content overlaps with `echodata.simrad::check_input_args_combination()` and remove overlapping parts
- [x] use `self.cal_params["equivalent_beam_angle"]` for computing `psifc` in `calibrate_ek.py`
    - right now `psifc` is retrieved directly from the Beam group and not from `self.cal_params`, so will be a bug if user provides equivalent_beam_angle to be used
- [x] remove unnecessary channel selection in EK80 calibration code, since `self.cal_params` contains only params for the selected channels (channels in `self.chan_sel`)
    - line 491 in `calibrate_ek`: `out = out - 2 * self.cal_params["sa_correction"].sel(channel=self.chan_sel)`
    - it's actually already selected because `vend` and `beam` are passed into `get_cal_params_EK` with `chan_sel` selected
- [x] do channel selection in `get_env_params_EK80` like in `get_cal_params_EK`?
    - then do not have to do whole bunch of `.sel(channel=self.chan_sel)` arbitrarily
- [x] do channel selection for `self.range_meter` as well when the range is calculated
    - then do not have to do whole bunch of `.sel(channel=self.chan_sel)` arbitrarily
- [x] remove redundant `self.compute_echo_range()` call in `CalibrateEK80` that resulted in extra channels in `self.range_meter`
- [x] clearly list out what are included in `self.cal_params`
    - make the main block in `_cal_complex_samples` cleaner/shorter
    - avoid bug like for `psifc`

### Env params
- [x] the recently reported bug from Lillia Guillet
    - line 417: the check only makes sense if `env_params` is xr.DataArray, so need handling for scalar-only case
- [x] `_harmonize_env_param_time()` should probably be in `env_params.py`?
    - right now in `range.py`
    - moved to `env_params.py` and renamed to `harmonize_env_param_time()` (ie without the leading `_` since it's not a private function anymore)
- [x] harmonize env param along ping time when constructing `self.env_params`
- [x] simplify `get_env_params_*`
    - remove redundancy in code and unnecessary selection of channels for EK60 and AZFP
- [x] tidy up docstring of `env_params.py::get_env_params_*`
- [x] remove `env_params::get_env_params`: not used
- [x] subset channels when constructing `self.env_params` for EK80 data
    - this is doable since `freq` (which is `self.freq_center`) is an input argument in `env_params::get_env_params_EK80` and it also has the right channel subset to be computed
- [x] make sure the added env params to the final Sv/TS datasets are with only the correct subset of channels
    - right now the env params added to the Sv/TS datasets are with *all* channels
    - this should happen naturally when `self.env_params` are subsetted at construction
- [x] need to think about whether it makes sense the store the harmonized env params or the original ones
    - seems to store the harmonized ones are better as data products? since the "recipe" would contain the original form?
    - keep it in the harmonized one for now, will see if need to change later
- [x] retire `EchoData._harmonize_env_param_time()` entirely and use the new one in `env_params.py`
    - this part is related to retiring `EchoData.compute_range()`

### For later
- [ ] move impedance intake to `get_cal_params_EK` ?
    - not doing this for now, since these are not likely to be passed in by the users at the moment -- may change in the future
- [ ] check what's going on with the `beam` dimension
    - likely cannot resolve in this PR since it is related to the data storage format
- [ ] do `compute_echo_range()` in `CalibrateAZFP` within `__init__`
    - right now it is outside of `__init__` because the needed `cal_type` argument is not passed in on the constructor and only passed in in `_cal_power_samples` called under `compute_Sv/TS`



## Others
- [ ] move `_add_params_to_output` to `api::compute_cal()`
    - right now it is done at the end of each calibration function, eg _cal_complex_samples
    - better to have it done once through `cal_obj._add_params_to_output(ds_cal)` at the higher level


### Docs
- list all allowable `cal_params` and `env_params` and describe the behavior
- explicitly list allowable data type for all parameters
    - some variables can be scalar or xr.DataArray
    - most variables can be 






## 2023/02/26: interface with ECS file
- add `ecs_file` as an input argument to CalibrateX classes
    - when `ecs_file` is not None: ignore user input cal_params and env_params
- when `ecs_file` is present:
    - parse the ECS file
    - organize parsed ECS data into xr.DataArray with the correct `channel` coordinates; this step can leverage the cal/env parameter ingestor from the above (under ## Others)
    - set `user_env_dict` as the parsed ECS dict for both `get_env_params_*` and `get_cal_params_*`, and the existing mechanism should *just work*
