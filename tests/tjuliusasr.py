import sys
from os import walk
from acom.utils.cmdwrapper import runcmd
from os.path import splitext, basename, isfile, join as pathjoin, exists as pathexists

testOutput = '''
Stat: adin_file: input speechfile: tmp/out1.wav
STAT: 41856 samples (2.62 sec.)
STAT: ### speech analysis (waveform -> MFCC)
pass1_best:  昌弘 さん の 家 に 嫁い で 三 年
sentence1:  昌弘 さん の 家 に 嫁い で 三 年 。

Stat: adin_file: input speechfile: tmp/out2.wav
STAT: 32256 samples (2.02 sec.)
STAT: ### speech analysis (waveform -> MFCC)
pass1_best:  いまだ わたし の 中 に は
WARNING: 00 _default: hypothesis stack exhausted, terminate search now
sentence1:  いまだ わたし の 中庭 。

Stat: adin_file: input speechfile: tmp/out3.wav
STAT: 31488 samples (1.97 sec.)
STAT: ### speech analysis (waveform -> MFCC)
pass1_best:  なに も 変化 が あり ませ ん 。
sentence1:  なに も 変化 が あり ませ ん 。

Stat: adin_file: input speechfile: tmp/out4.wav
STAT: 48768 samples (3.05 sec.)
STAT: ### speech analysis (waveform -> MFCC)
pass1_best:  現在 の わたし は 、 不妊 治療 中
WARNING: 00 _default: hypothesis stack exhausted, terminate search now
sentence1:  現在 の わたし は 、 不妊 治療 中 。

Stat: adin_file: input speechfile: tmp/out-1042-3480340-3480410.wav
STAT: 9120 samples (0.57 sec.)
<input rejected by short input>
'''

class AudioFile(object):
    def __init__(self):
        self.fpath = ''
        self.index = None

    def setFilePath(self, fpath):
        self.fpath = fpath
        bname, ext = splitext(basename(self.fpath))
        self.index = int(bname.split('-')[-3])

class TextChunk(object):
    def __init__(self):
        self.fpath = ''
        self.texts = []

    @property
    def text(self):
        return ''.join(self.texts)

    def dump(self):
        return '%s %s' % (self.fpath, len(self.texts))

class Trans(object):
    def __init__(self, fileListPath):
        self.fileListPath = fileListPath
        self.lastChunk = None
        self.chunks = []
        self.status = 'idle'

    def work(self):
        fileList = self.prepareListFile()
        print('file list: %s' % fileList)
        cmd = 'bash run-linux-dnn.sh -input file -filelist %s' % fileList
        ret, output = runcmd(cmd, callback = self)
        self.endFile()  # end last file
        #self.parseOutput(output)

    def prepareListFile(self):
        if isfile(self.fileListPath):
            return self.fileListPath
        else:
            audioFiles = []
            for root, dirs, files in walk(self.fileListPath):
                for fname in files:
                    fpath = pathjoin(root, fname)
                    bname, ext = splitext(fpath)
                    txtPath = bname + '.txt'
                    if pathexists(txtPath):
                        # omit
                        continue
                    if fname.endswith('.wav'):
                        audioFile = AudioFile()
                        audioFile.setFilePath(fpath)
                        audioFiles.append(audioFile)

            audioFiles.sort(key=lambda x: x.index)
            fileListPath = self.fileListPath.rstrip('/\\') + '.list'
            with open(fileListPath, 'wt') as fp:
                for audioFile in audioFiles:
                    fp.write('%s\n' % audioFile.fpath)
            return fileListPath

    filePart = 'Stat: adin_file: input speechfile:'
    sentencePart = 'sentence1:'
    def parseOutput(self, output):
        for line in output.split('\n'):
            self.parseLine(line)
        self.endFile()

    def parseLine(self, line):
        if self.status in ('idle', 'into_sentence', 'start_fpath') and self.filePart in line:
            self.endFile()
            fpath = line.split(self.filePart)[-1].strip()
            self.startFile(fpath)
            self.status = 'start_fpath'
        if self.status == 'start_fpath' and line.startswith(self.sentencePart):
            self.status = 'into_sentence'
            self.appendText(line[len(self.sentencePart):].strip().strip("。").strip())

    def writeStdout(self, line):
        self.parseLine(line)

    def writeStderr(self, line):
        pass

    def startFile(self, fpath):
        self.lastChunk = TextChunk()
        self.lastChunk.fpath = fpath

    def endFile(self):
        if self.lastChunk:
            self.chunks.append(self.lastChunk)
            self.saveChunk(self.lastChunk)
            self.lastChunk = None

    def appendText(self, text):
        self.lastChunk.texts.append(text)

    def saveChunk(self, chunk):
        print(chunk.dump())
        bpath, ext = splitext(chunk.fpath)
        assert(ext != '.txt')
        txtPath = bpath + '.txt'
        with open(txtPath, 'wt') as fp:
            fp.write(chunk.text)

t = Trans(sys.argv[1])
t.work()
#t.parseOutput(testOutput)
#for chunk in t.chunks:
#    t.saveChunk(chunk)
