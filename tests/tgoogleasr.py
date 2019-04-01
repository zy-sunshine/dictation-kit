import sys
import io
import os

# Imports the Google Cloud client library
beta = False
if beta:
    from google.cloud import speech_v1p1beta1 as speech
    from google.cloud.speech_v1p1beta1 import enums
    from google.cloud.speech_v1p1beta1 import types
else:
    from google.cloud import speech
    from google.cloud.speech import enums
    from google.cloud.speech import types

# Instantiates a client
client = speech.SpeechClient()

# The name of the audio file to transcribe
#file_name = os.path.join(os.path.dirname(__file__), 'resources', 'audio.raw')
file_name = sys.argv[1]

# Loads the audio into memory
with io.open(file_name, 'rb') as audio_file:
    content = audio_file.read()
    audio = types.RecognitionAudio(content=content)

config = types.RecognitionConfig(
    encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code='ja-JP',
    #enable_speaker_diarization=True,
    #enable_word_time_offsets=True,
)

# Detects speech in the audio file
response = client.recognize(config, audio)

for result in response.results:
    print(result)
    #print('Transcript: {}'.format(result.alternatives[0].transcript))
