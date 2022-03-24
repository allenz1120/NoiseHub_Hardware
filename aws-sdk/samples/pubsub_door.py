# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

import argparse
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
import sys
import threading
import time
from uuid import uuid4
import json
sys.path.insert(1, '/home/pi/NoiseHub_Hardware/noiseHub')
from thermistor import read_temp

# This sample uses the Message Broker for AWS IoT to send and receive messages
# through an MQTT connection. On startup, the device connects to the server,
# subscribes to a topic, and begins publishing messages to that topic.
# The device should receive those same messages back from the message broker,
# since it is subscribed to that same topic.

parser = argparse.ArgumentParser(description="Send and receive messages through and MQTT connection.")
parser.add_argument('--endpoint', required=True, help="Your AWS IoT custom endpoint, not including a port. " +
                                                      "Ex: \"abcd123456wxyz-ats.iot.us-east-1.amazonaws.com\"")
parser.add_argument('--port', type=int, help="Specify port. AWS IoT supports 443 and 8883.")
parser.add_argument('--cert', help="File path to your client certificate, in PEM format.")
parser.add_argument('--key', help="File path to your private key, in PEM format.")
parser.add_argument('--root-ca', help="File path to root certificate authority, in PEM format. " +
                                      "Necessary if MQTT server uses a certificate that's not already in " +
                                      "your trust store.")
parser.add_argument('--client-id', default="test-" + str(uuid4()), help="Client ID for MQTT connection.")
parser.add_argument('--topic', default="test/topic", help="Topic to subscribe to, and publish messages to.")
parser.add_argument('--message', default="Hello World!", help="Message to publish. " +
                                                              "Specify empty string to publish nothing.")
parser.add_argument('--count', default=10, type=int, help="Number of messages to publish/receive before exiting. " +
                                                          "Specify 0 to run forever.")
parser.add_argument('--use-websocket', default=False, action='store_true',
    help="To use a websocket instead of raw mqtt. If you " +
    "specify this option you must specify a region for signing.")
parser.add_argument('--signing-region', default='us-east-1', help="If you specify --use-web-socket, this " +
    "is the region that will be used for computing the Sigv4 signature")
parser.add_argument('--proxy-host', help="Hostname of proxy to connect to.")
parser.add_argument('--proxy-port', type=int, default=8080, help="Port of proxy to connect to.")
parser.add_argument('--verbosity', choices=[x.name for x in io.LogLevel], default=io.LogLevel.NoLogs.name,
    help='Logging level')

# Using globals to simplify sample code
args = parser.parse_args()

io.init_logging(getattr(io.LogLevel, args.verbosity), 'stderr')

received_count = 0
received_all_event = threading.Event()

# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
        resubscribe_results = resubscribe_future.result()
        print("Resubscribe results: {}".format(resubscribe_results))

        for topic, qos in resubscribe_results['topics']:
            if qos is None:
                sys.exit("Server rejected resubscribe to topic: {}".format(topic))


# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    print("Received message from topic '{}': {}".format(topic, payload))
    global received_count
    received_count += 1
    # if received_count == args.count:
    received_all_event.set()

if __name__ == '__main__':
    # Spin up resources
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

    proxy_options = None
    if (args.proxy_host):
        proxy_options = http.HttpProxyOptions(host_name=args.proxy_host, port=args.proxy_port)

    if args.use_websocket == True:
        credentials_provider = auth.AwsCredentialsProvider.new_default_chain(client_bootstrap)
        mqtt_connection = mqtt_connection_builder.websockets_with_default_aws_signing(
            endpoint=args.endpoint,
            client_bootstrap=client_bootstrap,
            region=args.signing_region,
            credentials_provider=credentials_provider,
            http_proxy_options=proxy_options,
            ca_filepath=args.root_ca,
            on_connection_interrupted=on_connection_interrupted,
            on_connection_resumed=on_connection_resumed,
            client_id=args.client_id,
            clean_session=False,
            keep_alive_secs=30)

    else:
        mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=args.endpoint,
            port=args.port,
            cert_filepath=args.cert,
            pri_key_filepath=args.key,
            client_bootstrap=client_bootstrap,
            ca_filepath=args.root_ca,
            on_connection_interrupted=on_connection_interrupted,
            on_connection_resumed=on_connection_resumed,
            client_id=args.client_id,
            clean_session=False,
            keep_alive_secs=30,
            http_proxy_options=proxy_options)

    print("Connecting to {} with client ID '{}'...".format(
        args.endpoint, args.client_id))

    connect_future = mqtt_connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    print("Connected!")

    # Subscribe
    print("Subscribing to topic '{}'...".format(args.topic))
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=args.topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received)

    subscribe_result = subscribe_future.result()
    print("Subscribed with {}".format(str(subscribe_result['qos'])))

    # Lidar Code
    from smbus2 import *
    import time
    DEFAULT_ADDRESS = 0x62  # Address of the device
    # Internal registers
    ACQ_COMMAND = 0x00  # W: 0x00 Reset all registers to default
    # W: 0x03 Measure distance (no correction)
    # W: 0x04 Measure distance (Bias correction)
    ACQ_CONFIG_REG = 0x04  # R/W: Configuration of the device
    STATUS = 0x01  # R: Status register of the device
    DISTANCE_OUTPUT = 0x8f  # R: Distance measurement in cm (2 Bytes)
    # R: Velocity measurement in cm/s (1 Byte, 2's complement)
    VELOCITY_OUTPUT = 0x09
    POWER_CONTROL = 0x65  # R/W: Configure power mode of the device
    SIG_COUNT_VAL = 0x02  # R/W: Max times a pulse can be sent
    IDLE_STATE = 0
    ENTRY_STATE = 1
    EXIT_STATE = 2

    """
    Interface for the Garmin Lidar-Lite v3
    """


    class Lidar:
        """
        @:param SMBus, a bus for the device to use
        """

        def __init__(self, bus=None):
            if bus is None:
                self.bus = SMBus(1)
            else:
                self.bus = bus
            self.is_on = False  # Represents the on/off state of the receiver circuit

        """
        Take one measurement in cm, if the receiver circuit is disabled, it will enable the circuit before
        taking a distance measurement
        If taking many measurements, it is recommended to take a bias corrected measurement every 100 readings
        @:param: bias_correction boolean, determines if measurement uses bias correction or not
        @:return int distance in cm
        """

        def read_distance(self, bias_correction=True):
            if not self.is_on:
                self.power_on()
            if bias_correction:
                # Write 0x04 to 0x00 for bias corrected measurement
                self.bus.write_byte_data(DEFAULT_ADDRESS, ACQ_COMMAND, 0x04)
            else:
                # Write 0x03 to 0x00 for no bias correction
                self.bus.write_byte_data(DEFAULT_ADDRESS, ACQ_COMMAND, 0x03)
            # Wait for device to receive distance reading
            self._wait_for_ready_()
            # time.sleep(1)
            # Read HIGH and LOW distance registers
            #distance = self.bus.read_i2c_block_data(DEFAULT_ADDRESS, DISTANCE_OUTPUT, 2)
            low = self.bus.read_byte_data(DEFAULT_ADDRESS, 0x10)
            high = self.bus.read_byte_data(DEFAULT_ADDRESS, 0x11)
            #print("HELLO", low, high)
            # return distance[0] << 8 | distance[1] # combine both bytes
            return low << 8 | high

        """
        Read the velocity of an object, if the receiver circuit is disabled, it will be
        enabled before taking a velocity measurement
        @:return int velocity in cm/s
            positive = away from lidar
            negative = towards lidar
        """

        def read_velocity(self):
            if not self.is_on:
                self.power_on()
            # Take two distance measurements to store in registers
            self.read_distance()
            self.read_distance()
            # Read the velocity register (8 bits, 2's complement)
            velocity = self.bus.read_byte_data(DEFAULT_ADDRESS, VELOCITY_OUTPUT)
            if velocity > 127:
                velocity = (256 - velocity)*(-1)
            return velocity

        """
        Read the current configuration of the device
        @:return list of ints, 7 bits
            bit 6: 0 = Enable reference process
                1 = Disable reference process
            bit 5: 0 = Use default delay for burst
                1 = Use custom delay from 0x45, HZ
            bit 4: 0 = Enable reference filter
                1 = Disable reference filter
            bit 3: 0 = Enable measurement quick termination
                1 = Disable measurement quick termination
            bit 2: 0 = Use default reference acquisition
                1 = Use custom  reference acquisition from 0x12
            bits 1-0: 00 = Default PWM mode
                    01 = Status output mode
                    10 = Fixed delay PWM mode
                    11 = Oscillator output mode (nominal 31.25kHz output)
            default config = 0x08 (0001000)
        """

        def read_device_config(self):
            config = int(self.bus.read_byte_data(DEFAULT_ADDRESS, ACQ_CONFIG_REG))
            config = bin(config)[2:].zfill(7)
            return [int(bit) for bit in str(config)]

        """
        Set the device config
        @:param list of ints, provide all 7 bits for config register
            bit 6: 0 = Enable reference process
                1 = Disable reference process
            bit 5: 0 = Use default delay for burst
                1 = Use custom delay from 0x45, HZ
            bit 4: 0 = Enable reference filter
                1 = Disable reference filter
            bit 3: 0 = Enable measurement quick termination
                1 = Disable measurement quick termination
            bit 2: 0 = Use default reference acquisition
                1 = Use custom  reference acquisition from 0x12
            bits 1-0: 00 = Default PWM mode
                    01 = Status output mode
                    10 = Fixed delay PWM mode
                    11 = Oscillator output mode (nominal 31.25kHz output)
            default config = 0x08 (0001000)
        """

        def write_device_config(self, bits):
            bits = [str(bit) for bit in bits]
            bits = int("".join(bits), 2)  # Convert to dec for i2c reg
            self.bus.write_byte_data(DEFAULT_ADDRESS, ACQ_CONFIG_REG, bits)

        """
        Read the current status of the device
        :return: list of ints
            bit 6: Process error flag
            bit 5: Health flag
            bit 4: Secondary return flag
            bit 3: Invalid signal flag
            bit 2: Signal overflow flag
            bit 1: Reference overflow flag
            bit 0: Busy flag
        """

        def read_device_status(self):
            # Read the STATUS register, bits 0-6 only
            status = int(self.bus.read_byte_data(DEFAULT_ADDRESS, 0x01))
            print("READING STATUS AND IT IS ", status)
            # Convert to binary, fill rest with 0's
            status = bin(status)[2:].zfill(7)
            return [int(bit) for bit in str(status)]

        """
        Check if the device is busy
        @:return boolean, true = busy
        """

        def device_busy(self):
            # STATUS register bit 0 represents busy flag, 0 for ready, 1 for busy
            return self.read_device_config()[-1]

        """
        Wait for the device to be ready
        """

        def _wait_for_ready_(self):
            while self.device_busy():
                # print(self.device_busy())
                pass

        """
        Set the maximum number of measurements the device can take before taking a reading
        note: the device will not always take this amount, only if required
            ex: surface is not very reflective, long distance
        The lower the number, the faster the measurement, values can range from 30 to 255
        @:param count max number of pulses (default 128)
        """

        def maximum_acquisition_count(self, count):
            if 30 < count < 255:
                raise Exception("Value must be between 30 and 255")
            self.bus.write_byte_data(DEFAULT_ADDRESS, SIG_COUNT_VAL, count)
            print(self.bus.read_byte_data(DEFAULT_ADDRESS, SIG_COUNT_VAL))

        """
        Turn the device receiver circuit on or off, This will save roughly 40mA
        Turning the receiver back on takes roughly the same amount of time as
        receiving a measurement
        @:param on boolean, represents the action
        """

        def power_on(self, on=True):
            if on:
                # Enable the receiver circuit
                self.is_on = True
                self.bus.write_byte_data(DEFAULT_ADDRESS, POWER_CONTROL, 0x80)
            else:
                # Disable the receiver circuit off
                self.is_on = False
                self.bus.write_byte_data(DEFAULT_ADDRESS, POWER_CONTROL, 0x81)


    def getDistance(num):
        if (num == 1):
            return(sensor1.read_distance(True)/100)
        if (num == 2):
            return(sensor2.read_distance(True)/100)

    roomCount = 0
    # Lidar system starts in idle state which is no movement in front of the sensors
    currentState = IDLE_STATE
    AWS_timer = int(time.time())

    sensor1 = Lidar()
    sensor2 = Lidar(SMBus(4))
    while(True):
        try:
            # Read and populate sensor distances twice. More accurate than sampling just once
            sensor1_distance = getDistance(1)
            sensor2_distance = getDistance(2)
            time.sleep(0.01)
            sensor1_distance = getDistance(1)
            sensor2_distance = getDistance(2)
            # print(str(sensor1_distance) + "      |      " + str(sensor2_distance))
            # If the system is in idle state, no one was previously walking through the tripwire
            
            if currentState == IDLE_STATE:
                # If the first sensor (closer to outside) dips below the threshold, the system is set to entry state
                if (sensor1_distance < 110 and sensor1_distance < sensor2_distance):
                    currentState = ENTRY_STATE
                    print(str(sensor1_distance) + "      |      " + str(sensor2_distance))
                # If the second sensor (closer to inside) dips below the threshold, the system is set to exit state
                if (sensor2_distance < 110 and sensor2_distance < sensor1_distance):
                    currentState = EXIT_STATE
                    print(str(sensor1_distance) + "      |      " + str(sensor2_distance))
            # If the system is in entry state, it means someone previously tripped the outside sensor and is entering the room
            elif currentState == ENTRY_STATE:
                print("Enter")
                roomCount += 1
                # The next state will be idle and we sleep for 0.75 seconds to account for most human walking speed through the door
                currentState = IDLE_STATE
                time.sleep(0.80)
            # If the system is in exit state, it means someone previously tripped the outside sensor and is entering the room
            elif currentState == EXIT_STATE:
                roomCount -= 1
                print("Exit")
                # The next state will be idle and we sleep for 0.75 seconds to account for most human walking speed through the door
                currentState = IDLE_STATE
                time.sleep(0.80)
            # Each sample of the lidar sensors has a sleep to maintain a 0.05s sample rate
            time.sleep(0.02)

            if int(time.time()) - AWS_timer > 180:
                # Publish message to server desired number of times.
                # This step is skipped if message is blank.
                # This step loops forever if count was set to 0.
                if args.message:
                    publish_count = 1
                    # message = "{} [{}]".format(args.message, publish_count)
                    temp = read_temp()
                    message = {'headcount': roomCount,
                                'temperature': temp
                                }
                    print("Publishing message to topic '{}': {}".format(args.topic, message))
                    message_json = json.dumps(message)
                    print(message_json)
                    mqtt_connection.publish(
                        topic=args.topic,
                        payload=message_json,
                        qos=mqtt.QoS.AT_LEAST_ONCE)
                    time.sleep(1)
                    publish_count += 1

                # Wait for all messages to be received.
                # This waits forever if count was set to 0.
                if args.count != 0 and not received_all_event.is_set():
                    print("Waiting for all messages to be received...")

                received_all_event.wait()
                print("{} message(s) received.".format(received_count))

                AWS_timer = int(time.time())
        except KeyboardInterrupt:
            print('\n\nI\'m gonna end it all')
            sys.exit()
        except Exception as e:
            # print('Lidar or thermistor sensor error')
            print(e)

    # Disconnect
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")
