import sys
from os import walk
from os.path import splitext, basename, exists as pathexists, join as pathjoin

class TextChunk(object):
    def __init__(self):
        self.fpath = ''
        self.text = ''
        self.index = None

    def setFilePath(self, fpath):
        self.fpath = fpath
        bname, ext = splitext(basename(self.fpath))
        self.index, self.start, self.end = bname.split('-')[-3:]
        self.index = int(self.index)
        self.start = int(self.start)
        self.end = int(self.end)

class SrtGenner(object):
    def __init__(self, fileListPath, outPath):
        self.fileListPath = fileListPath
        self.fileList = []
        self.chunks = []
        self.outPath = outPath

    def work(self):
        for root, dirs, files in walk(self.fileListPath):
            for fname in files:
                fpath = pathjoin(root, fname)
                bname, ext = splitext(fpath)
                if fname.endswith('.wav'):
                    self.fileList.append(fpath)

        for fpath in self.fileList:
            bpath, ext = splitext(fpath)
            txtPath = bpath + '.txt'
            chunk = TextChunk()
            if not pathexists(txtPath):
                print('WARN: not exists %s' % txtPath)
                continue
            with open(txtPath, 'rt') as fp:
                chunk.text = fp.read()
            chunk.setFilePath(fpath)
            self.chunks.append(chunk)

        self.chunks.sort(key=lambda x: x.index)

        self._genSrt()

    def parseHourMinuteSecondMs(self, intms):
        sec, ms = divmod(intms, 1000)
        minute, sec = divmod(sec, 60)
        hour, minute = divmod(minute, 60)
        return hour, minute, sec, ms

    def _genSrt(self):
        with open(self.outPath, 'wt') as fp:
            idx = -1
            for index, chunk in enumerate(self.chunks):
                text = chunk.text.strip().strip('。').strip()
                if not text:
                    continue
                fpath = splitext(chunk.fpath)[0] + '-zh.txt'
                text_zh = ''
                if pathexists(fpath):
                    with open(fpath, 'rt') as fp_zh:
                        text_zh = fp_zh.read()
                idx += 1
                hour, minute, sec, ms = self.parseHourMinuteSecondMs(chunk.start)
                hour_e, minute_e, sec_e, ms_e = self.parseHourMinuteSecondMs(chunk.end)
                fp.write('%s\n' % (idx + 1))
                fp.write('%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d\n' %
                    (hour, minute, sec, ms, hour_e, minute_e, sec_e, ms_e))
                if text_zh:
                    fp.write(text_zh)
                else:
                    fp.write(text)
                fp.write('\n\n')
        print('gen srt: %s' % self.outPath)

g = SrtGenner(sys.argv[1], sys.argv[2])
g.work()
