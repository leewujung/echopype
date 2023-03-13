# 2023/03/09
- [x] move `_compute_angle_from_complex` to top of `split_beam_angle.py`
- [ ] `get_angle_complex_CW` should allow for other `beam_type` in addition to `beam_type=1`
- [ ] `_get_offset` in split angle routines can be eliminated by using `cal_params` stored with the `ds_Sv` dataset
    - this way user input cal values are incorpoated naturally
    - currently this would result in a buggy situation since `angle_offset` is only pulled from data and not user supplied dict
- revise `get_angle_complex_BB_nopc`
    - use `angle_offset_*` from `ds_Sv/TS` directly
    - do not have to pass in `ed` is passing in `ds_beam`
- add `angle_sensitivity_*` to defined cal params stored in `ds_Sv`
- change sequence of waveform and encode mode in function names
    - eg `get_angle_power_CW` to `get_angle_CW_power`


# Later
- add attributes to split-beam angles



# pyecholab
_get_param_data
- scaling of `angle_offset_alongship/athwartship` and `beam_width_alongship/athwartship`: https://github.com/CI-CMG/pyEcholab/blob/40aa1fe0f874caaddd85918f814e834e802f6c2f/echolab2/instruments/EK80.py#L4749-L4779
- scaling of `angle_sensitivity_alongship/athwartship`: https://github.com/CI-CMG/pyEcholab/blob/40aa1fe0f874caaddd85918f814e834e802f6c2f/echolab2/instruments/EK80.py#L4782-L4820