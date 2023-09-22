from pathlib import Path
from .utils.ek_raw_io import RawSimradFile, SimradEOF

def split_raw(source_file, storage_options):

    CW_filename = Path(source_file).stem + "_CW.raw"
    FM_filename = Path(source_file).stem + "_FM.raw"

    datagram_all = []

    with RawSimradFile(
        source_file, "r", return_raw=True, storage_options=storage_options
    ) as fid:
        

        while True:
            try:
                datagram_all.append(fid.read(1))
            except SimradEOF:
                break
    
    with open("my_file.raw", "wb") as bf:
        for dgram in datagram_all:
            bf.write(dgram)

    assert 1 == 1