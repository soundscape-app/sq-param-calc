'''
Loudness calculation according to ISO532-1,
methods for stationary and time varying signals
'''
import math
from core import *
import locale
ld = __import__("loudness_ISO532-1", fromlist = ["loudness_ISO532-1"])
ldh = __import__("loundess_ISO532-1_helper", fromlist = ["loudness_ISO532-1_helper"])

# Constant
MAX_BUF_SIZE = 256

# Name of output file (*.csv) for specific loudness 
SPECL_OUT_NAME = "SpecLoudness"
# Output: number of digits after comma
OUTPUT_PREC = 4
# % percentile to output
P_OUTPUT = 5
# Name of output file for loudness (savedas *.csv)
LOUD_OUT_NAME = "Loudness"

#Sampling rate to which output/total summed loudness is downsampled
SR_LOUDNESS = 500

CalculationModeFromLevels = 0
CalculationModeFromSignal = 1
CalculationModeInvalid = 2

def main(argv):
    Signal = InputData()
    RefSignal = InputData()

    argc = len(argv)

    DecFactorLevel = 1
    DecFactorLoudness = 1
    SampleLevel = 1
    SampleRateLoudness = 1
    NumSamplesLevel = 1
    NumSamplesLoudness = 1

    locale.setlocale(locale.LC_ALL, "English")

    currentCmdArgIndex = 1

    # First Argument: Stationary|Time_varying
    if(argc > currentCmdArgIndex):
        CmdArgBuffer = argv[currentCmdArgIndex]
        if(CmdArgBuffer[:4] == "STAT"):
            Method = LoudnessMethodStationary
        elif(CmdArgBuffer[:4] == "Time"):
            Method = LoudnessMethodTimeVarying
        else:
            ldh.f_print_err_msg_and_exit("Unsupported loudness method.")
    
    # Second argument: (F|D)
    currentCmdArgIndex = 2
    if(argc > currentCmdArgIndex):
        CmdArgBuffer = argv[currentCmdArgIndex]
        if(CmdArgBuffer[0] == "D"):
            SoundField = SoundFieldDiffuse
        elif(CmdArgBuffer[0] == "F"):
            SoundField = SoundFieldFree
        else:
            ldh.f_print_err_msg_and_exit("Unsupported sound field type")
    
    '''
    Third argument:
			if Method == LoudnessMethodStationary
				argc == 4: 28 colon separated levels or text file with levels
				argc == 5: 32-bit float WAVE file
				argc == 7: 16-bit integer WAVE file
			if Method == LoudnessMethodTimeVarying
				argc == 4: 32-bit float WAVE file
				argc == 6: 16-bit integer WAVE file	
    '''
    
    currentCmdArgIndex = 3
    if(argc > currentCmdArgIndex):
        if((Method == LoudnessMethodStationary and argc > currentCmdArgIndex + 1) or \
           (Method == LoudnessMethodTimeVarying and argc > currentCmdArgIndex)):
            CalculationMode = CalculationModeFromSignal

            InputName = (argv[currentCmdArgIndex])[:MAX_BUF_SIZE]
            
            ReferenceFileNeeded = ldh.f_read_wavfile(InputName)
            
            currentCmdArgIndex = 4
            if(argc > currentCmdArgIndex + 1):
                # Fourth argument: name of reference file
                ReferenceName = (argv[currentCmdArgIndex])[:MAX_BUF_SIZE]

                # Fifth argument: reference level
                currentCmdArgIndex = 5
                CmdArgBuffer = (argv[currentCmdArgIndex])[:MAX_BUF_SIZE]
                
                ldh.f_replace_comma_with_dot(CmdArgBuffer, MAX_BUF_SIZE)

                ReferenceLevel = float(CmdArgBuffer)
                if(ReferenceLevel < 20 or ReferenceLevel > 120):
                    ldh.f_print_err_msg_and_exit("please choose 20 < 'Calibration level in dB rms' < 120")
                
                # Read reference file
                if(ldh.f_read_wavfile(ReferenceName, RefSignal) != 1):
                    ldh.f_print_err_msg_and_exit("Reference file contains no integer data")
                
                # Calculate calibration factor
                pData = 0
                IntensSum = 0
                for IdxTime in range(RefSignal.NumSamples):
                    IntensSum += (RefSignal.pData[pData] ** 2)
                    pData += 1
                IntensSum /= RefSignal.NumSamples
                CalFactor = math.sqrt((10 ** (ReferenceLevel / 10)) * I_REF / IntensSum)
                
                # Apply calibration factor to input signal
                pData = 0
                for IdxTime in range(Signal.NumSamples):
                    Signal.pData[pData] *= CalFactor
                    pData += 1
                
                currentCmdArgIndex = 6
            else:
                if(ReferenceFileNeeded == 1):
                    ldh.f_print_err_msg_and_exit("For integer data please specify calibration file and calibration level")
                
            # Fourth or sixth argument
            # when Method == LoudnessMethodStationary: time skip
            if(Method == LoudnessMethodStationary):
                if(argc > currentCmdArgIndex):
                    CmdArgBuffer = argv[currentCmdArgIndex][:MAX_BUF_SIZE]

                    ldh.f_replace_comma_with_dot(CmdArgBuffer, MAX_BUF_SIZE)

                    TimeSkip = float(CmdArgBuffer)
                    if(TimeSkip < 0 or TimeSkip > 1):
                        ldh.f_print_err_msg_and_exit("0 <= <time skip value> / s <= 1")
                    if(TimeSkip >= Signal.NumSamples / Signal.SampleRate):
                        ldh.f_print_err_msg_and_exit("<time skip value> >= signal duration")
                else:
                    ldh.f_print_err_msg_and_exit("Input argument <time skip value> missing.")
            else:
                CalculationMode = CalculationModeFromLevels

                NumSamplesLevel = 1

                ThirdOctaveLevel = [[0 for _ in range(NumSamplesLevel)] for _ in range(N_LEVEL_BANDS)]

                # Check loudness method
                if(Method == LoudnessMethodTimeVarying):
                    ldh.f_print_err_msg_and_exit("Direct input of third octave levels only supported for stationary method")

                # Copy argument
                CmdArgBuffer = argv[currentCmdArgIndex][:MAX_BUF_SIZE]
                
                # If colon separated list, this argument is a list of third octave levels
                if(ldh.f_is_colon_separated_list(CmdArgBuffer, MAX_BUF_SIZE)):
                    ldh.f_replace_comma_with_dot(CmdArgBuffer, MAX_BUF_SIZE)
                    
                    retval = ldh.f_levels_from_list(ThirdOctaveLevel, CmdArgBuffer, MAX_BUF_SIZE)
                    if(retval < 0):
                        ldh.f_print_err_msg_and_exit("Extraction of level values from input argument failed")

                # otherwise it is assumed to be the filename of a file containing the third octave levels
                else:
                    retval = ldh.f_levels_from_file(ThirdOctaveLevel, CmdArgBuffer)
                    if(retval < 0):
                        ldh.f_print_err_msg_and_exit("Reading levels from file failed")
    
    # Set locate back to default
    locale.setlocale(locale.LC_ALL, "")

    if(Method == LoudnessMethodTimeVarying): # Always from signal
        SampleRateLevel = SR_LEVEL
        SampleRateLoudness = SR_LOUDNESS
        DecFactorLevel = (int)(Signal.SampleRate / SampleRateLevel)
        DecFactorLoudness = (int)(SampleRateLevel / SampleRateLoudness)
        NumSamplesLevel = Signal.NumSamples / DecFactorLevel
        NumSamplesLoudness = NumSamplesLevel / DecFactorLoudness
    
    # Memory Allocation
    
    OutLoudness = [0. for _ in range(NumSamplesLevel)]
    OutSpecLoudness = [[0. for _ in range(NumSamplesLevel)] for _ in range[N_BARK_BANDS]]

    # Actual loudness calculation
    if(CalculationMode == CalculationModeFromSignal):
        retval = ldh.f_loudness_from_signal(Signal, SoundField, Method, TimeSkip, \
                                            OutLoudness, OutSpecLoudness, NumSamplesLevel)
    elif(CalculationMode == CalculationModeFromLevels):
        retval = ldh.f_loudness_from_levels(ThirdOctaveLevel, NumSamplesLevel, SoundField, \
                                            Method, OutLoudness, OutSpecLoudness)
    else:
        ldh.f_print_err_msg_and_exit("Internal error occured")
    
    if(retval < 0):
        if(retval == LoudnessErrorOutputVectorTooSmall):
            ldh.f_print_err_msg_and_exit("result vector too small")
        else:
            ldh.f_print_err_msg_and_exit("An error occurred during loudness calculation")
    
    NumSamplesLevel = retval

    # PostProcessing

    if(SoundField == SoundFieldDiffuse):
        SoundFieldString = "diffues field"
    elif(SoundField == SoundFieldFree):
        SoundFieldString = "free field"
    else:
        ldh.f_print_err_msg_and_exit("Invalid sound field type")
    
    # Downsampling to SR_LOUDNESS for time varying loudness
    if(Method == LoudnessMethodTimeVarying):
        ldh.f_write_specloudness_to_file(OutSpecLoudness, NumSamplesLevel, DecFactorLoudness,\
                                         SPECL_OUT_NAME, SoundField, SampleRateLoudness, OUTPUT_PREC, P_OUTPUT)

        NumSamplesLoudness = ldh.f_downsampling(OutLoudness, OutLoudness, NumSamplesLevel, DecFactorLoudness)
        Maximum = ldh.f_max_of_buffer(OutLoudness, P_OUTPUT, NumSamplesLoudness)
        Percentile = ldh.f_calc_percentile(OutLoudness, P_OUTPUT, NumSamplesLoudness)

        ldh.f_write_loudness_to_file(OutLoudness, NumSamplesLoudness, 1, LOUD_OUT_NAME, Maximum, Percentile, \
                                     SoundField, SampleRateLoudness, OUTPUT_PREC, P_OUTPUT)
        LoudnessLevel = ldh.f_sone_to_phon(Percentile)

        print(f"\nLoudness (Nmax) / sone ({SoundFieldString}): {Maximum : 6.2f}\n\nLoudness (N{P_OUTPUT}) /sone ({SoundFieldString}): {Percentile : 6.2f}")
    else:
        ldh.f_write_specloudness_to_file(OutSpecLoudness, NumSamplesLevel, DecFactorLoudness, SPECL_OUT_NAME, \
                                         SoundField, SampleRateLoudness, OUTPUT_PREC, P_OUTPUT)

        ldh.f_write_loudness_to_file(OutLoudness, NumSamplesLevel, 1, LOUD_OUT_NAME, OutLoudness[0], OutLoudness[0], \
                                     SoundField, SampleRateLoudness, OUTPUT_PREC, P_OUTPUT)
        
        LoudnessLevel = ldh.f_sone_to_phon(OutLoudness[0])
        print(f"\nLoudness (N) / sone ({SoundFieldString}): {OutLoudness[0] : 6.2f}\n\nLoudness level (LN) / phon ({SoundFieldString}): {LoudnessLevel : 5.1f}")
        