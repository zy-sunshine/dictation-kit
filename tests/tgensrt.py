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
        self.index = int(bname.split('-')[-3])

    def parseStartEnd(self):
        bname, ext = splitext(basename(self.fpath))
        start, end = bname.split('-')[-2:]
        return int(start), int(end)

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
                idx += 1
                text = chunk.text.strip()
                if text == '。':
                    continue
                if not text:
                    continue
                start, end = chunk.parseStartEnd()
                hour, minute, sec, ms = self.parseHourMinuteSecondMs(start)
                hour_e, minute_e, sec_e, ms_e = self.parseHourMinuteSecondMs(end)
                fp.write('%s\n' % idx)
                fp.write('%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d\n' %
                    (hour, minute, sec, ms, hour_e, minute_e, sec_e, ms_e))
                fp.write(text)
                fp.write('\n\n')
        print('gen srt: %s' % self.outPath)

g = SrtGenner(sys.argv[1], sys.argv[2])
g.work()
