ffmpeg -y  -i data/01.mp3  -acodec pcm_s16be -f s16be -ac 1 -ar 16000 data/01.raw
ffmpeg -y  -i data/01.mp3  -ac 1 -ar 16000 data/01.wav
