import re
import sys
from acom.utils.cmdwrapper import runcmd
from os.path import splitext, exists as pathexists

testOutput = '''
Stat: adin_file: input speechfile: test.wav
Warning: strip: sample 0-45065 has zero value, stripped
STAT: 71800 samples (4.49 sec.)
STAT: triggered: [53266..125066] 4.49s from 00:00:3.33
STAT: ### speech analysis (waveform -> MFCC)
pass1_best:
sentence1:  。
STAT: 30800 samples (1.92 sec.)
STAT: triggered: [125266..156066] 1.92s from 00:00:7.83
STAT: ### speech analysis (waveform -> MFCC)
pass1_best:
WARNING: 00 _default: hypothesis stack exhausted, terminate search now
sentence1:  。
STAT: 1087800 samples (67.99 sec.)
STAT: triggered: [156266..1244066] 67.99s from 00:00:9.77
STAT: ### speech analysis (waveform -> MFCC)
pass1_best:
'''

class TextChunk(object):
    TIME_PATTERN = re.compile(r'^STAT: triggered: \[(\d+)\.\.(\d+)\] ([\d\.]+)s from (\d+):(\d+):(\d+)\.(\d+)')
    SENTENCE_PATTERN = re.compile(r'^sentence(\d+):(.*)$')
    def __init__(self, index):
        self.index = index
        self.timeLine = ''
        self.sentenceLines = []
        self.sentences = []

        self.sampleStart = 0
        self.sampleStop = 0
        self.duration = 0
        self.startHour = 0
        self.startMin = 0
        self.startSec = 0
        self.startMs = 0

    def fillTimeMatch(self, match, line):
        if match:
            self.timeLine = line
            (self.sampleStart, self.sampleStop, self.duration, self.startHour,
                self.startMin, self.startSec, self.startMs) = match.groups()

            self.sampleStart = int(self.sampleStart)
            self.sampleStop = int(self.sampleStop)
            self.duration = float(self.duration)
            self.startHour = int(self.startHour)
            self.startMin = int(self.startMin)
            self.startSec = int(self.startSec)

            if len(self.startMs) < 3:
                self.startMs += (3 - len(self.startMs)) * '0'
            elif len(self.startMs) > 3:
                self.startMs = self.startMs[:3]
            self.startMs = int(self.startMs)
            return

    def fillSentenceMatch(self, match, line):
        if match:
            self.sentenceLines.append(line)
            idx, sentence = match.groups()
            sentence = sentence.strip().strip("。").strip()
            self.sentences.append(sentence)

    DUMP_PATTERN = re.compile(r'^\[(\d+)..(\d+)\]\[(\d+):(\d+):(\d+)[\.,](\d+) ([\d\.]+)\](.*)$')
    def fillDumpMatch(self, match, line):
        (self.sampleStart, self.sampleStop, self.startHour, self.startMin,
            self.startSec, self.startMs, self.duration, text) = match.groups()
        self.sampleStart = int(self.sampleStart)
        self.sampleStop = int(self.sampleStop)
        self.startHour = int(self.startHour)
        self.startMin = int(self.startMin)
        self.startSec = int(self.startSec)
        self.startMs = int(self.startMs)
        self.duration = float(self.duration)
        self.reviseTime()
        self.sentences.append(text.strip())

    def reviseTime(self):
        # revise
        self.startHour = self.startHour % 24
        self.startMin = self.startMin % 60
        self.startSec = self.startSec % 60

    @property
    def text(self):
        return ''.join(self.sentences)

    def dump(self):
        return '[%s..%s][%02d:%02d:%02d.%03d %.2f] %s' % (self.sampleStart,
            self.sampleStop, self.startHour, self.startMin,
            self.startSec, self.startMs, self.duration, self.text)

    def getEndHourMinSecMs(self):
        secs = self.startHour * 60 * 60 + self.startMin * 60 + self.startSec + \
            self.startMs / 1000 + self.duration
        endHour, secs = divmod(secs, 60*60)
        endMin, secs = divmod(secs, 60)
        endSec = int(secs)
        endMs = (secs - endSec) * 1000
        return endHour, endMin, endSec, endMs

    def dumpSrtSec(self, index):
        endHour, endMin, endSec, endMs = self.getEndHourMinSecMs()
        return '%d\n%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d\n%s\n\n' % \
            (index+1, self.startHour, self.startMin, self.startSec, self.startMs,
                endHour, endMin, endSec, endMs, self.text)

class Trans(object):
    def __init__(self, audioFilePath, outFilePath):
        self.audioFilePath = audioFilePath

        self.lastChunk = None
        self.chunks = []
        self.status = 'idle'
        self.chunkIndex = 0
        self.srtIndex = 0
        self.outFilePath = outFilePath
        self.outFile = open(outFilePath, 'wt')
        bpath, ext = splitext(self.outFilePath)
        self.dumpFilePath = bpath + '.log'
        self.dumpFile = open(self.dumpFilePath, 'wt')

    def work(self):
        fileList = self.prepareListFile()
        print('file list: %s' % fileList)
        cmd = 'bash run-linux-dnn.sh -cutsilence -input file -filelist %s' % fileList
        ret, output = runcmd(cmd, callback = self)
        self.endChunk()  # end last file
        #self.parseOutput(output)

    def prepareListFile(self):
        if not pathexists(self.audioFilePath):
            raise RuntimeError('do not exists: %s' % self.audioFilePath)
        bpath, ext = splitext(self.audioFilePath)
        fileListPath = bpath + '.list'
        with open(fileListPath, 'wt') as fp:
            fp.write('%s\n' % self.audioFilePath)
        return fileListPath

    def parseOutput(self, output):
        for line in output.split('\n'):
            self.parseLine(line)
        self.endChunk()

    def parseLine(self, line):
        match = None
        if self.status in ('idle', 'into_sentence', 'start_block'):
            match = TextChunk.TIME_PATTERN.search(line)
            if match:
                self.endChunk()
                self.startChunk()
                self.lastChunk.fillTimeMatch(match, line)
                self.status = 'start_block'

        if self.status == 'start_block':
            match = TextChunk.SENTENCE_PATTERN.search(line)
            if match:
                self.status = 'into_sentence'
                self.lastChunk.fillSentenceMatch(match, line)

    def writeStdout(self, line):
        self.parseLine(line)

    def writeStderr(self, line):
        pass

    def startChunk(self):
        assert(self.lastChunk == None)
        self.lastChunk = TextChunk(self.chunkIndex)
        self.chunkIndex += 1

    def endChunk(self):
        if self.lastChunk:
            self.chunks.append(self.lastChunk)
            self.saveChunk(self.lastChunk)
            self.lastChunk = None

    def parseDump(self, dumpLines):
        index = 0
        for line in dumpLines:
            match = TextChunk.DUMP_PATTERN.search(line)
            if match:
                chunk = TextChunk(index)
                index += 1
                chunk.fillDumpMatch(match, line)
                self.chunks.append(chunk)
                self.saveChunk(chunk)

    def saveChunk(self, chunk):
        dumpStr = chunk.dump()
        print(dumpStr)
        self.dumpFile.write('%s\n' % dumpStr)
        self.dumpFile.flush()
        if not chunk.text.strip():
            return
        self.outFile.write(chunk.dumpSrtSec(self.srtIndex))
        self.srtIndex += 1
        self.outFile.flush()

t = Trans(sys.argv[1], sys.argv[2])
t.work()
#t.parseOutput(testOutput)
#t.endChunk()
#t.parseDump(open(sys.argv[1], 'rt').readlines())
#for chunk in t.chunks:
#    t.saveChunk(chunk)
