"""
Functions for enhancing the spatial and temporal coherence of data.
"""
from typing import Union

import numpy as np
import pandas as pd
import xarray as xr
from geopy import distance

from ..utils.prov import echopype_prov_attrs
from .mvbs import get_MVBS_along_channels


def _set_MVBS_attrs(ds):
    """
    Attach common attributes.

    Parameters
    ----------
    ds : xr.Dataset
        dataset containing MVBS
    """
    ds["ping_time"].attrs = {
        "long_name": "Ping time",
        "standard_name": "time",
        "axis": "T",
    }

    ds["Sv"].attrs = {
        "long_name": "Mean volume backscattering strength (MVBS, mean Sv re 1 m-1)",
        "units": "dB",
        "actual_range": [
            round(float(ds["Sv"].min().values), 2),
            round(float(ds["Sv"].max().values), 2),
        ],
    }


def compute_MVBS(ds_Sv, range_meter_bin=20, ping_time_bin="20S"):
    """
    Compute Mean Volume Backscattering Strength (MVBS)
    based on intervals of range (``echo_range``) and ``ping_time`` specified in physical units.

    Output of this function differs from that of ``compute_MVBS_index_binning``, which computes
    bin-averaged Sv according to intervals of ``echo_range`` and ``ping_time`` specified as
    index number.

    Parameters
    ----------
    ds_Sv : xr.Dataset
        dataset containing Sv and ``echo_range`` [m]
    range_meter_bin : Union[int, float]
        bin size along ``echo_range`` in meters, default to ``20``
    ping_time_bin : str
        bin size along ``ping_time``, default to ``20S``

    Returns
    -------
    A dataset containing bin-averaged Sv
    """

    # create bin information for echo_range
    range_interval = np.arange(0, ds_Sv["echo_range"].max() + range_meter_bin, range_meter_bin)

    # create bin information needed for ping_time
    ping_interval = (
        ds_Sv.ping_time.resample(ping_time=ping_time_bin, skipna=True).asfreq().ping_time.values
    )

    # calculate the MVBS along each channel
    MVBS_values = get_MVBS_along_channels(ds_Sv, range_interval, ping_interval)

    # create MVBS dataset
    ds_MVBS = xr.Dataset(
        data_vars={"Sv": (["channel", "ping_time", "echo_range"], MVBS_values)},
        coords={
            "ping_time": ping_interval,
            "channel": ds_Sv.channel,
            "echo_range": range_interval[:-1],
        },
    )

    # TODO: look into why 'filenames' exist here as a variable
    # Added this check to support the test in test_process.py::test_compute_MVBS
    if "filenames" in ds_MVBS.variables:
        ds_MVBS = ds_MVBS.drop_vars("filenames")

    # ping_time_bin parsing and conversions
    # Need to convert between pd.Timedelta and np.timedelta64 offsets/frequency strings
    # https://xarray.pydata.org/en/stable/generated/xarray.Dataset.resample.html
    # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Series.resample.html
    # https://pandas.pydata.org/docs/reference/api/pandas.Timedelta.html
    # https://pandas.pydata.org/docs/reference/api/pandas.Timedelta.resolution_string.html
    # https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#dateoffset-objects
    # https://numpy.org/devdocs/reference/arrays.datetime.html#datetime-units
    timedelta_units = {
        "d": {"nptd64": "D", "unitstr": "day"},
        "h": {"nptd64": "h", "unitstr": "hour"},
        "t": {"nptd64": "m", "unitstr": "minute"},
        "min": {"nptd64": "m", "unitstr": "minute"},
        "s": {"nptd64": "s", "unitstr": "second"},
        "l": {"nptd64": "ms", "unitstr": "millisecond"},
        "ms": {"nptd64": "ms", "unitstr": "millisecond"},
        "u": {"nptd64": "us", "unitstr": "microsecond"},
        "us": {"nptd64": "ms", "unitstr": "millisecond"},
        "n": {"nptd64": "ns", "unitstr": "nanosecond"},
        "ns": {"nptd64": "ms", "unitstr": "millisecond"},
    }
    ping_time_bin_td = pd.Timedelta(ping_time_bin)
    # res = resolution (most granular time unit)
    ping_time_bin_resunit = ping_time_bin_td.resolution_string.lower()
    ping_time_bin_resvalue = int(
        ping_time_bin_td / np.timedelta64(1, timedelta_units[ping_time_bin_resunit]["nptd64"])
    )
    ping_time_bin_resunit_label = timedelta_units[ping_time_bin_resunit]["unitstr"]

    # Attach attributes
    _set_MVBS_attrs(ds_MVBS)
    ds_MVBS["echo_range"].attrs = {"long_name": "Range distance", "units": "m"}
    ds_MVBS["Sv"] = ds_MVBS["Sv"].assign_attrs(
        {
            "cell_methods": (
                f"ping_time: mean (interval: {ping_time_bin_resvalue} {ping_time_bin_resunit_label} "  # noqa
                "comment: ping_time is the interval start) "
                f"echo_range: mean (interval: {range_meter_bin} meter "
                "comment: echo_range is the interval start)"
            ),
            "binning_mode": "physical units",
            "range_meter_interval": str(range_meter_bin) + "m",
            "ping_time_interval": ping_time_bin,
            "actual_range": [
                round(float(ds_MVBS["Sv"].min().values), 2),
                round(float(ds_MVBS["Sv"].max().values), 2),
            ],
        }
    )

    prov_dict = echopype_prov_attrs(process_type="processing")
    prov_dict["processing_function"] = "commongrid.compute_MVBS"
    ds_MVBS = ds_MVBS.assign_attrs(prov_dict)
    ds_MVBS["frequency_nominal"] = ds_Sv["frequency_nominal"]  # re-attach frequency_nominal

    return ds_MVBS


def compute_MVBS_index_binning(ds_Sv, range_sample_num=100, ping_num=100):
    """
    Compute Mean Volume Backscattering Strength (MVBS)
    based on intervals of ``range_sample`` and ping number (``ping_num``) specified in index number.

    Output of this function differs from that of ``compute_MVBS``, which computes
    bin-averaged Sv according to intervals of range (``echo_range``) and ``ping_time`` specified
    in physical units.

    Parameters
    ----------
    ds_Sv : xr.Dataset
        dataset containing ``Sv`` and ``echo_range`` [m]
    range_sample_num : int
        number of samples to average along the ``range_sample`` dimension, default to 100
    ping_num : int
        number of pings to average, default to 100

    Returns
    -------
    A dataset containing bin-averaged Sv
    """
    da_sv = 10 ** (ds_Sv["Sv"] / 10)  # average should be done in linear domain
    da = 10 * np.log10(
        da_sv.coarsen(ping_time=ping_num, range_sample=range_sample_num, boundary="pad").mean(
            skipna=True
        )
    )

    # Attach attributes and coarsened echo_range
    da.name = "Sv"
    ds_MVBS = da.to_dataset()
    ds_MVBS.coords["range_sample"] = (
        "range_sample",
        np.arange(ds_MVBS["range_sample"].size),
        {"long_name": "Along-range sample number, base 0"},
    )  # reset range_sample to start from 0
    ds_MVBS["echo_range"] = (
        ds_Sv["echo_range"]
        .coarsen(  # binned echo_range (use first value in each average bin)
            ping_time=ping_num, range_sample=range_sample_num, boundary="pad"
        )
        .min(skipna=True)
    )
    _set_MVBS_attrs(ds_MVBS)
    ds_MVBS["Sv"] = ds_MVBS["Sv"].assign_attrs(
        {
            "cell_methods": (
                f"ping_time: mean (interval: {ping_num} pings "
                "comment: ping_time is the interval start) "
                f"range_sample: mean (interval: {range_sample_num} samples along range "
                "comment: range_sample is the interval start)"
            ),
            "comment": "MVBS binned on the basis of range_sample and ping number specified as index numbers",  # noqa
            "binning_mode": "sample number",
            "range_sample_interval": f"{range_sample_num} samples along range",
            "ping_interval": f"{ping_num} pings",
            "actual_range": [
                round(float(ds_MVBS["Sv"].min().values), 2),
                round(float(ds_MVBS["Sv"].max().values), 2),
            ],
        }
    )

    prov_dict = echopype_prov_attrs(process_type="processing")
    prov_dict["processing_function"] = "commongrid.compute_MVBS_index_binning"
    ds_MVBS = ds_MVBS.assign_attrs(prov_dict)
    ds_MVBS["frequency_nominal"] = ds_Sv["frequency_nominal"]  # re-attach frequency_nominal

    return ds_MVBS


def compute_NASC(
    ds_Sv: xr.Dataset,
    cell_dist: Union[int, float],  # TODO: allow xr.DataArray
    cell_depth: Union[int, float],  # TODO: allow xr.DataArray
) -> xr.Dataset:
    """
    Compute Nautical Areal Scattering Coefficient (NASC) from an Sv dataset.

    Parameters
    ----------
    ds_Sv : xr.Dataset
        A dataset containing Sv data.
        The Sv dataset must contain 'latitude' and 'longitude' as data variables.
    cell_dist: int, float
        The horizontal size of each NASC cell, in nautical miles [nmi]
    cell_depth: int, float
        The vertical size of each NASC cell, in meters [m]

    Returns
    -------
    xr.Dataset
        A dataset containing NASC

    Notes
    -----
    The NASC computation implemented here corresponds to the Echoview algorithm PRC_NASC
    https://support.echoview.com/WebHelp/Reference/Algorithms/Analysis_Variables/PRC_ABC_and_PRC_NASC.htm#PRC_NASC  # noqa
    The difference is that since in echopype masking of the Sv dataset is done explicitly using
    functions in the ``mask`` subpackage so the computation only involves computing the
    mean Sv and the mean height within each cell.

    In addition, here the binning of pings into individual cells is based on the actual horizontal
    distance computed from the latitude and longitude coordinates of each ping in the Sv dataset.
    Therefore, both regular and irregular horizontal distance in the Sv dataset are allowed.
    This is different from Echoview's assumption of constant ping rate, vessel speed, and sample
    thickness when computing mean Sv.
    """
    # Check Sv contains lat/lon
    if "latitude" not in ds_Sv or "longitude" not in ds_Sv:
        raise ValueError("Both 'latitude' and 'longitude' must exist in the input Sv dataset.")

    # Get distance from lat/lon in nautical miles
    ds_Sv = ds_Sv.dropna
    df_pos = ds_Sv["latitude"].to_dataframe().join(ds_Sv["longitude"].to_dataframe())
    df_pos["latitude_prev"] = df_pos["latitude"].shift(-1)
    df_pos["longitude_prev"] = df_pos["longitude"].shift(-1)
    df_latlon_nonan = df_pos.dropna()
    df_latlon_nonan["dist"] = df_latlon_nonan.apply(
        lambda x: distance.distance(
            (x["latitude"], x["longitude"]),
            (x["latitude_prev"], x["longitude_prev"]),
        ).nm,
        axis=1,
    )
    df_pos = df_pos.join(df_latlon_nonan["dist"], how="left")
    df_pos["dist"] = df_pos["dist"].cumsum()
    nan_ping_index = df_pos["dist"].isnull().values  # pings with NaN distance
    df_pos.dropna(subset=["dist"], inplace=True)

    # Find binning indices along distance
    cell_dist = 0.1
    bin_num_dist = np.ceil(df_pos["dist"].max() / cell_dist)
    digitized_dist = np.digitize(df_pos["dist"], np.arange(bin_num_dist) * cell_dist, right=False)
    
    # Find binning indices along depth
    cell_depth = 20

    # Compute mean Sv and mean height

    # TODO: Attach attributes

    # return ds_NASC


def regrid():
    return 1
