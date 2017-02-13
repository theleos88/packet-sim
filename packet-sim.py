import simpy
import numpy
import math
import random
import time
import signal
import os

from collections import deque # double-ended queue

# Global variables
CAPACITY = 256
ARRIVAL_RATE = 1000000 # 1 Mpps, a packet every us.
SERVICE_TIME = 1./1000000 # 1 MHz
SIZE = 0
COUNT = 0
data = {}
busy = False

# Math functions
def exp_distr(rate):
    return -math.log(1.0 - random.random()) / rate

def const_distr(rate):
    return float(1.0/rate)

# Control
def signal_handler(signum, stack):
    print data

# Queue model
buffer= deque()

def packet_events(env, data):
    global buffer

    while True:
        t = exp_distr(data["ARRIVAL_RATE"])
        yield env.timeout(t)
        data["COUNT"]+=1

        if len(buffer)>=data["CAPACITY"]:
            data["DROP"]+=1
            #print "Drop", data["DROP"], env.now
        else:
            data["SIZE"]+=1
            buffer.append( (data["COUNT"], env.now)  )

            #print "Received", data["COUNT"], env.now
            notify_server(env, data)

def packet_burst(env, data, size):
    global buffer

    while True:
        t = exp_distr(data["ARRIVAL_RATE"])
        yield env.timeout(t)

        for i in range(1,size):
            if len(buffer)>=data["CAPACITY"]:
                data["DROP"]+=1
                #print "Drop", data["DROP"], env.now
                #break
            else:
                data["COUNT"]+=1
                data["SIZE"]+=1
                buffer.append( (data["COUNT"], env.now)  )

            print "Received Burst", data["COUNT"], env.now
        notify_server(env, data)


        #Leos second version: No need for this
        #env.process(queue_process(env, data, queue))


def packet_departures(env, data):

    global busy, buffer

    busy = True
    while len(buffer)!=0:
        t = const_distr(1.0/data["SERVICE_TIME"])
        yield env.timeout(t)

        data["PROCESSED"]+=1
        (a,b) = buffer.popleft()
        data["SIZE"]-=1

        #print "Sent",a,env.now
    busy = False


def notify_server(env, data):
    global busy

    if not busy:
        env.process(packet_departures(env, data))
    return


# print "Callback", runs, DATA

random.seed(1)
signal.signal(signal.SIGUSR1, signal_handler)
print os.getpid()

env = simpy.Environment()
#req = simpy.Resource(env, capacity=1)
data["CAPACITY"]=CAPACITY
data["ARRIVAL_RATE"] = ARRIVAL_RATE
data["SERVICE_TIME"] = SERVICE_TIME
data["SIZE"]=SIZE
data["COUNT"]=COUNT
data["DROP"]=0
data["PROCESSED"]=0

env.process(packet_events(env, data))
#env.process(packet_burst(env, data, 8))

#env.run(until=10)
print data
for i in range(1,300):
    #print("Starting simulation.",i, env.now)
    env.run(until=i*0.1)
    #print("End of simulation.", env.now)
    print data
    #print i, data["COUNT"], data["PROCESSED"], data["DROP"], data["SIZE"]
