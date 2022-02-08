import pyaudio
import numpy as np

maxValue = 2**16
bars = 35
p=pyaudio.PyAudio()
stream=p.open(format=pyaudio.paInt16,channels=1,rate=44100,
              input=True, frames_per_buffer=512)
while True:
    data = np.fromstring(stream.read(512),dtype=np.int16)
    dataL = data*32
    #dataR = data[1::2]
    peakL = np.max(dataL)/maxValue*2
    #peakR = np.abs(np.max(dataR)-np.min(dataR))/maxValue
    lString = "#"*int(peakL*bars)+"-"*int(bars-peakL*bars)
    #rString = "#"*int(peakR*bars)+"-"*int(bars-peakR*bars)
    print("L=[%s]"%(lString))
