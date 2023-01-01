# Redesign the Process class for echopype

## General thoughts
- The main thing is to split out the data model and the processing methods
- Seems it would work to have:
    - class EchoData as data model
    - class Process

## Use case
- Think about how we want to use it first, and then how to implement.
- The use cases should consider a separate use of the visualization module which allows user to directly visualize a set of files, in addition to the data model object.

```python
calibration
#  converted data set and visualize the results
from echopype import EchoData
from echopype import Process

# Initialize an EchoData object that handles all communication with memory or storage
#  This is a factory method.
files = ['123.nc', '456.nc', ...]  # list of previously converted raw data files
ed = EchoData(files, data_type='raw')  # input: raw data files from Convert
ed = EchoData(files, data_type='Sv')   # input: Sv files

# Initialize a Process object and operate on the echo data object
proc = Process(model='EK80')
proc.update_env_parameters(sound_speed=1489)  # change environmental parameters
proc.calibrate(ed, cal_type='CW')  calibration
proc.calc_TS(ed)               # calculate TS
proc.remove_noise(ed, method='DH')    # remove noise from Sv, using De Robertis & Higginbottom
proc.calc_MVBS(    # calculate MBVS from Sv
    bin_dict = {'range': 5, 'ping_idx': 30},  # 5 m range bins and 30 ping bins
)               
proc.calc_MVBS(    # calculate MBVS from Sv
    bin_dict = {'range': 5, 'ping_time': '1min'},  # 5 m range bins and 1 min ping_time bins
)               
proc.regrid(   # regrid echo data according to specified params
    range=np.arange(0,50,5), 
    ping_time=some_time_vector,
)

# Below are methods to add
proc.detect_bottom(ed, threshold=1.5)  # detect where bottom is basd on ping-by-ping Sv
ds_db_diff = proc.db_diff(  # dB-differencing, returning DataSet
    ed, 
    th=[('freq1','freq2','th_loA','th_hiA'), 
        ('freq2','freq3','th_loB','th_hiB')
    ]
)

# Plotting
data.plot_echogram(ping_time=slice('2020-05-05', '2020-05-10'))
data.plot_echogram(source='MVBS')
```

```python
# Use case: a user wants to visualize previously saved files, 
#  which can be raw backscatter, Sv, or MVBS.
from echopype.visualize import plot_echogram, plot_bottom
echo_files = ['123.nc', '456.nc', ...]  # files containing echogram type of data to be plotted
bottom = 'bottom_line.nc'  # a DataArray or numpy array containing the bottom line
plot_echogram(echo_files)
plot_bottom(bottom)
```
