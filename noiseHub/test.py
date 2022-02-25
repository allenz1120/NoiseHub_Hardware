import lidarTest 
import threading
import time
#print("here")
t = threading.Thread(target=lidarTest.getHeadcount)
t.start()

for i in range(100):
    print("HELLO")
    print(lidarTest.roomCount)
    time.sleep(1)
