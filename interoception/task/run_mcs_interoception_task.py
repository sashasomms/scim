#!/usr/bin/python
# Sasha Sommerfeldt 2019

from psychopy import core, visual, prefs, event, data, parallel
import random
import sys
import serial
import time
import os
import copy
from useful_functions import *
import logging


# The following line is for serial over GPIO
## Set the correct port for your machine's usb plug -- In arduino see Tools -> Port for arduino port
# Serial port to talk to arduino
port = 'COM4' # Psychophys stimulus computer
logging.warning("Port is " + port)

# Parallel port to talk to Biopac amplifiers
# (found through Windows Control Panel-> Device Manager -> Ports (COM & LPT) -> Parallel Port -> Resources tab -> copy lowest number )
myParallelPort = 0xDFF8 # Psychophys room stimulus PC
print("Setting parallel port to " + hex(myParallelPort))
parallel.setPortAddress(myParallelPort)
print("Setting parallel port pins to all 0")
parallel.setData(0)

def setBiopacDIN(*args):
    NumArgs = len(args)
    print(NumArgs)
    if NumArgs == 1:
        print( "Setting parallel data to " + str(args[0]))
        parallel.setData(2**(args[0]))
    if NumArgs == 2:
        print( "Setting parallel data to " + str(args[0]) + str(args[1]) )
        parallel.setData(2**(args[0]) | 2**(args[1]))
    if NumArgs == 3:
        print( "Setting parallel data to " + str(args[0]) + str(args[1]) + str(args[2]) )
        parallel.setData(2**(args[0]) | 2**(args[1]) | 2**(args[2]))

def setParallelPortPins(*args):
    pins = 0
    for arg in args:
        print("Setting parallel port pin " + str(arg) + " high")
        pins = pins |  (2**arg)
    print("Setting those pins.")
    parallel.setData(pins)

    # parallel.setData does all the work:
    # Pin 1 corresponds to binary 0's-place, which is to say on is 1, off is 0.
    # Pin 2 corresponds to binary 1's place, on is 2, off is 0. And so on.
    # So, to convert the pin number to a value that parallel.setData can use, subtract 1 from
    # the pin number to get the 0's or 1's or 2's or whatver's place, then raise 2 to that power.
    # So, 1's place = 2**1, or 2. And 7's (top pin)'s place is 2**7 or 128.
    # For example, to get 42, in binary is 32 (or 2^5) + 8 (or 2^3) + 2 (or 2^1).
    # This gives you any number between 0 (all pins 1 through 7 low) and 255 (all pins high).

def clearBiopacDINs():
    parallel.setData(0)


ard = serial.Serial(port,9600,timeout=0)
time.sleep(2) # wait for Arduino


### Variables that should stay the same for the duration of the study
expName = 'MCSinteroception'
# How long you want the light to stay on/flash for. 2 characters/digits allowed
msStimulus = 10
# What to multiply the ecgAVG by to set the RWaveThreshold. 3 characters allowed
thresholdMultiplier = 2.5
# Number of heart beats per trial (typically 5). 2 characters/digits allowed
beatsPerTrial = 5
# Number of samples to use to calculate the average signal. 4 characters/digits allowed
ecgAVGLength = 500

# How long to wait for a participant response
responseWaitTime = 5.0
confidenceResponseWaitTime = 5.0


# Mapping of keyboard keys to what they represent in the experiment (data coding)
responseKeyDict = {'num_2':'sim', 'num_3':'not'}
confidenceResponseKeyDict = {'num_7':'1', 'num_8':'2', 'num_9':'3', 'num_subtract':'4'}


#### TEXT DISPLAYED TO PARTICIPANT ####
calibrationText = 'Before we get started, we need to calibrate the experiment. This may take several minutes. \
\n\nPlease try to remain still and keep your legs and ankles uncrossed.'

practiceAgainText = "Would you like to practice again?"

confidenceText = 'How confident are you?'

responseKeyText = '+ = Yes    |    - = No'

confidenceKeyText = '1 = Not at all confident    |    4 = Completely confident'


## Light-Tone Instructions
LTinstrText1 = 'For the first part of this task, you will see the green light flash on the box and hear tones. \
\n\nOn each trial, there will be a series of 5 light flashes paired with 5 tones. \
\n\nFor some trials, the tones and lights will occur at the same time, and on other trials, the lights and tones will occur at slightly different times.'

LTinstrText1b = 'Within a trial, whether the lights and tones occur at the same time or at different times will always be the same. The sequence of 5 lights and tones on each trial is to give you enough time to make your judgment.'

LTinstrText1c = 'It is important to note that across all trials, the lights and tones will always occur at the same pace or rhythm. The difference is that, for some trials, either the lights or the tones are slightly delayed.\
\n\nYour task is to determine whether the lights and tones occur AT THE SAME TIME.'

LTinstrText2 = 'After each series of 5 light-tone pairs, a second screen will ask whether the lights and tones occurred at the same time. \
\n\nYou should wait until this second screen appears before making your response. If you respond before the screen appears, your answer will not be recorded.'

LTinstrText3 = "On the response screen, \
\n\nThe '+' key will always represent 'Yes, at the same time.' \
\n\nThe '-' key will always represent 'No, not at the same time.' \
\n\nThe following text will always display at the bottom of the response screen as a reminder:"

LTinstrText4 = "After you make your response, another screen will ask how confident you are that your response was accurate. \
\n\nFor example, if you responded 'No', then you should rate how confident you are that your answer of 'No' is correct."

LTinstrText5 = "To rate your confidence in your answer, you will use the 1, 2, 3, and 4 keys. \
\n\nHere, 1 represents 'Not at all confident,' and 4 represents 'Completely confident.'"

LTinstrText6 = "Let's first test the response keypad. \
\n\nPlease press 3 on the keypad."

LTinstrText7 = 'Good! \
\n\nPlease try to remain still, with your legs and ankles uncrossed, throughout the entire task. \
\n\nPlease also remember to wait until each response screen appears before pressing a button to respond. \
\n\nFirst, you will have 6 trials to practice before moving on to the actual task. \
\n\nDo you have any questions before we begin?'

LTfocusText = 'Please focus on the green light on the box.'

LTstartText = 'You will now start the actual trials. They will be the same as the practice trials you just completed. \
\n\nThere will be 1 block/set of trials for this section. It is important to respond on every trial. \
\n\nDo you have any questions before we begin?'

LTresponseText = 'Did the lights and tones occur at the same time?'





## Heartbeat-Tone Instructions
HTinstrText1 = 'Good job! \
\n\nFor the next section, instead of the light, your task is to determine whether the tones occur at the same time as your heartbeats. \
Sometimes the tones will occur at the same time as when you feel your heartbeats, and sometimes they will not. \
\n\nSimilar to the first part of this task, your heartbeats and the tones will always occur at the same pace or rhythm, but will not always occur at the same time. \
\n\nYour task is to determine whether your heartbeats and the tones occur AT THE SAME TIME.'

HTinstrText2 = 'You should keep your hands on the table and keypad, sensing your heart without taking your pulse. \
\n\nYou may sense your heartbeats in different locations in your body. \
Across the task, it is important to be consistent in where in your body you sense your heartbeats, so try to tune in to the same spot each time.'

HTinstrText2b = "You may not be able to sense your heartbeats at all. That's okay. Just try your best."

HTinstrText3 = 'Please take 20 seconds now to tune into your heartbeats.'

HTinstrText4 = 'OK. Just like before, on each trial you will hear 5 tones. This time, the tones will correspond to 5 heartbeats. \
\n\nThen, a screen will ask whether the tones occurred at the same time as your heartbeats. \
\n\nThen, another screen will ask how confident you are in your response.'

HTinstrText5 = 'Please remember to remain still with your legs and ankles uncrossed throughout the entire task. \
\n\nPlease also remember to wait until each response screen appears before pressing a button to respond. \
\n\nFirst, you will have 6 trials to practice before moving on to the actual task. \
\n\nDo you have any questions before we begin?'

HTfocusText = 'Please focus on your heartbeats. '

HTstartText = 'You will now start the actual trials for this section. They will be the same as the practice trials you just completed. \
\n\nThere will be 3 blocks/sets of trials for this section. It is important to respond on every trial.\
\n\nDo you have any questions before we begin?'

HTresponseText = 'Did your heartbeats and the tones occur at the same time?'




#### ARDUINO FUNCTIONS ####

def readOneArdLine(ard):
    while (ard.inWaiting() < 1):
        time.sleep(0.1)
    time.sleep(0.1)
    r = ard.readline()
    return r


def readSomeArdLines(ard):
    ArduinoMessage = readOneArdLine(ard)
    while '##' not in ArduinoMessage :
        ArduinoMessage = readOneArdLine(ard) # read all characters in buffer
        logging.warning('Waiting for ##: ' + ArduinoMessage)
        time.sleep(0.1)
    logging.warning('A:::::::::::::: %s ::::::::::::::A' % ArduinoMessage)
    return ArduinoMessage


def resetArduino():
    # Handshake with Arduino. Loop on this until it works.
    #ArduinoMessage = ''
    while True:
        ## For the arduino
        command = 'R'
        strCommand = str(command)
        ard.flush() # flush the outgoing message buffer
        logging.warning("P: Command sent = %s" % strCommand)
        ard.write('>CM ' + strCommand + '\n')
        ard.flush()
        time.sleep(10)
        ArduinoMessage = readSomeArdLines(ard) # read all characters in buffer
        logging.warning(ArduinoMessage)
        if ('#ArduinoReady' in ArduinoMessage) :
            logging.warning("Arduino is reset and ready.")
            return

def initializeArduino(msStimulus, thresholdMultiplier, beatsPerTrial):
    strMsStimulus = str(msStimulus)
    logging.warning("P: Stimulus delay sent = %s" % strMsStimulus)
    ard.write('>ST ' + strMsStimulus + '\n')
    ard.flush()
    time.sleep(1)
    readSomeArdLines(ard)

    strThresholdMultiplier = str(thresholdMultiplier)
    logging.warning("P: Threshold multiplier sent = %s" % strThresholdMultiplier)
    ard.write('>TM ' + strThresholdMultiplier + '\n')
    ard.flush()
    time.sleep(1)
    readSomeArdLines(ard)

    ard.flush()
    strBeatsPerTrial = str(beatsPerTrial)
    logging.warning("P: Beats per trial sent = %s" % strBeatsPerTrial)
    ard.write('>BP ' + strBeatsPerTrial + '\n')
    ard.flush()
    time.sleep(1)
    readSomeArdLines(ard)

    # 'I' tells the arduino to initialize with the following variables
    command = 'I'
    strCommand = str(command)
    ard.flush() # flush the outgoing message buffer
    logging.warning("P: Command sent = %s" % strCommand)
    ard.write('>CM ' + strCommand + '\n')
    ard.flush()
    time.sleep(2)
    ArduinoMessage = readSomeArdLines(ard)

    if ('ERROR' in ArduinoMessage) :
        exit()


# Run calibration to find the average of ecgAVGLength number of ECG samples
def calibrateArduino(ecgAVGLength):
    strEcgAVGLength = str(ecgAVGLength)
    logging.warning("P: Length/Number of samples for ecg AVG sent = %s" % strEcgAVGLength)
    ard.write('>AL ' + strEcgAVGLength + '\n')
    ard.flush()
    time.sleep(1)
    readSomeArdLines(ard)
    # 'C' tells the arduino to calibrate
    command = 'C'
    strCommand = str(command)
    ard.flush() # flush the outgoing message buffer
    logging.warning("P: Command sent = %s" % strCommand)
    ard.write('>CM ' + strCommand + '\n')
    ard.flush()
    # Wait
    time.sleep(1)
    ArduinoMessage = readSomeArdLines(ard)
    while not '#CDone' in ArduinoMessage:
        logging.warning('Not yet finished A:' + ArduinoMessage)
        if ('ERROR' in ArduinoMessage) :
            calibrationResults = "Error in calibration. Please try again."
            logging.warning(calibrationResults)
            exit()
        time.sleep(0.1)
        ArduinoMessage = readSomeArdLines(ard)
    calibrationResults = "Calibration completed."
    return calibrationResults




#### PARTICIPANT INTERFACE FUNCTIONS ####

def initExperiment(expName, msStimulus, thresholdMultiplier, beatsPerTrial, ecgAVGLength):
    while True:
        runTimeVarOrder = ['subjID','trialSet','timepoint']
        ### runTimeVars gives us three variables:
        # 1. a dictionary giving study information,
        # 2. a list giving an order of the runTimeVariables,
        # 3. an experiment name
        runTimeVars = getRunTimeVars({'subjID':'', 'trialSet':['Choose', 'A','B'], 'timepoint':['Choose', 't1','t2']}, runTimeVarOrder, expName)
        subjID = runTimeVars['subjID']
        outputFilePath = 'data/%s_%s_%s.csv' % (runTimeVars['subjID'],runTimeVars['timepoint'], runTimeVars['expName'])
        lightToneOutputFilePath = 'data/%s_%s_%s_lightTone.csv' % (runTimeVars['subjID'],runTimeVars['timepoint'], runTimeVars['expName'])
        practiceOutputFilePath = 'data/%s_%s_%s_practice.csv' % (runTimeVars['subjID'],runTimeVars['timepoint'], runTimeVars['expName'])
        logFilePath = 'data/%s_%s_%s.log' % (runTimeVars['subjID'],runTimeVars['timepoint'], runTimeVars['expName'])
        print("logfile is stored at: %s" % logFilePath)
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logging.basicConfig(filename=logFilePath,level=logging.DEBUG, filemode='w')
        if runTimeVars['subjID'] == '':
            popupError('Participant ID is blank')
        elif 'Choose' in runTimeVars.values():
            popupError('Need to choose a value from a dropdown box')
        elif os.path.isfile(outputFilePath) :
            popupError('ERROR: File already exists. Double-check ID and timepoint.')
        else:
            try:
                outputFile = openOutputFile(outputFilePath)
                lightToneOutputFile = openOutputFile(lightToneOutputFilePath)
                practiceOutputFile = openOutputFile(practiceOutputFilePath)
                logging.warning(outputFilePath)
                if outputFile: #files were able to be opened
                    break
                logging.warning(lightToneOutputFilePath)
                if lightToneOutputFile: #files were able to be opened
                    break
            except:
                popupError('Output file(s) could not be opened')

    resetArduino()
    initializeArduino(msStimulus, thresholdMultiplier, beatsPerTrial)
    logging.warning("Finished initializing")
    # Header and trial info
    (header,trialInfo) = importTrialsWithHeader('trials/'+runTimeVars['trialSet']+'_trials.csv')
    (lightToneHeader,lightToneTrialInfo) = importTrialsWithHeader('trials/lightTone'+runTimeVars['trialSet']+'_trials.csv')
    (practiceHeader,practiceTrialInfo) = importTrialsWithHeader('trials/practice'+runTimeVars['trialSet']+'_trials.csv')
    ## add some more info to headers and trial info
    for eachTrialLine in trialInfo :
        eachTrialLine['subjID'] = subjID
        eachTrialLine['msStimulus'] = msStimulus
        eachTrialLine['thresholdMultiplier'] = thresholdMultiplier
        eachTrialLine['beatsPerTrial'] = beatsPerTrial
        eachTrialLine['ecgAVGLength'] = ecgAVGLength
    for eachTrialLine in lightToneTrialInfo :
        eachTrialLine['subjID'] = subjID
        eachTrialLine['msStimulus'] = msStimulus
        eachTrialLine['thresholdMultiplier'] = thresholdMultiplier
        eachTrialLine['beatsPerTrial'] = beatsPerTrial
        eachTrialLine['ecgAVGLength'] = ecgAVGLength
    for eachTrialLine in practiceTrialInfo :
        eachTrialLine['subjID'] = subjID
        eachTrialLine['msStimulus'] = msStimulus
        eachTrialLine['thresholdMultiplier'] = thresholdMultiplier
        eachTrialLine['beatsPerTrial'] = beatsPerTrial
        eachTrialLine['ecgAVGLength'] = ecgAVGLength
    expandHeader = ['msStimulus', 'thresholdMultiplier', 'beatsPerTrial', 'ecgAVGLength']
    datafileHeader = ['subjID'] + header + expandHeader
    lightToneDatafileHeader = ['subjID'] + header + expandHeader
    practiceDatafileHeader = ['subjID'] + header + expandHeader
    # Add variable names to the top of each file
    writeToFile(lightToneOutputFile,lightToneDatafileHeader+['RT','response','confidenceRT','confidence'],writeNewLine=True)
    writeToFile(outputFile,datafileHeader+['RT','response','confidenceRT','confidence'],writeNewLine=True)
    writeToFile(practiceOutputFile,practiceDatafileHeader+['RT','response','confidenceRT','confidence'],writeNewLine=True)
    return (practiceDatafileHeader, practiceTrialInfo, practiceOutputFile, lightToneDatafileHeader, lightToneTrialInfo, lightToneOutputFile, datafileHeader, trialInfo, outputFile)



def showTrial(curTrial, header, outputFile, lightToneYN, win, responseScreen, responseKeys, confidenceStim, confidenceKeys, askText):
    logging.warning(curTrial)
    if lightToneYN == 'Y':
        # Tell arduino to turn on a light with R-spike
        logging.warning("lightTone")
        command = 'P'
        fixationStim = visual.TextStim(win=win,text='V', color='white', height=60, pos=(0, 50))
    elif lightToneYN == 'N':
        logging.warning("trial")
        command = 'T'
        fixationStim = visual.TextStim(win=win,text='+', color='white', height=60, pos=(0, 50))
    # Reset variables
    response = ''
    RT = ''
    confidenceRT = ''
    confidence = ''
    msDelay = curTrial['trialDelay']
    ## Just show a fixation cross and the arduino does the job of setting off the set of tone stimuli for the trial
    fixationStim.draw()
    win.flip()

    # Send arduino the delay for this trial
    strMsDelay = str(msDelay)
    logging.warning("P: Delay sent: %s" % strMsDelay)
    ard.write('>DL ' + strMsDelay + '\n')
    ard.flush()
    # Wait
    time.sleep(2)
    # Look for a response from Arduino
    readSomeArdLines(ard)

    # Tell the arduino to run a trial
    timerClock = core.Clock() # timer for troubleshooting
    strCommand = str(command)
    ard.flush() # flush the outgoing message buffer
    logging.warning("P: Command sent = %s" % strCommand)
    ard.write('>CM ' + strCommand + '\n')
    ard.flush()
    # Send different DIN to python to mark trial depending on delay type.
    # This will stay on until the end of the trial.
    if strMsDelay == '0' :
        setBiopacDIN(0)
    if strMsDelay == '100' :
        setBiopacDIN(1)
    if strMsDelay == '200' :
        setBiopacDIN(2)
    if strMsDelay == '300' :
        setBiopacDIN(3)
    if strMsDelay == '400' :
        setBiopacDIN(4)
    if strMsDelay == '500' :
        setBiopacDIN(5)
    # Wait
    time.sleep(1)
    readSomeArdLines(ard)
    timePostCommand = timerClock.getTime()
    logging.warning("After sending command and Arduino's message response to command at %s" % timePostCommand)
    # Look for Arduino to say #TDone (trial done)
    responseKey = ''
    ArduinoMessage = readOneArdLine(ard)
    logging.warning("Before #TDone loop %s" % ArduinoMessage)
    while '#TDone' not in ArduinoMessage :
        ArduinoMessage = readOneArdLine(ard)
        logging.warning("Inside waiting for #TDone %s" % ArduinoMessage)
        #time.sleep(.1)
    timeBefore = timerClock.getTime()
    clearBiopacDINs() # Clear all biopac DINs to mark trial is off
    logging.warning("Passed #TDone while at %s" % timeBefore)
    time.sleep(2)
    # Ask for a response
    RTtimer = core.Clock()
    responseKeys.draw()
    responseScreen.draw()
    win.flip()
    RTtimer.reset()
    timeAfter = timerClock.getTime() #for troubleshooting
    logging.warning("Flipped the screen at %s" % timeAfter) # for troubleshooting
    # Measure reaction time (RT)
    responseKey = event.waitKeys(keyList=responseKeyDict.keys(), maxWait=responseWaitTime, timeStamped=RTtimer)
    if responseKey :
        print(responseKey[0][0])
        RT = responseKey[0][1] * 1000.00
        response = responseKeyDict[ responseKey[0][0] ][0]
        logging.warning("response RT = %s" % RT)
        logging.warning("response = %s" % response)
    else:
        RT = 'NA'
        response = 'NA'
        logging.warning("Failed response. Response RT = %s" % RT)
        logging.warning("Failed response. Response = %s" % response)
    win.flip()
    ## Confidence rating
    confidenceResponseKey = ''
    confidenceStim.draw()
    confidenceKeys.draw()
    win.flip()
    # Measure reaction time (RT) for confidence rating
    RTtimer.reset()
    confidenceResponseKey = event.waitKeys(keyList=confidenceResponseKeyDict.keys(), maxWait=confidenceResponseWaitTime, timeStamped=RTtimer)
    if confidenceResponseKey :
        print(confidenceResponseKey[0][0])
        confidenceRT = confidenceResponseKey[0][1] * 1000.00
        confidenceResponse = confidenceResponseKeyDict[ confidenceResponseKey[0][0] ][0]
        logging.warning("confidence response RT = %s" % confidenceRT)
        logging.warning("confidence response = %s" % confidenceResponse)
    else :
        confidenceRT = 'NA'
        confidenceResponse = 'NA'
        logging.warning("Failed response. Confidence response RT = %s" % confidenceRT)
        logging.warning("Failed response. Confidence response = %s" % confidenceResponse)
    win.flip()
    ## Record the data for this trial to file
    curTrial['datafileHeader'] = datafileHeader
    ## Write data to output file
    trialData = [curTrial[_] for _ in curTrial['datafileHeader']] # add independent and runtime variables to what's written to the output file
    # Dependent variables
    trialData.extend((RT,response,confidenceRT, confidenceResponse))
    writeToFile(outputFile,trialData,writeNewLine=True)

def sayFocus(focusText):
	focus = visual.TextStim(win=win,text=focusText, color="white", height=45, wrapWidth=900, alignHoriz='center', pos=(0, 150))
	focus.draw()
	win.flip()
	time.sleep(5)

if __name__ == '__main__':
    ## Initialize the experiment (includes resetting arduino and intitializing arduino)
    ## (Get runtime variables, trial lists, etc.)
    (practiceDatafileHeader, practiceTrialInfo, practiceOutputFile, lightToneDatafileHeader, lightToneTrialInfo, lightToneOutputFile, datafileHeader, trialInfo, outputFile) = initExperiment(expName, msStimulus, thresholdMultiplier, beatsPerTrial, ecgAVGLength)

    #### Calibration ####
    win = visual.Window(fullscr=True,allowGUI=False, color="black", units='pix')
    calibrationScreen = visual.TextStim(win=win,text=calibrationText, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 150))
    calibrationScreen.draw()
    win.flip()
    calibrationResults = calibrateArduino(ecgAVGLength)
    calibrationResultsScreen = visual.TextStim(win=win,text=calibrationResults, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 150))
    calibrationResultsScreen.draw()
    win.flip()
    event.waitKeys(keyList=['space'])

    ## General/repeated use text stim
    responseKeys = visual.TextStim(win=win,text=responseKeyText, color='white', height=30, wrapWidth=1000, pos=(0, -200))
    confidenceStim = visual.TextStim(win=win,text=confidenceText, color='white', height=50, wrapWidth=1100, pos=(0, 150))
    confidenceKeys = visual.TextStim(win=win,text=confidenceKeyText, color="white", height=30, wrapWidth=1000, pos=(0, -200))
    practiceAgain = visual.TextStim(win=win,text=practiceAgainText, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 150))



    #### LIGHT-TONE ####
    # Is it a lightTone block? Y or N
    lightToneYN = 'Y'
    askText = LTresponseText
    focusText = LTfocusText
    responseScreen = visual.TextStim(win=win,text=askText, color="white", height=50, wrapWidth=1100, pos=(0, 150))

    ## Instructions
    LTinstructions1 = visual.TextStim(win=win,text=LTinstrText1, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 50))
    LTinstructions1.draw()
    win.flip()
    event.waitKeys(keyList=['space'])
    #
    LTinstructions1b = visual.TextStim(win=win,text=LTinstrText1b, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 150))
    LTinstructions1b.draw()
    win.flip()
    event.waitKeys(keyList=['space'])
    #
    LTinstructions1c = visual.TextStim(win=win,text=LTinstrText1c, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 150))
    LTinstructions1c.draw()
    win.flip()
    event.waitKeys(keyList=['space'])
    #
    LTinstructions2 = visual.TextStim(win=win,text=LTinstrText2, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 150))
    LTinstructions2.draw()
    win.flip()
    event.waitKeys(keyList=['space'])
    #
    LTinstructions3 = visual.TextStim(win=win,text=LTinstrText3, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 150))
    LTinstructions3.draw()
    responseKeys.draw()
    win.flip()
    event.waitKeys(keyList=['space'])
    #
    LTinstructions4 = visual.TextStim(win=win,text=LTinstrText4, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 150))
    LTinstructions4.draw()
    win.flip()
    event.waitKeys(keyList=['space'])
    #
    LTinstructions5 = visual.TextStim(win=win,text=LTinstrText5, color="white", height=45, wrapWidth=1100, pos=(0, 150))
    LTinstructions5.draw()
    confidenceKeys.draw()
    win.flip()
    event.waitKeys(keyList=['space'])
    #
    LTinstructions6 = visual.TextStim(win=win,text=LTinstrText6, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 150))
    LTinstructions6.draw()
    win.flip()
    event.waitKeys(keyList=['num_9'])
    #
    LTinstructions7 = visual.TextStim(win=win,text=LTinstrText7, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 150))
    LTinstructions7.draw()
    win.flip()
    event.waitKeys(keyList=['space'])
    #

    ## Practice trials
    sayFocus(focusText)
    for i,curPracticeTrial in enumerate(practiceTrialInfo):
        showTrial(curPracticeTrial, practiceDatafileHeader, practiceOutputFile, lightToneYN, win, responseScreen, responseKeys, confidenceStim, confidenceKeys, askText)
    # Ask if they want to practice again
    practiceAgain.draw()
    win.flip()
    # Allow 'y' or 'n' key responses (idea is that experimenter should press these after asking participant)
    practiceAgainYN = event.waitKeys(keyList=['y','n'])
    # If yes
    if practiceAgainYN[0][0] == 'y' :
        # Run practice trials again
        sayFocus(focusText)
        for i,curPracticeTrial in enumerate(practiceTrialInfo):
            showTrial(curPracticeTrial, practiceDatafileHeader, practiceOutputFile, lightToneYN, win, responseScreen, responseKeys, confidenceStim, confidenceKeys, askText)
    ## Actual trials
    LTstart = visual.TextStim(win=win,text=LTstartText, color="white", height=45, wrapWidth=900, alignHoriz='center', pos=(0, 150))
    LTstart.draw()
    win.flip()
    event.waitKeys(keyList=['space'])

    # Tell biopac to turn a DIN on to mark the start of the block
    setBiopacDIN(6)
    clearBiopacDINs()
    # Begin lightTone blocks
    sayFocus(focusText)
    for i,curLightToneTrial in enumerate(lightToneTrialInfo):
        logging.warning("curtrial Block = %s" % curLightToneTrial['block'])
        if i != 1 :
            lastTrial = i - 1
        else:
            lastTrial = i
        logging.warning("Last trial Block = %s" % lightToneTrialInfo[lastTrial]['block'])
        # Find when the block switched
        blockDifference = int(curLightToneTrial['block']) - int(lightToneTrialInfo[lastTrial]['block'])
        # If it is a new block, show break screen rather than next trial
        if blockDifference == 1 :
            LTblockEndText = 'Good job! Please take a short break. You have completed %s / %s blocks. \n\nFeel free to move a bit or stretch now, but please remember to remain still with your legs and ankles uncrossed throughout the task. \n\nAlso remember to wait for each response screen to appear before responding. \n\nPlease let me know when you are ready to continue.' % (lightToneTrialInfo[lastTrial]['block'], curLightToneTrial['numBlocks'])
            breakInstr = visual.TextStim(win=win,text=LTblockEndText, color="white", height=45, wrapWidth=800, pos=(0, 150))
            breakInstr.draw()
            win.flip()
            event.waitKeys(keyList= ['space'])
            sayFocus(focusText)
            logging.warning("initiating trial")
            showTrial(curLightToneTrial, lightToneDatafileHeader, lightToneOutputFile, lightToneYN, win, responseScreen, responseKeys, confidenceStim, confidenceKeys, askText)
            win.flip()
            setBiopacDIN(6) # turn DIN back on to signal start to a new block
            clearBiopacDINs()
        # If still in same block, then show the trial
        else:
            logging.warning("initiating trial")
            showTrial(curLightToneTrial, lightToneDatafileHeader, lightToneOutputFile, lightToneYN, win, responseScreen, responseKeys, confidenceStim, confidenceKeys, askText)
            win.flip()
    clearBiopacDINs()



    #### HEARTBEAT-TONE ####
    # Is it a lightTone block? Y or N
    lightToneYN = 'N'
    askText = HTresponseText
    focusText = HTfocusText
    responseScreen = visual.TextStim(win=win,text=askText, color="white", height=50, wrapWidth=1100, pos=(0, 150))


    ## Instructions
    HTinstructions1 = visual.TextStim(win=win,text=HTinstrText1, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 50))
    HTinstructions1.draw()
    win.flip()
    event.waitKeys(keyList=['space'])
    #
    HTinstructions2 = visual.TextStim(win=win,text=HTinstrText2, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 150))
    HTinstructions2.draw()
    win.flip()
    event.waitKeys(keyList=['space'])
    #
    HTinstructions2b = visual.TextStim(win=win,text=HTinstrText2b, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 150))
    HTinstructions2b.draw()
    win.flip()
    event.waitKeys(keyList=['space'])
    #
    HTinstructions3 = visual.TextStim(win=win,text=HTinstrText3, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 150))
    HTinstructions3.draw()
    win.flip()
    time.sleep(20)
    #
    HTinstructions4 = visual.TextStim(win=win,text=HTinstrText4, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 150))
    HTinstructions4.draw()
    win.flip()
    event.waitKeys(keyList=['space'])
    #
    HTinstructions5 = visual.TextStim(win=win,text=HTinstrText5, color="white", height=45, wrapWidth=1100, alignHoriz='center', pos=(0, 150))
    HTinstructions5.draw()
    win.flip()
    event.waitKeys(keyList=['space'])

    ## Practice trials
    sayFocus(focusText)
    for i,curPracticeTrial in enumerate(practiceTrialInfo):
        showTrial(curPracticeTrial, practiceDatafileHeader, practiceOutputFile, lightToneYN, win, responseScreen, responseKeys, confidenceStim, confidenceKeys, askText)
    # Ask if they want to practice again
    practiceAgain.draw()
    win.flip()
    # Allow 'y' or 'n' key responses (idea is that experimenter should press these after asking participant)
    practiceAgainYN = event.waitKeys(keyList=['y','n'])
    # If yes
    if practiceAgainYN[0][0] == 'y' :
        # Run practice trials again
        sayFocus(focusText)
        for i,curPracticeTrial in enumerate(practiceTrialInfo):
            showTrial(curPracticeTrial, practiceDatafileHeader, practiceOutputFile, lightToneYN, win, responseScreen, responseKeys, confidenceStim, confidenceKeys, askText)
    ## Actual trials
    HTstart = visual.TextStim(win=win,text=HTstartText, color="white", height=45, wrapWidth=900, alignHoriz='center', pos=(0, 150))
    HTstart.draw()
    win.flip()
    event.waitKeys(keyList=['space'])

    # For each trial in trialInfo
    # Tell biopac to mark the block
    setBiopacDIN(6)
    clearBiopacDINs()
    # Begin heartbeat-tone blocks
    sayFocus(focusText)
    for i,curTrial in enumerate(trialInfo):
        logging.warning("curtrial Block = %s" % curTrial['block'])
        if i != 1 :
            lastTrial = i - 1
        else:
            lastTrial = i
        logging.warning("Last trial Block = %s" % trialInfo[lastTrial]['block'])
        # Find when the block switched
        blockDifference = int(curTrial['block']) - int(trialInfo[lastTrial]['block'])
        # If it is a new block, show break screen rather than next trial
        if blockDifference == 1 :
            HTblockEndText = 'Good job! Please take a short break. You have completed %s / %s blocks. \n\nFeel free to move a bit or stretch now, but please remember to remain still with your legs and ankles uncrossed throughout the task. \n\nAlso remember to wait for each response screen to appear before responding. \n\nPlease let me know when you are ready to continue.' % (trialInfo[lastTrial]['block'], curTrial['numBlocks'])
            breakInstr = visual.TextStim(win=win,text=HTblockEndText, color="white", height=45, wrapWidth=800, pos=(0, 150))
            breakInstr.draw()
            win.flip()
            event.waitKeys(keyList= ['space'])
            sayFocus(focusText)
            logging.warning("initiating trial")
            showTrial(curTrial, datafileHeader, outputFile, lightToneYN, win, responseScreen, responseKeys, confidenceStim, confidenceKeys, askText)
            win.flip()
            setBiopacDIN(6) # turn DIN back on to signal start to a new block
            clearBiopacDINs()
        # If still in same block, then show the trial
        else:
            logging.warning("initiating trial")
            showTrial(curTrial, datafileHeader, outputFile, lightToneYN, win, responseScreen, responseKeys, confidenceStim, confidenceKeys, askText)
            win.flip()
    clearBiopacDINs()

    #### CONCLUSION ####
    win.flip()
    conclusionText = "Thank you. You have finished the task."
    conclusionStim = visual.TextStim(win=win,text=conclusionText, color="white", height=45, wrapWidth=800, pos=(0, 100))
    conclusionStim.draw()
    win.flip()
    setBiopacDIN(7) # Tell biopac to record end of task
    clearBiopacDINs()
    event.waitKeys(keyList= ['space'])
