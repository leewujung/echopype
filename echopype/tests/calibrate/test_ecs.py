from pathlib import Path
from datetime import datetime

import numpy as np
import xarray as xr

from echopype.calibrate.ecs import ECSParser, ev2ep, check_source_channel_order


data_dir = Path("./echopype/test_data/ecs")


CORRECT_PARSED_PARAMS = {
    "fileset": {
        "SoundSpeed": 1496.0,
        "TvgRangeCorrection": "BySamples",
        "TvgRangeCorrectionOffset": 2.0,
    },
    "sourcecal": {
        "T1": {
            "AbsorptionCoefficient": 0.002822,
            "EK60SaCorrection": -0.7,
            "Ek60TransducerGain": 22.95,
            "Frequency": 18.00,
            "MajorAxis3dbBeamAngle": 10.82,
            "MajorAxisAngleOffset": 0.25,
            "MajorAxisAngleSensitivity": 13.89,
            "MinorAxis3dbBeamAngle": 10.9,
            "MinorAxisAngleOffset": -0.18,
            "MinorAxisAngleSensitivity": 13.89,
            "SoundSpeed": 1480.6,
            "TwoWayBeamAngle": -17.37,
        },
        "T2": {
            "AbsorptionCoefficient": 0.009855,
            "EK60SaCorrection": -0.52,
            "Ek60TransducerGain": 26.07,
            "Frequency": 38.00,
            "MajorAxis3dbBeamAngle": 6.85,
            "MajorAxisAngleOffset": 0.0,
            "MajorAxisAngleSensitivity": 21.970001,
            "MinorAxis3dbBeamAngle": 6.81,
            "MinorAxisAngleOffset": -0.08,
            "MinorAxisAngleSensitivity": 21.970001,
            "SoundSpeed": 1480.6,
            "TwoWayBeamAngle": -21.01,
        },
        "T3": {
            "AbsorptionCoefficient": 0.032594,
            "EK60SaCorrection": -0.3,
            "Ek60TransducerGain": 26.55,
            "Frequency": 120.00,
            "MajorAxis3dbBeamAngle": 6.52,
            "MajorAxisAngleOffset": 0.37,
            "MajorAxisAngleSensitivity": 23.12,
            "MinorAxis3dbBeamAngle": 6.58,
            "MinorAxisAngleOffset": -0.05,
            "MinorAxisAngleSensitivity": 23.12,
            "SoundSpeed": 1480.6,
            "TwoWayBeamAngle": -20.47,
        },
    },
    "localcal": {"MyCal": {"TwoWayBeamAngle": -17.37}},
}

env_params_dict = {
    "sound_speed": [1480.6, 1480.6, 1480.6],
    "sound_absorption": [0.002822, 0.009855, 0.032594],
    "frequency_nominal": [1.8e+04, 3.8e+04, 1.2e+05],
}
CORRECT_ENV_DATASET = xr.Dataset({k: (["channel"], v) for k, v in env_params_dict.items()})

cal_params_dict = {
    "sa_correction": [-0.7, -0.52, -0.3],
    "gain_correction": [22.95, 26.07, 26.55],
    "frequency_nominal": [1.8e+04, 3.8e+04, 1.2e+05],
    "beamwidth_athwartship": [10.82, 6.85, 6.52],
    "angle_offset_athwartship": [0.25, 0.0, 0.37],
    "angle_sensitivity_athwartship": [13.89, 21.970001, 23.12],
    "beamwidth_alongship": [10.9, 6.81, 6.58],
    "angle_offset_alongship": [-0.18, -0.08, -0.05],
    "angle_sensitivity_alongship": [13.89, 21.970001, 23.12],
    "equivalent_beam_angle": [-17.37, -17.37, -17.37],
}
CORRECT_CAL_DATASET = xr.Dataset({k: (["channel"], v) for k, v in cal_params_dict.items()})


def test_convert_ecs():
    # Test converting an EV calibration file (ECS)
    ecs_path = data_dir / "Summer2017_JuneCal_3freq_mod.ecs"

    ecs = ECSParser(ecs_path)
    ecs.parse()

    # Spot test parsed outcome
    assert ecs.data_type == "SimradEK60Raw"
    assert ecs.version == "1.00"
    assert ecs.file_creation_time == datetime(
        year=2015, month=6, day=19, hour=23, minute=26, second=4
    )
    assert ecs.parsed_params == CORRECT_PARSED_PARAMS

    # Test ECS hierarchy
    dict_ev_params = ecs.get_cal_params()

    # SourceCal overwrite FileSet settings
    assert dict_ev_params["T1"]["SoundSpeed"] == 1480.60

    # LocalCal overwrites SourceCal
    assert dict_ev_params["T2"]["TwoWayBeamAngle"] == -17.37

    # Test assembled datasets
    ds_cal, ds_env = ev2ep(dict_ev_params)
    assert ds_cal.identical(CORRECT_CAL_DATASET)
    assert ds_env.identical(CORRECT_ENV_DATASET)


def test_check_source_channel_order():

    ds_in = xr.Dataset(
        {
            "var1": (["channel"], [1, 2, 3]),
            "frequency_nominal": (["channel"], [18000, 38000, 120000]),
        }
    )
    freq_ref = xr.DataArray(
        [38000, 18000, 120000],
        coords={"channel": ["chB", "chA", "chC"]},
        dims=["channel"],
    )

    ds_out = check_source_channel_order(ds_in, freq_ref)

    assert np.all(ds_out["channel"].values == ["chB", "chA", "chC"])  # channel follow those of freq_ref
    assert not "frequency_nominal" in ds_out  # frequency_nominal has been dropped
