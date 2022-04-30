# NoiseHub Engineering Addendum (See Wiki for further documentation)
## Intro
The problem NoiseHub aims to solve is one all college students experience: finding a suitable study space on campus can be challenging and consume precious time, better spent studying. NoiseHub intends to improve efficiency in students' search for study spaces by providing accurate and real-time information on study spaces across campus. This information includes room temperature, noise levels, and an estimate of current occupancy.

As a final deliverable, the NoiseHub team will present a fully functioning sensor suite and companion app which is tailored to each individual user. Users will be able to specify room aspects they find important, and the suggested study spaces will be filtered based on the users preferences.

<!-- NEW SECTION -->
## Areas of the Project

<!-- NEW SECTION -->
## Current State
The system is currently able to source headcount, noise, and temperature data continuously, uploading the data to AWS for permanent temporal storage. The mobile application is able to source data from AWS, trigger a Lambda function to run data analysis on the last 24 hours of data on demand, graph the past 24 hours of data, and offer a user feedback capability in the case of under or overreporting room occupancy. 

<!-- NEW SECTION -->
## Gotchas
These are some of the major roadblocks we ran into while working on the project. This section aims to inform future developers on how to avoid them, diagnose them, and fix them.

# Hardware
The Lidars were the most problematic piece of hardware in this project. Firstly, the standard Lidar without a breakout board has extremely small and tightly grouped pin holes. Whoever solders wires to the Lidar should have at least some experience soldering. Furthermore, ensure you’re using a good soldering kit. When soldering our first Lidar, the soldering pen wouldn’t heat properly, causing messy connections that leaked to each other and caused a short, killing our first Lidar. After soldering, ensure the flux is contained to each pin and there are no cross connections before connecting to power. You can tell if the Lidar is working properly if you see a faint red light blinking in one of the lenses. 

The microphone is another point of improvement. It was important to find a plug-and-play, small form-factor microphone that did not require any drivers in order to maximize compatibility and make it easy to work with. However, the microphone we chose from Adafruit is extremely low fidelity and made it very difficult to accurately model room noise. Although it may be difficult to find a high fidelity, small form-factor microphone that does not require drivers, it would be very worthwhile to do so. 

The model of thermistor we used doesn’t have actual pins, only loose wires. To work around this, you can either solder the wires to pins or twist them and fit them into the breadboard. If fitting them into the breadboard make sure you insert the wires all the way. It’s easy to accidentally bend them and only get them halfway in, the circuit won’t work. 

# Software
The noise_client.py script is very computationally intensive, sampling both audio and thermistor data at a relatively fast rate. Due to using Raspberry Pis and writing code in Python, a lot of these computations are slower and more computationally expensive than if they were compiled and run on a microcontroller. Given our timeline and experience, it was also vastly easier to develop using Python on a system we were all very familiar with. However, higher sample rates would cause some issues such as dropped MQTT payloads, dropped samples, and I/O errors. Choosing another microcontroller or optimizing the code by adjusting sample rates and mathematical operations could solve this issue. 

The software for the Lidars can be tricky. The default library provided for them reads from the wrong registers. Make sure you’re reading the low bytes from register 0x10, and the high bytes from 0x11. Also, the sensor just fails sometimes. It’s a known issue with them and there’s not much you can do about it. Because we’re constantly sampling, we can mitigate this by wrapping it in a try statement, catching the exception and just moving on. 

# Mobile App
Developing the mobile application was a gradual process that involved many code refactors as new methods were found and architecture changes were made. The current state of the application is stable and much of the code has been refactored to follow best practices. 

One practice we found to be highly beneficial towards a better development experience was turning as much code as possible into reusable components. It makes it far easier to trace issues and optimize the code for better performance when you can isolate components and make changes centrally without having to scour multiple files. A major issue that we kept running into during development was a cell stack error due to too many function calls and state refreshes. The file in question was making several API calls with many state variables, overall a difficult file to debug. After refactoring the code to import most of the backend logic as functions, it was far easier to trace and understand why so many function calls were being made and optimize the code.

# AWS Resources
When creating and maintaining the AWS resources in this project, it is critical to document the processes closely and make sure to follow best practices at all times to prevent issues, especially when it comes to security. Be diligent in practicing the principle of least privilege and make sure to create budget alarms to avoid unwanted charges.
In certain parts of the project, it is necessary to harcode credentials, and it is important to make sure to not accidentally publish them on Github. In the event this happens, following the principle of least privilege will be critical to preventing any potential damage. Placing credentials in a separate file and importing them will also make it far easier to rotate them when needed. 

Credentials within the mobile application are one of the more significant security risks in the project. Initially we were using IAM roles in order to provide the SDK with the necessary credentials, but we learned that when a user registers and signs into the application, the local Cognito session has credentials to which we can assign additional permissions and pass to the SDK calls. In the future, this can be used to prevent users with different levels of access from performing certain operations. 


<!-- NEW SECTION →
##Safety Warnings

Improper cable management of the Lidar sensor suite can create a tripping hazard. This could lead to injury of users, with the client at liability for improper maintenance. 

Improperly mounted sensor suites are at risk of falling onto users. This could lead to injury of users. 

Improper management of administrative credentials can pose a security threat. Exposed credentials can lead to a breach of the clients control over their NoiseHub system, and, in cases of poor online security practice, could lead to a breach of the client's network.

This product's backend is susceptible to any threats AWS services are susceptible to. A breach of the backend can lead to compromised personal user information.

Users are recommended to not use open containers of liquids near the sensor suites. Spilling of liquid on the sensor suites can cause damage to the sensors and Pi.

This product should be mounted only in controlled environments. Areas like gymnasiums with unpredictable moving objects can hit the sensor suite, causing wires to come loose, damage sensors, damage the Pi, or break the casing.


