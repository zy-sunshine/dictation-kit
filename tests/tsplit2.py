import re
import sys
from acom.utils.cmdwrapper import runcmd

fpath = sys.argv[1]
cmd = 'ffmpeg -i %s -af silencedetect=noise=-30dB:d=0.5 -f null -' % fpath
ret, output = runcmd(cmd)
'''
Run: ffmpeg -i data/01.mp3 -af silencedetect=noise=-30dB:d=0.5 -f null -
ffmpeg version N-88268-g75bd010 Copyright (c) 2000-2017 the FFmpeg developers
  built with gcc 5.4.0 (Ubuntu 5.4.0-6ubuntu1~16.04.9) 20160609
  configuration: --prefix=/home/netsec/ffmpeg_build --pkg-config-flags=--static --extra-cflags=-I/home/netsec/ffmpeg_build/include --extra-ldflags=-L/home/netsec/ffmpeg_build/lib --bindir=/home/netsec/bin --enable-gpl --enable-libass --enable-libfdk-aac --enable-libfreetype --enable-libmp3lame --enable-libopus --enable-libtheora --enable-libvorbis --enable-libvpx --enable-libx264 --enable-nonfree --extra-cflags=-I../nv_sdk --extra-ldflags=-L../nv_sdk --extra-cflags=-I/usr/local/cuda/include/ --extra-ldflags=-L/usr/local/cuda/lib64 --disable-shared --enable-cuda --enable-cuvid --enable-libspeex
  libavutil      56.  0.100 / 56.  0.100
  libavcodec     58.  1.100 / 58.  1.100
  libavformat    58.  0.102 / 58.  0.102
  libavdevice    58.  0.100 / 58.  0.100
  libavfilter     7.  0.101 /  7.  0.101
  libswscale      5.  0.101 /  5.  0.101
  libswresample   3.  0.100 /  3.  0.100
  libpostproc    55.  0.100 / 55.  0.100
[mp3 @ 0x364a9c0] Estimating duration from bitrate, this may be inaccurate
Input #0, mp3, from 'data/01.mp3':
  Metadata:
    genre           : Blues
  Duration: 00:00:31.80, start: 0.000000, bitrate: 128 kb/s
    Stream #0:0: Audio: mp3, 44100 Hz, mono, s16p, 128 kb/s
Stream mapping:
  Stream #0:0 -> #0:0 (mp3 (native) -> pcm_s16le (native))
Press [q] to stop, [?] for help
Output #0, null, to 'pipe:':
  Metadata:
    genre           : Blues
    encoder         : Lavf58.0.102
    Stream #0:0: Audio: pcm_s16le, 44100 Hz, mono, s16, 705 kb/s
    Metadata:
      encoder         : Lavc58.1.100 pcm_s16le
[silencedetect @ 0x365f5a0] silence_start: 4.56776
[silencedetect @ 0x365f5a0] silence_end: 5.43347 | silence_duration: 0.865714
[silencedetect @ 0x365f5a0] silence_start: 14.3637
[silencedetect @ 0x365f5a0] silence_end: 15.5951 | silence_duration: 1.23143
[silencedetect @ 0x365f5a0] silence_start: 21.1294
[silencedetect @ 0x365f5a0] silence_end: 21.7339 | silence_duration: 0.60449
[silencedetect @ 0x365f5a0] silence_start: 23.9767
[silencedetect @ 0x365f5a0] silence_end: 24.7641 | silence_duration: 0.787347
[silencedetect @ 0x365f5a0] silence_start: 27.7384
[silencedetect @ 0x365f5a0] silence_end: 28.4735 | silence_duration: 0.735102
size=N/A time=00:00:31.79 bitrate=N/A speed= 987x
video:0kB audio:2738kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: unknown
'''

class Chunk(object):
    def __init__(self):
        self.start = 0
        self.end = 0

    @property
    def duration(self):
        return self.end - self.start

    def dump(self):
        return 's:%s e:%s d:%s' % (self.start, self.end, self.duration)

    def startWithPad(self, pad=0.25):
        result = self.start - pad
        if result < 0:
            return 0
        else:
            return result

    def endWithPad(self, limit, pad=0.25):
        result = self.end + pad
        if result > limit:
            return limit
        else:
            return result

    def getPadStartEndDur(self, endLimit, pad=0.25):
        start = self.startWithPad(pad)
        end = self.endWithPad(endLimit, pad)
        return start, end, end - start

class ChunkParse(object):
    #Duration: 00:00:31.80
    DURATION_PATTERN = re.compile(r'Duration: (\d{2}):(\d{2}):(\d{2}).(\d{2})')
    def __init__(self, content):
        self.chunks = []
        self.lastChunk = None
        self.content = content
        self.duration = 0

    def parse(self):
        for line in self.content.split('\n'):
            if 'silence_start:' in line:
                tm = line.split('silence_start:')[-1].strip()
                tm = float(tm)
                self.start(tm)
            if 'silence_end:' in line:
                tm = line.split('silence_end:')[-1].split('|')[0].strip()
                tm = float(tm)
                self.stop(tm)
            pattern = self.DURATION_PATTERN.search(line)
            if pattern:
                hour, minute, second, ms = pattern.groups()
                self.duration = int(hour) * 60 * 60 + int(minute) * 60 + int(second) + int(ms) / 1000

    def start(self, tm):
        self.lastChunk = Chunk()
        self.lastChunk.start = tm

    def stop(self, tm):
        self.lastChunk.end = tm
        self.chunks.append(self.lastChunk)
        self.lastChunk = None

parser = ChunkParse(output)
parser.parse()
for chunk in parser.chunks:
    print(chunk.dump())
print(parser.duration)

class Spliter(object):
    def __init__(self, emptyChunks, duration):
        self.emptyChunks = emptyChunks
        self.duration = duration
        self.chunks = []
        self.lastChunk = None

    def parse(self):
        if len(self.emptyChunks) == 0:
            chunk = Chunk()
            chunk.start = 0
            chunk.end = self.duration
            self.chunks = [ chunk ]
            return

        lastEChunk = None
        for index, echunk in enumerate(self.emptyChunks):
            if index == 0 and echunk.start < 0.5:
                lastEChunk = echunk
                continue
            if lastEChunk is None:
                start = 0
            else:
                start = lastEChunk.end
            self.start(start)
            end = echunk.start
            self.stop(end)
            lastEChunk = echunk

        if self.duration - lastEChunk.end > 0.5:
            self.start(lastEChunk.end)
            self.stop(self.duration)

    def start(self, tm):
        self.lastChunk = Chunk()
        self.lastChunk.start = tm

    def stop(self, tm):
        self.lastChunk.end = tm
        self.chunks.append(self.lastChunk)
        self.lastChunk = None

parser = Spliter(parser.chunks, parser.duration)
parser.parse()
for index, chunk in enumerate(parser.chunks):
    #print(chunk.dump())
    # ffmpeg -ss <silence_end - 0.25> -t <next_silence_start - silence_end + 2 * 0.25> -i input.mov word-N.mov
    start, end, dur = chunk.getPadStartEndDur(parser.duration)
    cmd = 'ffmpeg -y -ss %s -t %s -i %s -ac 1 -ar 16000 %s' % \
        (start, dur, fpath, 'tmp/out-%s-%s-%s.wav' % (index, int(chunk.start*1000), int(chunk.end*1000)))
    runcmd(cmd)
print(parser.duration)

# ffmpeg -y  -i 01.mp3 -acodec pcm_s16be -f s16le -ac 1 -ar 16000 01.raw
