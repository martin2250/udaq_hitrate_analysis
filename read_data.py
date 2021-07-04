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

# load C++ implementation and fall back to slow python version
try:
    from util_native.checksum_fletcher import fletcher_16 
except ImportError:
    print('falling back to python implementaion for fletcher checksum', file=sys.stderr)
    def fletcher_16(msg: bytes) -> int:
        sum1 = sum2 = 0
        for i in msg:
            sum1 = ((sum1 + i) % 255)
            sum2 = ((sum2 + sum1) % 255)
        return (sum1 << 8) | sum2

try:
    from util_native.analyze_hitbuf import analyze_hitbuf
except ImportError:
    print('falling back to python implementaion for hitbuffer decoder', file=sys.stderr)
    OBJECT_CODE_PPS_SECOND  = 0xe0
    OBJECT_CODE_PPS_YEAR    = 0xe4
    OBJECT_CODE_TRIG_CONFIG = 0xe5
    OBJECT_CODE_DATA_FORMAT = 0xe6

    def analyze_hitbuf(data_in: bytes) -> Tuple[int, int]:
        '''analyze binary hitbuffer data, return number of seconds and number of hits'''
        # unpack tuples returned by iter_unpack
        words = (value for value, in struct.iter_unpack('<I', data_in))
        # hitbuffer files have the following stucture. to always count hits in a whole number
        # of seconds, we discard the entries marked with X -> subtract two seconds at the end
        # PPS year X
        # PPS second X
        # hits X
        # repeat:
        #    PPS second
        #    hits
        # PPS second X
        # hits X
        seconds = hits = hits_temp = 0
        # decode frames
        try:
            print('start')
            for header in words:
                frame_type = header >> 24
                if frame_type == OBJECT_CODE_PPS_SECOND:
                    # print('PPS second', header & 0x03ffffff)
                    # start counting hits after the second PPS sec 
                    if seconds < 2:
                        hits_temp = 0
                    # store hits after every second to discard all hits after the last PPS second
                    hits = hits_temp
                    seconds += 1
                elif frame_type == OBJECT_CODE_PPS_YEAR:
                    # print('PPS year')
                    pass
                elif frame_type == OBJECT_CODE_TRIG_CONFIG:
                    # skip next word
                    next(words)
                elif frame_type == OBJECT_CODE_DATA_FORMAT:
                    pass
                else: # hit
                    # print('hit')
                    hits_temp += 1
                    # skip remaining words
                    multi = next(words)
                    adc_count = (multi >> 28) & 0xf
                    extra_words = adc_count // 2
                    for _ in range(extra_words):
                        next(words)
        except StopIteration:
            raise ValueError('Incomplete frame at end of data')
        seconds -= 2
        if seconds < 1:
            raise ValueError('too little data')
        return seconds, hits

def decode_cobs(packet: bytes) -> bytes:
    if len(packet) < 4:
        raise ValueError(f'packet too short {packet}')
    packet = cobs.decode(packet)
    cs_calc = fletcher_16(packet[:-2])
    cs_recv, = struct.unpack('>H', packet[-2:])
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
        raise ValueError(f'len(header) = {len(header)} != 2') # stupid old python version
        # raise ValueError(f'{len(header)=} != 2')
    num_blocks, = struct.unpack('<H', header)
    # check last packet for OK
    last_block = packets[-1]
    if last_block != OK_STR:
        raise ValueError(f'last_block= {last_block} is not OK') # stupid old python version
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
    ptime, _, _ = ptime.partition(b'\tCLK:') # remove CLK part
    _, *ptime, _ = ptime.decode().split() # remove TAI: and second of day 
    year, day, h, m, s = map(int, ptime) # convert to int
    time = datetime.datetime(2000 + year, 1, 1, h, m, s) + datetime.timedelta(day - 1)
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
        for m in members:
            if m.type == BinType.HITBUF:
                try:
                    data = decode_cobs_hitfile(tar.extractfile(m.info).read())
                    if len(data) % 4 != 0:
                        raise ValueError('data length not divisible by four')
                    seconds, hits = analyze_hitbuf(data)
                    json.dump({
                        'channel': m.channel,
                        'time': m.time.timestamp(),
                        'hits': hits,
                        'seconds': seconds,
                    }, sys.stdout)
                    sys.stdout.write('\n')
                except Exception as e:
                    print(m.info.name, e, file=sys.stderr)
                    continue
            elif m.type == BinType.MONITOR:
                decode_cobs_monitor(tar.extractfile(m.info).read())


def read_tar_outer(p: Path):
    p = Path(p)
    name, _, _ = p.name.partition('.flat.tar')
    with tarfile.open(p) as tar:
        # decompress inner tgz into memory to speed up random access
        inner = io.BytesIO(gzip.decompress(
            tar.extractfile(name + '.tgz').read()))
        read_tar_inner(inner)


# read_tar_outer('./data-hitbuf/scint-taxi-MicroDAQ_hitbuf_20210114.flat.tar')
# read_tar_outer('./data-hitbuf/scint-taxi-MicroDAQ_hitbuf_20210125.flat.tar')
# read_tar_outer('./data-hitbuf/scint-taxi-MicroDAQ_hitbuf_20210302.flat.tar')

read_tar_outer(sys.argv[1])
