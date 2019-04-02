import re
import sys

class TextChunk(object):
    TIME_PATTERN = re.compile(r'^\W*?(\d{2}):(\d{2}):(\d{2}),(\d{3})\W+-->\W+(\d{2}):(\d{2}):(\d{2}),(\d{3})')
    def __init__(self, index):
        self.index = index
        self.texts = []
        self.transText = ''

        self.startHour = 0
        self.startMin = 0
        self.startSec = 0
        self.startMs = 0

        self.endHour = 0
        self.endMin = 0
        self.endSec = 0
        self.endMs = 0

    def fillTimeMatch(self, match, line):
        if not match: return
        (self.startHour, self.startMin, self.startSec, self.startMs,
            self.endHour, self.endMin, self.endSec, self.endMs) = \
            [ int(item) for item in match.groups() ]

    @property
    def text(self):
        return '\n'.join(self.texts)

    def dumpSrtSec(self):
        return '%d\n%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d\n%s\n\n' % \
            (self.index+1, self.startHour, self.startMin, self.startSec, self.startMs,
                self.endHour, self.endMin, self.endSec, self.endMs, self.transOrText())

    def transOrText(self):
        if self.transText:
            return self.transText
        else:
            return self.text

class Trans(object):
    def __init__(self, srtPath, outSrtPath):
        self.srtPath = srtPath
        self.outSrtPath = outSrtPath
        self.chunks = []
        self.initGoogleClient()
        self.lastChunk = None

    def initGoogleClient(self):
        # Imports the Google Cloud client library
        from google.cloud import translate

        # Instantiates a client
        self.translate_client = translate.Client()

    def work(self):
        with open(self.srtPath, 'rt') as fp:
            prevLine = ''
            index = -1
            for origLine in fp.readlines():
                index += 1
                line = origLine.strip()
                # parse time secondly
                match = TextChunk.TIME_PATTERN.search(line)
                if match:
                    self.endChunk(False)
                    if not prevLine.isdigit():
                        raise RuntimeError('match on line %s but prev line is not index number' % (index+1, ))
                    index = int(prevLine) - 1
                    index = max(0, index)
                    self.lastChunk = TextChunk(index)
                    self.lastChunk.fillTimeMatch(match, line)
                elif line:
                    # save text
                    if self.lastChunk:
                        self.lastChunk.texts.append(line)
                prevLine = line
            self.endChunk(True)

        import ipdb; ipdb.set_trace()
        self._doTrans()
        self._dumpSrt()

    def endChunk(self, isLast):
        if self.lastChunk:
            if not isLast:
                self.lastChunk.texts.pop()  # pop the next chunk's number
            self.chunks.append(self.lastChunk)
            self.lastChunk = None

    def _doTrans(self):
        chunkList = []
        textList = []
        for index, chunk in enumerate(self.chunks):
            text = chunk.text.strip().strip('。').strip()
            if not text:
                continue
            chunkList.append(chunk)
            textList.append(text)

        for idx in range(0, len(chunkList), 100):
            start = idx
            end = idx + 100
            self.transPiece(chunkList[start: end], textList[start: end])

    def transPiece(self, chunkList, textList):
        # The target language
        target = 'zh'

        # Translates some text into Russian
        translations = self.translate_client.translate(
            textList,
            target_language=target)

        for chunk, translation in zip(chunkList, translations):
            transText = translation['translatedText']
            chunk.transText = transText

    def _dumpSrt(self):
        with open(self.outSrtPath, 'wt') as fp:
            for chunk in self.chunks:
                fp.write(chunk.dumpSrtSec())

g = Trans(sys.argv[1], sys.argv[2])
g.work()
