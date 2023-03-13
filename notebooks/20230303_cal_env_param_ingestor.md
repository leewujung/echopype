## 2023/03/03
- [ ] need a cal/env parameter ingestor to handle/organize user input cal/env params:
    - scalar: no change
    - list: does NOT allow because there is no explict channel or frequency correpsondence
    - dict{frequency: value}: does not allow duplications
    - dict{channel: value}: here channel has to use the same channel id as in the echodata `channel` dimension
    - xr.DataArray: no change
    - for the dict and xr.DataArray cases: need to check correspondence with data
        - the channel dimension has to be *identical*: no missing or extra channels/frequencies should exist (in theory can allow extra ones, but seems better to just require things to be identical)
- [ ] sort out the `gain` vs `gain_correction` entries in `cal_params`
    - `gain_correction` is used for EK60, AZFP, and EK80 when `gain` does not exist in the Vendor-specific group for center frequency-based interpolation



- the current `get_param_BB` is used to triage between:
    - interpolate freq-dependent params (gain, angle offset, beamwidth, z_et)
    - or grab a const from a dict


- move all interpolation of cal params to `CalibrateEK80.get_cal_params_EK` so that it'll happen when the cal object is constructed
- the `get_cal_params_*` param can take 3 sources of input
    - user input
    - data file
    - default param (from echopype, set from some references)


- track down what z_et and z_er are: transceiver and transducer impedance? or receiver and transmit impedance?

- make sure use is consistent: `impedance_receive` / `impedance_receiver`





## 2023/03/06

### Things to make sure to pick up
- [x] right now only focus on CalibrateEK80, but need to make sure new routines work for CalibrateEK60/AZFP as well
    - in particular using `self.cal_params` in place of on-the-fly paramter calculations
- [x] completely replace the old `get_cal_params_EK` with `get_cal_params_EK_new`





## 2023/03/07
- [x] add in `sanitize_user_cal_dict` to allow input xr.DataArray to be of dimensions `(cal_channel_id, cal_frequency)`
    - right now only allow input xr.DataArray to be of dimension `channel`
- [x] add test for `get_cal_params_EK` and `get_cal_params_AZFP`
    - test to ensure user cal_params dict intake is correct: `test_get_cal_params_AZFP` ensures this
    - `test_get_cal_params_EK` only tests for additional cases

- add test for get_vend_cal_params_power

- consider what to do with the `ping_time` dimension that is attached with `self.freq_center` for BB data
    - this adds computational complexity, needed only when there is ping-by-ping changes
    - can put in a flag in `compute_Sv` and `compute_TS` to opt out of allowing ping-by-ping changes if users know the data are "simple" such that there is no ping-by-ping variation of cal and env params