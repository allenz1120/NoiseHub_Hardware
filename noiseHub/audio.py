import pyaudio
import numpy as np
import time
import statistics

# Microphone config
maxValue = 2**16
bars = 35
p=pyaudio.PyAudio()
stream=p.open(format=pyaudio.paInt16,channels=1,rate=44100,
              input=True, frames_per_buffer=512)
lString = 0

# Loop audio stream continuously
while True:
    data = np.fromstring(stream.read(512, exception_on_overflow=False),dtype=np.int16)
    dataL = data*16

    # Calculate current volume level
    volume = np.max(dataL)/maxValue*2
    print(f'volume: {volume}')

    # Visualize current volume level on 0-1 scale
    lString = "#"*int(volume*bars)+"-"*int(bars-volume*bars)
    print(f'[{lString}]')
