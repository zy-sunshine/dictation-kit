import sys
from os import walk
from os.path import splitext, basename, exists as pathexists, join as pathjoin

class TextChunk(object):
    def __init__(self):
        self.fpath = ''
        self.text = ''
        self.index = None
        self.start = 0
        self.end = 0

    def setFilePath(self, fpath):
        self.fpath = fpath
        bname, ext = splitext(basename(self.fpath))
        self.index, self.start, self.end = bname.split('-')[-3:]
        self.index = int(self.index)
        self.start = int(self.start)
        self.end = int(self.end)

class Trans(object):
    def __init__(self, fileListPath):
        self.fileListPath = fileListPath
        self.fileList = []
        self.chunks = []
        self.initGoogleClient()

    def initGoogleClient(self):
        # Imports the Google Cloud client library
        from google.cloud import translate

        # Instantiates a client
        self.translate_client = translate.Client()

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

        self._doTrans()

    def _doTrans(self):
        chunkList = []
        textList = []
        for index, chunk in enumerate(self.chunks):
            text = chunk.text.strip().strip('。').strip()
            if not text:
                continue
            chunkList.append(chunk)
            textList.append(text)

        # The target language
        target = 'zh'

        # Translates some text into Russian
        translations = self.translate_client.translate(
            textList,
            target_language=target)

        for chunk, translation in zip(chunkList, translations):
            fpath = splitext(chunk.fpath)[0] + '-zh.txt'
            with open(fpath, 'wt') as fp:
                transText = translation['translatedText']
                fp.write(transText)

g = Trans(sys.argv[1])
g.work()
