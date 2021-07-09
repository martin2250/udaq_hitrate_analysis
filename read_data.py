#!/usr/bin/python3
import datetime
import enum
import gzip
import io
import struct
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Tuple
import json

from cobs import cobs

# load C++ implemenations
import udaq_analysis_lib.analyze_hitbuffer as analyze
from udaq_analysis_lib.fletcher_16 import fletcher_16


@dataclass
class Panel:
    adc_amp: Tuple[float, float] = (float('Nan'), float('Nan')) # stupid old version of pyton
    adc_per_pe_offset: float = float('Nan')
    adc_per_pe_factor_temp: float = float('Nan')
    adc_per_pe_factor_auxdac: float = float('Nan')
    mip_per_pe_offset: float = float('Nan')
    mip_per_pe_factor_temp: float = float('Nan')
    mip_per_pe_factor_auxdac: float = float('Nan')


# from calibration csvs
panels = [
    Panel(adc_amp=(6.571565312524594, 80.94875187527528), adc_per_pe_offset=-144.43994279968206, adc_per_pe_factor_temp=-0.2930746360308953,
          adc_per_pe_factor_auxdac=0.09199106677441772, mip_per_pe_offset=-88.89603311937648, mip_per_pe_factor_temp=-0.27898287333168087, mip_per_pe_factor_auxdac=0.07747924576759614),
    Panel(adc_amp=(6.52838039640283, 77.90388096204346), adc_per_pe_offset=-132.7279728299177, adc_per_pe_factor_temp=-0.29702092978353634,
          adc_per_pe_factor_auxdac=0.0871905626973858, mip_per_pe_offset=-105.5519664621495, mip_per_pe_factor_temp=-0.30153733231838364, mip_per_pe_factor_auxdac=0.08649458802379155),
    Panel(adc_amp=(6.55388838887122, 81.16310634565774), adc_per_pe_offset=-151.18829546041786, adc_per_pe_factor_temp=-0.29198903200246823,
          adc_per_pe_factor_auxdac=0.0936481090852252, mip_per_pe_offset=-95.19458419964486, mip_per_pe_factor_temp=-0.2805599108606021, mip_per_pe_factor_auxdac=0.0809718006821564),
    Panel(adc_amp=(6.508768026385524, 83.9229430665138), adc_per_pe_offset=-144.4245027147568, adc_per_pe_factor_temp=-0.3019536751969425,
          adc_per_pe_factor_auxdac=0.09299748957023715, mip_per_pe_offset=-88.59115319715606, mip_per_pe_factor_temp=-0.2715295748573229, mip_per_pe_factor_auxdac=0.07730171382823496),
    Panel(adc_amp=(6.547014385306461, 80.76710390437852), adc_per_pe_offset=-146.92292609892547, adc_per_pe_factor_temp=-0.3055965917716603,
          adc_per_pe_factor_auxdac=0.09326285661594973, mip_per_pe_offset=-107.12238152982248, mip_per_pe_factor_temp=-0.284873042643401, mip_per_pe_factor_auxdac=0.08624608685437932),
    Panel(adc_amp=(6.561398144439558, 79.28945968739885), adc_per_pe_offset=-135.38163753948064, adc_per_pe_factor_temp=-0.3070578230228417,
          adc_per_pe_factor_auxdac=0.08865548382612648, mip_per_pe_offset=-95.87071993209084, mip_per_pe_factor_temp=-0.2697346672494465, mip_per_pe_factor_auxdac=0.0793254438536431),
    Panel(adc_amp=(6.578555150399217, 81.5053331143242), adc_per_pe_offset=-147.70532417481886, adc_per_pe_factor_temp=-0.31458579686797994,
          adc_per_pe_factor_auxdac=0.09466026981290745, mip_per_pe_offset=-76.27908674971293, mip_per_pe_factor_temp=-0.2493064698108615, mip_per_pe_factor_auxdac=0.0679316819269532),
    Panel(adc_amp=(6.510941373817512, 81.12896068467317), adc_per_pe_offset=-143.33292491599002, adc_per_pe_factor_temp=-0.3156532141564224,
          adc_per_pe_factor_auxdac=0.0938045438530023, mip_per_pe_offset=-79.25182088382198, mip_per_pe_factor_temp=-0.2923868693440639, mip_per_pe_factor_auxdac=0.07643681240096512),
]


def decode_cobs(packet: bytes) -> bytes:
    if len(packet) < 4:
        raise ValueError(f'packet too short {packet}')
    packet = cobs.decode(packet)
    cs_calc = fletcher_16(packet[:-2])
    cs_recv, = struct.unpack('<H', packet[-2:])
    if cs_calc != cs_recv:
        raise ValueError(f'invalid checksum {cs_calc:04X} {cs_recv:04X}')
        # raise ValueError(f'invalid checksum {cs_calc=:04X} {cs_recv=:04X}')
    return packet[1:-2]


OK_STR = b'OK\n\0'


def decode_cobs_hitfile(data_in: bytes) -> bytes:
    packets = [
        decode_cobs(packet)
        for packet in data_in.split(b'\0')
        if len(packet) > 0 and packet != b'\xff'
    ]
    # decode header (single byte with number of blocks)
    header = packets[0]
    if len(header) != 2:
        # stupid old python version
        raise ValueError(f'len(header) = {len(header)} != 2')
        # raise ValueError(f'{len(header)=} != 2')
    num_blocks, = struct.unpack('<H', header)
    # check last packet for OK
    last_block = packets[-1]
    if last_block != OK_STR:
        # stupid old python version
        raise ValueError(f'last_block= {last_block} is not OK')
        # raise ValueError(f'{last_block=} is not OK')
    # check that we have exactly the right number of blocks
    if len(packets) != num_blocks + 2:
        raise ValueError(
            f'wrong number of blocks received:{len(packets)-2}, expected {num_blocks}')
    data = bytearray()
    for block in packets[1:-1]:
        data.extend(block)
    return bytes(data)


def decode_cobs_monitor(data_in: bytes) -> Tuple[datetime.datetime, float]:
    packets = [
        decode_cobs(packet)
        for packet in data_in.split(b'\0')
        if len(packet) > 0 and packet != b'\xff'
    ]
    try:
        # temperature packet usually starts with this TODO: find better criterium
        ptemp = next(p for p in packets if p.startswith(b'0.0000'))
        ptime = next(p for p in packets if p.startswith(b'TAI:'))
    except StopIteration:
        raise ValueError('either temperature or TAI packet not found')
    # decode temperature
    temperature = float(ptemp.rstrip(b'\n\0').decode().split()[1])
    # decode TAI string
    ptime, _, _ = ptime.partition(b'\tCLK:')  # remove CLK part
    _, *ptime, _ = ptime.decode().split()  # remove TAI: and second of day
    year, day, h, m, s = map(int, ptime)  # convert to int
    time = datetime.datetime(2000 + year, 1, 1, h, m,
                             s) + datetime.timedelta(day - 1)
    return time, temperature


class BinType(enum.IntEnum):
    MONITOR = 0
    HITBUF = 1
    CONFIG = 2


@dataclass
class uDaqFile:
    info: tarfile.TarInfo
    channel: int
    time: datetime.datetime
    type: BinType

    def parse(info: tarfile.TarInfo) -> 'uDaqFile':
        udaq, bintype, channel, time = info.name.split('_', maxsplit=3)
        if udaq != 'MicroDAQ':
            raise ValueError('does not start with MicroDAQ')
        if bintype == 'monitor':
            bintype = BinType.MONITOR
        elif bintype == 'hitbuf':
            bintype = BinType.HITBUF
        elif bintype == 'config':
            bintype = BinType.CONFIG
        else:
            raise ValueError('unknown binary type ' + bintype)
        channel = int(channel)
        if 'readout' in time:
            time, _, _ = time.rpartition('_')
        else:
            time, _, _ = time.rpartition('.')
        time = datetime.datetime.strptime(time, '%Y%m%d_%H%M%S')
        return uDaqFile(info, channel, time, bintype)


def read_tar_inner(i: IO[bytes]):
    with tarfile.open(fileobj=i) as tar:
        members = [uDaqFile.parse(info) for info in tar.getmembers()]
        members.sort(key=lambda m: m.time)

        # we always used the same AUXDAC (SiPM voltage) for all hitbuffer measurements ~Marie
        auxdac = 2650
        temperature = [None for _ in range(8)]
        max_adc_counts = 3600
        thresholds_mip = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7]

        for m in members:
            if m.type == BinType.HITBUF:
                # only evaluate hitbuffer measurements when we have a valid soft threshold
                if temperature[m.channel] is None:
                    continue
                try:

                    # concatenate COBS frames
                    data = decode_cobs_hitfile(tar.extractfile(m.info).read())
                    # count cpu triggers
                    baseline_sums, baseline_counts = analyze.get_baseline(
                        data, max_adc_counts)
                    baseline_adc = tuple(
                        s/c for s, c in zip(baseline_sums, baseline_counts))
                    # calculate panel properties
                    panel = panels[m.channel]
                    # pe per adc "gain"
                    adc_per_pe = panel.adc_per_pe_offset
                    adc_per_pe += panel.adc_per_pe_factor_temp * \
                        temperature[m.channel]
                    adc_per_pe += panel.adc_per_pe_factor_auxdac * auxdac
                    # MIP per pe
                    pe_per_mip = panel.mip_per_pe_offset
                    pe_per_mip += panel.mip_per_pe_factor_temp * \
                        temperature[m.channel]
                    pe_per_mip += panel.mip_per_pe_factor_auxdac * auxdac

                    mip_per_adc0 = 1 / (adc_per_pe * pe_per_mip)

                    results = []

                    for threshold_mip in thresholds_mip:
                        seconds, hits = analyze.get_hitrate_thresh(
                            data,
                            panel.adc_amp,
                            baseline_adc,
                            mip_per_adc0,
                            threshold_mip,
                            max_adc_counts,
                        )
                        results.append(hits/seconds)

                    json.dump({
                        'channel': m.channel,
                        'time': m.time.timestamp(),
                        'results': results,
                    }, sys.stdout)
                    sys.stdout.write('\n')
                except Exception as e:
                    print(m.info.name, e, file=sys.stderr)
                    continue
            elif m.type == BinType.MONITOR:
                _, temp = decode_cobs_monitor(tar.extractfile(m.info).read())
                temperature[m.channel] = temp
                json.dump({
                    'channel': m.channel,
                    'time': m.time.timestamp(),
                    'temp': temp,
                }, sys.stdout)
                sys.stdout.write('\n')


def read_tar_outer(p: Path):
    p = Path(p)
    name, _, _ = p.name.partition('.flat.tar')
    with tarfile.open(p) as tar:
        # decompress inner tgz into memory to speed up random access
        inner = io.BytesIO(gzip.decompress(
            tar.extractfile(name + '.tgz').read()))
        read_tar_inner(inner)


if len(sys.argv) > 1:
    read_tar_outer(sys.argv[1])
else:
    # read_tar_outer('./data-hitbuf/scint-taxi-MicroDAQ_hitbuf_20210114.flat.tar')
    # read_tar_outer('./data-hitbuf/scint-taxi-MicroDAQ_hitbuf_20210125.flat.tar')
    read_tar_outer(
        './data-hitbuf/scint-taxi-MicroDAQ_hitbuf_20210302.flat.tar')
