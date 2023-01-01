

## SetGroupsEK60
- investigating problem with very long writing time to s3
- best to just review the entire `set_groups_ek60` code to make sure I understand everything
- below will note down whatever things worth noteded or requiring additions or changes
- NOT chunked:
    - Provenance group
    - Environment group
    - Sonar group


- test for duplicated ping_time
    - should trigger warning in `SetGroupsEK60.__init__`
    - CODE Q: review error message: seems like one is for when the backscatter_r values are actually the same, and the other is for when the backscatter_r values are NOT the same?
    - Q: is there such check for EK80?
- CODE Q: `water_level` what happens when there is no data in the data file? is it filled by `np.nan` as needed?
- CODE Q: does `pitch/roll/heave` have the `channel` dimension at the moment?


- Need discussion:
    - if to remove `INDEX2POWER` factor from the `backscatter_r` to make it consistent with the angle data variables

- Need code work:
    - EASY: remove the `beam` dimension from `frequency_start` and `frequency_end`
        - this will save a lot of headache in `CalibrateEK80` and `env_params_new`
    - EASY BUT NEED DISCUSSION: remove the `beam` dimension from `equivalent_beam_angle`
    - short circuit the temporary zarr store to the final zarr store in `_set_beam_group1_zarr_vars`
    - right now `p2z = Parsed2Zarr(parser)` is initiated within `open_raw` when `offload_to_zarr=True`, but this makes it very difficult to trace down where `self.parsed2zarr_obj.temp_zarr_dir` is from since it is hard to find in the `SetGroupsEKX` objects. We should change this initialization to within the `SetGroupsEKX` objects





- in `get_transmit_signal`
    - **DONE** the only use of echodata within this function is to get echodata["Sonar/Beam_group1"] except for when passing into `filter_decimate_chirp`
    - **DONE** can pass in `chan_sel` so only assembling transmit signals for channels under consideration
- **DONE** `absorption` should NOT have beam dimension
- **DONE** refactor range functions using the new `range.py`
    - factor out AZFP and EK components
    - use new EK input checking and EK
- **DONE** `get_gain_for_complex` needs refactoring and potentially moved to `utils_EK80.py`
- **DONE** review whether functions under `cal_params.py` require passing in the entire `echodata` object, or just need to use `beam` like those in `ek80_complex.py`
- **DONE** set `waveform_mode` and `encode_mode` as class attributes and simplify methods 
- `_cal_complex_samples` and `get_transmit_signal` need to have an option to allow transmit parameters to vary across pings


### Tests
- `test_compute_Sv_ek80_pc_echoview`
    - this is the test to use for checking pulse compression and computing power
- cal test:
    - make sure the cases where some channels are NOT active can compute and the resultant Sv are not NaN-padded (ie only contains the active channels)


- good docstring sentences to keep:
    ```
    The EK80 echosounder can be configured to transmit
    either broadband (``waveform_mode="BB"``)
    or narrowband (``waveform_mode="CW"``) signals.
    When transmitting in broadband mode, the returned echoes are
    encoded as complex samples (``encode_mode="complex"``).
    When transmitting in narrowband mode, the returned echoes can be encoded
    either as complex samples (``encode_mode="complex"``)
    or as power/angle combinations (``encode_mode="power"``) in a format
    similar to those recorded by EK60 echosounders.
    ```
