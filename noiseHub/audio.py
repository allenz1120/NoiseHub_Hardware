import pyaudio
import numpy as np
import time
import statistics
import math

# ENUMS
LOW_VOLUME_STATE = 0
MEDIUM_VOLUME_STATE = 1
HIGH_VOLUME_STATE = 2

POLLING_INTERVAL = 0.5
SAMPLE_PERIOD = 120 / 4
SAMPLES_PER_PERIOD = SAMPLE_PERIOD / POLLING_INTERVAL
COUNTER_THRESHOLD = 0.75

THRESHOLD_1 = 0.08
THRESHOLD_2 = 0.3
THRESHOLD_3 = 0.6

# Microphone config
maxValue = 2**16
bars = 35
p=pyaudio.PyAudio()
stream=p.open(format=pyaudio.paInt16,channels=1,rate=44100,
              input=True, frames_per_buffer=512)
lString = 0

counter = 0

state = LOW_VOLUME_STATE

thresholds = [THRESHOLD_1, THRESHOLD_2]

num_samples = 0

# Loop audio stream continuously
while True:
    num_samples += 1
    num_samples_remaining = SAMPLES_PER_PERIOD - num_samples

    data = np.fromstring(stream.read(512, exception_on_overflow=False),dtype=np.int16)
    dataL = data*32

    # Calculate current volume level
    volume = np.max(dataL)/maxValue*2
    print(f'volume: {volume}')

    if volume > thresholds[state]:
        if counter == 0:
            start_time = int(time.time())
        counter += 1

    if num_samples_remaining + counter < COUNTER_THRESHOLD or counter > 1 and int(time.time()) - start_time > SAMPLE_PERIOD:
        counter = 0

    print(f'counter: {counter}')

    if counter > SAMPLES_PER_PERIOD * COUNTER_THRESHOLD:
        if state == LOW_VOLUME_STATE:
            state = MEDIUM_VOLUME_STATE
            print('\nSTATE CHANGE: MEDIUM\n')
        if state == MEDIUM_VOLUME_STATE:
            state = HIGH_VOLUME_STATE
            print('\nSTATE CHANGE: HIGH\n')
        counter = 0

    # Visualize current volume level on 0-1 scale
    lString = "#"*int(volume*bars)+"-"*int(bars-volume*bars)
    # print(f'[{lString}]')
    time.sleep(POLLING_INTERVAL)
