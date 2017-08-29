#!/usr/bin/python3

import RPi.GPIO as gpio
import time
import datetime
import sys

# some notes about the setup
# whether I use pullup or pulldown, the power loss occurs through the reed switch
# so I need to use a high resister on the reed switch. 9k ohms, if possible, because I think the pullupdown resistors are 10k ohms

# SO, I shall use a pullup resistor, making GPIO the power source. Thus, the other pin must be ground.
# SO, when the switch closes the value will be LOW or Grounded

# GLOBALS -- change per desire!

PinGround = 6; #never used but to bear it in mind
PinGPIO = 7;
LogDir = "~/logs/"; # Include the trailing slash, this is where raw data is stored.

# END GLOBALS

class Datapoint:
    def __init__(self, totalRevs, revs, time):
        self.totalDist = totalRevs;
        self.instDist = revs;
        self.secondsElapsed = time;
        self.time = str(int(time/60)) + ":" + str(int(time%60)).zfill(2);
        self.aveSpeed = float(totalRevs)/time; #revs/sec
        self.instSpeed = float(revs)/10.0; # revs/sec
        self.unitSpeed = "revs/sec"; #default units
        self.unitDist = "revs"; #default


def main():
    argV = sys.argv
    argC = len(argV);
    if(argC == 1):
        # just the filename, run the picycle
        picycle();
        return;
    elif (argV[1] == "h") or (argV[1] == "help") or (argC > 3):
        print("Usage: either use no arguments to run the log or pass a log file to translate it");
    elif(argC == 2):
        translate(argV[1]);
    else:
        translate(argV[1], newFilepath=argV[2]);
    return;
    

def picycle():
    setupPins();
    print("pins setup"); #debug
    fullCount = 0; 
    startTime = time.time();
    lastTime = startTime;
    standstill = 10; # on standstill, this will be increased until 60, when recording stops
    gpio.wait_for_edge(PinGPIO, gpio.FALLING); #wait until movement to record
    while(standstill < 70):
        # fullcount is included so that the program doesn't terminate before ride starts
        count = 0;
        while(time.time() - lastTime < 10): # log about every 10 seconds
            tempTimeout = 10000-int((time.time() - lastTime)*1000);
            print("listening, timeout at " + str(tempTimeout)); #debug
            rev = gpio.wait_for_edge(PinGPIO, gpio.FALLING, timeout=tempTimeout, bouncetime=200); # waits until voltage falls from 3.3V to 0 V
            # timeout to make sure that things move in multiples of 10 seconds, bounce to avoid doublecounting
            if rev is not None:
                count += 1;
                print("rev counted"); # debug
            else:   #debug
                print("timeout"); #debug
        fullCount += count;
        lastTime = time.time();
        if(count == 0):
            standstill += 10;
        else:
            writeToLog(fullCount, count, lastTime-startTime);
            standstill = 10;
    writeToLog.file.close()
    return;

def writeToLog(totalRevs, revs, deltaTime):
    if "filepath" not in writeToLog.__dict__: # if this variable hasn't been initialized
        now = datetime.datetime.now(); # a note to python non-natives: these are hacks for a static variable
        writeToLog.filepath = LogDir + str(now.date()) + "_" + str(now.hour) + ":" + str(now.minute).zfill(2);
        writeToLog.file = open(writeToLog.filepath, "w");
    # a note for those new to coding: static variables are initialized once and then retain their value over multiple calls of the same function
    writeToLog.file.write(str(totalRevs) + "," + str(revs) + "," + str(deltaTime) + "\n");
    return;

def setupPins():
    gpio.setmode(gpio.BOARD);
    gpio.setup(PinGPIO, gpio.IN, pull_up_down=gpio.PUD_UP)
    return;

def translate(filepath, newFilepath=None): # this is incomplete, new functions and functionality will go here
    print("Translating to " + filepath);
    data = getList(filepath);
    if(newFilepath is None):
        for point in data:
            print(formatDatapoint(point));
    else:
        writeNewFile(newFilepath, data);
    return;

def getList(filepath):
    retlist = [];
    file = open(filepath, "r");
    for line in file:
        parse = line[:-1].split(",");
        retlist.append(Datapoint(int(parse[0]), int(parse[1]), float(parse[2])));
    file.close();
    return retlist;

def formatDatapoint(dp):
    format = str(dp.totalDist) + " " + dp.unitDist;
    format += "\t\t|\t" + "{:4.2}".format(dp.aveSpeed) + " " + dp.unitSpeed;
    format += "\t|\t" + str(dp.instDist) + " " + dp.unitDist;
    format += "\t\t|\t" + "{:4.2}".format(dp.instSpeed) + " " + dp.unitSpeed;
    format += "\t|\t" + dp.time;
    return format;

def writeNewFile(filepath, data):
    file = open(filepath, "w");
    file.write("Total Distance\t|\tAverage Speed\t| Instantaneous Distance| Instaneous Speed\t|\tTime\n");
    file.write("_"*105 + "\n");
    for point in data:
        file.write(formatDatapoint(point) + "\n");
    file.close();
    return;
main();

