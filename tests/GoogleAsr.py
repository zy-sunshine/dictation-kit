import sys
import io
from time import sleep

# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

from os import walk
from acom.utils.cmdwrapper import runcmd
from os.path import splitext, basename, isfile, join as pathjoin, exists as pathexists

class AudioFile(object):
    def __init__(self):
        self.fpath = ''
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

    @property
    def duration(self):
        return self.end - self.start

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
        self.initClient()

    def initClient(self):
        # Instantiates a client
        self.client = speech.SpeechClient()

    def work(self):
        fileList = self.prepareListFile()
        print('file list: %s' % fileList)
        audioFiles = []
        with open(fileList, 'rt') as fp:
            for line in fp.readlines():
                fpath = line.strip()
                audioFile = AudioFile()
                audioFile.setFilePath(fpath)
                audioFiles.append(audioFile)

        largeFiles = []
        audioFiles.sort(key=lambda x: x.index)
        for audioFile in audioFiles:
            if audioFile.duration < 60*1000:
                self.processFileGoogle(audioFile)
            else:
                largeFiles.append(audioFile)

        # process largeFiles with julius
        fileList = 'tmp.list'
        with open(fileList, 'wt') as fp:
            for audioFile in largeFiles:
                fp.write('%s\n' % audioFile.fpath)

        cmd = 'bash run-linux-dnn.sh -input file -filelist %s' % fileList
        ret, output = runcmd(cmd, callback = self)
        self.endFile()  # end last file

    filePart = 'Stat: adin_file: input speechfile:'
    sentencePart = 'sentence1:'
    def parseLine(self, line):
        if self.status in ('idle', 'into_sentence', 'start_fpath') and self.filePart in line:
            self.endFile()
            fpath = line.split(self.filePart)[-1].strip()
            self.startFile(fpath)
            self.status = 'start_fpath'
        if self.status == 'start_fpath' and line.startswith(self.sentencePart):
            self.status = 'into_sentence'
            self.appendText(line[len(self.sentencePart):].strip())

    def writeStdout(self, line):
        self.parseLine(line)

    def writeStderr(self, line):
        pass

    def processFileGoogle(self, audioFile):
        self.startFile(audioFile.fpath)
        if audioFile.duration < 2000:  # < 2 seconds
            content = ''
        else:
            content = self.transFile(audioFile.fpath)
        self.appendText(content)
        self.endFile()

    def transFile(self, file_name):
        # Loads the audio into memory
        with io.open(file_name, 'rb') as audio_file:
            content = audio_file.read()
            audio = types.RecognitionAudio(content=content)

        config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code='ja-JP',
        )

        # Detects speech in the audio file
        response = self.client.recognize(config, audio)
        if not response.results:
            return ''
        else:
            return response.results[0].alternatives[0].transcript

        #uri = 'http://hostdare01.0dayku.com/dictation-kit_tmp/%s' % basename(file_name)
        #print(uri)
        #audio = {'uri': uri}
        #response = self.client.long_running_recognize(config, audio)
        #self.parse = True
        #def callback(operation_future):
        #    # Handle result.
        #    result = operation_future.result()
        #    self.pause = False

        #    #for result in response.results:
        #    #print('Transcript: {}'.format(result.alternatives[0].transcript))
        #    self.tmpText = result.alternatives[0].transcript
        #    print(self.tmpText)
        #response.add_done_callback(callback)
        #metadata = response.metadata()
        #print(metadata)
        #while self.parse:
        #    sleep(0.7)
        #return self.tmpText

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
