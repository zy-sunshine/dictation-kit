import sys
from pydub import AudioSegment
from pydub.silence import split_on_silence

sound_file = AudioSegment.from_wav(sys.argv[1])
#sound_file = AudioSegment.from_raw(sys.argv[1], {'sample_width'})
audio_chunks = split_on_silence(
    sound_file,
    # must be silent for at least half a second
    min_silence_len=300,

    # consider it silent if quieter than -16 dBFS
    silence_thresh=-16
)

for i, chunk in enumerate(audio_chunks):
    out_file = "tmp/chunk{0}.wav".format(i)
    #import ipdb; ipdb.set_trace()
    print("exporting %s %0.2f" % (out_file, chunk.duration_seconds))
    chunk.export(out_file, format="wav")
