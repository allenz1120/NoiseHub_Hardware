import pyaudio
import numpy as np
import time
import statistics
import math


def audio_loop():
    # ENUMS
    LOW_VOLUME_STATE = 0
    MEDIUM_VOLUME_STATE = 1
    HIGH_VOLUME_STATE = 2

    POLLING_INTERVAL = 0.5          # Seconds per sample
    SAMPLE_PERIOD = 120 / 15         # Seconds per period (/4 for debug purposes - reduce waiting time)
    SAMPLES_PER_PERIOD = SAMPLE_PERIOD / POLLING_INTERVAL

    LOW_MEDIUM_COUNT_PERCENTAGE = 0.25      # Medium state lies between 25% and 75% of threshold trips
    MEDIUM_HIGH_COUNT_PERCENTAGE = 0.75     # High state lies above 75% threshold trips

    RMS_THRESHOLD = 0.08

    # Microphone config
    maxValue = 2**16
    bars = 35
    p=pyaudio.PyAudio()
    stream=p.open(format=pyaudio.paInt16,channels=1,rate=44100,
                input=True, frames_per_buffer=512)

    # Initialize variables
    counter = 0
    state = LOW_VOLUME_STATE
    num_samples = 0

    # Loop audio stream continuously
    while True:
        # Start timer for sending current volume state to AWS
        AWS_timer = int(time.time())

        num_samples += 1                                            # Current period sample count
        num_samples_remaining = SAMPLES_PER_PERIOD - num_samples    # Number of samples remaining in sample period

        # RMS calculation
        data = np.fromstring(stream.read(512, exception_on_overflow=False),dtype=np.int16)
        dataL = data*32

        # Calculate current volume level
        volume = np.max(dataL)/maxValue*2
        # print(f'volume:  {volume:.4f} | state:   {state}')

        # # Reset Conditions
        # num_samples_remaining + counter < SAMPLES_PER_PERIOD * MEDIUM_HIGH_COUNT_PERCENTAGE or
        if (counter > 1 and int(time.time()) - start_time > SAMPLE_PERIOD) or (counter == SAMPLES_PER_PERIOD):
            counter = 0
            num_samples = 0
            print('\n--------COUNTER RESET--------\n')

        # Counter Increase Condition
        if volume > RMS_THRESHOLD:
            if counter == 0:
                print('\n--------COUNTER START--------\n')
                start_time = int(time.time())
            counter += 1

    #    print(f'counter: {counter}      | samples: {num_samples}/{int(SAMPLES_PER_PERIOD)}\n')

        # Increase State: Low to Medium
        # If 25% < counter < 75% threshold trips
        # aka
        # If the counter exceeds the LOW_MEDIUM threshold, but does not exceed the MEDIUM_HIGH threshold
        high_to_low = state == HIGH_VOLUME_STATE and num_samples == SAMPLES_PER_PERIOD and counter < SAMPLES_PER_PERIOD * MEDIUM_HIGH_COUNT_PERCENTAGE and counter > SAMPLES_PER_PERIOD * LOW_MEDIUM_COUNT_PERCENTAGE
        low_to_high = state == LOW_VOLUME_STATE and counter > SAMPLES_PER_PERIOD * LOW_MEDIUM_COUNT_PERCENTAGE and counter < SAMPLES_PER_PERIOD * MEDIUM_HIGH_COUNT_PERCENTAGE
        if (high_to_low) or (low_to_high):
            state = MEDIUM_VOLUME_STATE
            print('\n--------STATE CHANGE: MEDIUM--------\n')
            counter = 0
            num_samples = 0

        # Increase State: Medium to High
        # If counter > 75% threshold trips
        # aka
        # If the counter exceeds the MEDIUM_HIGH threshold
        elif state == MEDIUM_VOLUME_STATE and counter > SAMPLES_PER_PERIOD * MEDIUM_HIGH_COUNT_PERCENTAGE:
            state = HIGH_VOLUME_STATE
            print('\n--------STATE CHANGE: HIGH--------\n')
            counter = 0
            num_samples = 0

        # If the current state is Medium and the counter does not exceed LOW_MEDIUM threshold
        elif state == MEDIUM_VOLUME_STATE and num_samples == SAMPLES_PER_PERIOD and counter < SAMPLES_PER_PERIOD * LOW_MEDIUM_COUNT_PERCENTAGE:
            state = LOW_VOLUME_STATE
            print('\n--------STATE CHANGE: LOW--------\n')
            counter = 0
            num_samples = 0

        # Visualize current volume level on 0-1 scale
        # lString = "#"*int(volume*bars)+"-"*int(bars-volume*bars)
        # print(f'[{lString}]')
        time.sleep(POLLING_INTERVAL)

        if int(time.time()) - AWS_timer > 5:
            # Publish message to server desired number of times.
            # This step is skipped if message is blank.
            # This step loops forever if count was set to 0.
            if args.message:
                if args.count == 0:
                    print ("Sending messages until program killed")
                else:
                    print ("Sending {} message(s)".format(args.count))

                publish_count = 1
                while (True):
        #            message = "{} [{}]".format(args.message, publish_count)
                    audio_state = audio.state
                    print(f'AUDIO_STATE: {audio_state}')

                    message = {'noise': audio_state}

                    # message = makePayload()
                    # message2 = getDistance()
                    # message.update(message2)
                    print("Publishing message to topic '{}': {}".format(args.topic, message))
                    message_json = json.dumps(message)
                    print(message_json)
                    mqtt_connection.publish(
                        topic=args.topic,
                        payload=message_json,
                        qos=mqtt.QoS.AT_LEAST_ONCE)
                    time.sleep(1)
                    publish_count += 1

                    sleep(5)

            # Wait for all messages to be received.
            # This waits forever if count was set to 0.
            if args.count != 0 and not received_all_event.is_set():
                print("Waiting for all messages to be received...")

            received_all_event.wait()
            print("{} message(s) received.".format(received_count))

            # Disconnect
            print("Disconnecting...")
            disconnect_future = mqtt_connection.disconnect()
            disconnect_future.result()
            print("Disconnected!")
