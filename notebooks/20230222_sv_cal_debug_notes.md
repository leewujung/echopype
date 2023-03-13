
## 2023/02/22
- use file: `'../spheroid_echo/sample_data/2018115-D20181213-T094600.raw'`
- test: `test_compute_Sv_ek80_CW_complex_BB_complex` in echopype
- test: `test/test_ek80_bb.py` in pyEchoLab
- pyEchoLab swapped to use `ek80_chirp2` that is verbatim from the CRIMAC repo
- previously pyEchoLab has `ek80_chirp` that is a slightly different implementation
- all channels are:
    ['WBT 714581-15 ES18', 'WBT 714583-15 ES120-7C', 'WBT 714590-15 ES70-7C',
       'WBT 714596-15 ES38-7', 'WBT 714597-15 ES333-7C',
       'WBT 714605-15 ES200-7C']
- BB channels are: ES70-7C, ES38-7
- the rest are CW channels



## 2023/02/23
### Notes
- can test against:
    ```python
    calibration._tx_signal = tx_data  # transmit signal
    calibration._tau_eff = tau_eff  # effective pulse length
    calibration._y_t = y_t  # timestamp of transmit signal
    ```
    ```python
    # code to generate the above
    #  compute effective pulse duration
    if return_pc and raw_data.pulse_form[idx] > 0:
        y_eff = np.convolve(y, np.flipud(np.conj(y))) / np.linalg.norm(y,2) ** 2
    else:
        y_eff = y
    ptxa = np.abs(y_eff) ** 2
    teff = np.sum(ptxa) / (np.max(ptxa) * rx_sample_frequency_decimated)    

    # tx_data: list of y from above
    # tau_eff: array of teff from above
    ```
- `_complex_to_power` is where pyEcholab has the complex data to power (`prx` in echopype) conversion
- pulse compression code in pyEcholab: https://github.com/CI-CMG/pyEcholab/blob/RHT-EK80-Svf/echolab2/instruments/util/simrad_signal_proc.py#L306-L330
    - mathematically identical to echopype implementation
- can test against:
    - `raw_power` in `data_refs.append(raw_power)` holds the pulse compressed power (scaled by impedance voltage divider etc), this is in `_get_sample_data`
- I stepped through all the function sequence to calculate pulse compressed output to compare pyEcholab and echopype implementation and values: the values are very similar and only differ on the order of 1e-7
    - pyEcholab call sequence: `_get_sample_data`/`_complex_to_power`/`_get_complex`
- pyEcholab `EK80._convert_power` has code that are equivalent to the final step in computing `out` in echopype `calibrate_ek._cal_complex_samples`

### Things to change
- [x] BB mode `angle_offset/beamwidth_alongship/athwartship` interpolation
    - for BB we should interpolate using what's stored in `Vendor_specific` group and not those CW ones in `Sonar/Beam_group1`, just like for gain correction
    - can change `get_gain_BB` function to interpolate other variables
    - DONE! new function name `get_param_BB`. Verified values against `cal_parms` in pyEcholab.
- [x] `B_theta_phi_m`
    - gain needs to be corrected by `B_theta_phi_m`
    - [pyEcholab ref](https://github.com/CI-CMG/pyEcholab/blob/RHT-EK80-Svf/echolab2/instruments/EK80.py#L4263-L4274)
- [x] [Accept Zer/Zet from file](https://github.com/CI-CMG/pyEcholab/blob/RHT-EK80-Svf/echolab2/instruments/EK80.py#L2896-L2913)
- [x] default sampling frequency
    - [pyEcholab red](https://github.com/CI-CMG/pyEcholab/blob/RHT-EK80-Svf/echolab2/instruments/EK80.py#L4569-L4580)
- [x] `angle_offset/beamwidth_alongship/athwartship` need to be stored in `self.cal_params` for `get_param_BB` to operate on in cases when no BB param exist
- [x] some checking not working for BB complex only data?
    - `Summer2018--D20180905-T033113.raw` has BB complex only, but the check did not work to say mode="CW" would not work
    - DONE! add a check under `_retrieve_correct_beam_group_EK80` for waveform_mode="CW" but all data are BB
- [x] `sa_correction` needs to be taken into account for CW comde complex data also
    - currently not included in echopype
    - [pyEcholab ref](https://github.com/CI-CMG/pyEcholab/blob/RHT-EK80-Svf/echolab2/instruments/EK80.py#L4326-L4330)
- [x] GPT vs WBT [different effective pulse duration](https://github.com/CI-CMG/pyEcholab/blob/RHT-EK80-Svf/echolab2/instruments/EK80.py#L4245-L4251)
- [x] GPT vs WBT [different index offset along range (range computation)](https://github.com/CI-CMG/pyEcholab/blob/RHT-EK80-Svf/echolab2/instruments/EK80.py#L4297-L4308)
- [x] remove `TVG_CORRECTION_FACTOR` from `range.py`




## 2023/03/01-02
- [x] range computation changes
    - the offset/shift in range that echopype has been using is for TVG compensation only and should NOT be used as actual range -- the range BEFORE the offset/shift is the one to use
    - in pyecholab range computation is done in `get_range_vector`
- [x] only compute range for channel=`chan_sel`, right now it computes range for all channels in the dataset
- [x] drop the `time1` coordinate from `ds_Sv["Sv"]`
    - need to trace down where that gets added
    - this was a regression bug -- resolved by moving the self.env_params harmonizing block further up



## Defer to later:
- [ ] store `sample_offset` in the Vendor-specific group, and use it for range computation
    - for both EK60 and EK80
    - pyecholab EK60 implementation has range_sample dimension starting from -1, not sure why, but tvg offset is still 2, so that would produce a net difference of 1 sample?
    - pyecholab EK80 range is the same as echopype range computation when the tvg offset/shift is not superimposed
- [ ] need to track down the difference between the first 8 samples between echopype and pyecholab/echoview for EK60 Sv data
- [ ] Sv integration test should include:
    - Sv data array dimensions
    - key variables that should exist in compute_Sv output
