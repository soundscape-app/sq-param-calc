'''
Loudness calculation according to ISO532-1,
methods for stationary and time varying signals
'''
import math
from .core import *
import locale
from .loudness_ISO532_1 import *
from .loudness_ISO532_1_helper import *

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

def loudness_main(argv):
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
    Method = 2147483647
    ThirdOctaveLevel = [[0 for _ in range(NumSamplesLevel)] for _ in range(N_LEVEL_BANDS)]
    SoundField = 2147483647

    # First Argument: Stationary|Time_varying
    if(argc > currentCmdArgIndex):
        CmdArgBuffer = argv[currentCmdArgIndex]
        if(CmdArgBuffer[:4] == "Stat"):
            Method = LoudnessMethodStationary
        elif(CmdArgBuffer[:4] == "Time"):
            Method = LoudnessMethodTimeVarying
        else:
            f_print_err_msg_and_exit("Unsupported loudness method.")
    
    # Second argument: (F|D)
    currentCmdArgIndex = 2
    if(argc > currentCmdArgIndex):
        CmdArgBuffer = argv[currentCmdArgIndex]
        if(CmdArgBuffer[0] == "D"):
            SoundField = SoundFieldDiffuse
        elif(CmdArgBuffer[0] == "F"):
            SoundField = SoundFieldFree
        else:
            f_print_err_msg_and_exit("Unsupported sound field type")
    
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
    CalculationMode = 0
    currentCmdArgIndex = 3
    if(argc > currentCmdArgIndex):
        if((Method == LoudnessMethodStationary and argc > currentCmdArgIndex + 1) or \
           (Method == LoudnessMethodTimeVarying and argc > currentCmdArgIndex)):
            CalculationMode = CalculationModeFromSignal

            InputName = (argv[currentCmdArgIndex])[:MAX_BUF_SIZE]
            
            ReferenceFileNeeded = Loudness_ISO532_1_helper.Read_WAVE_file.f_read_wavfile(InputName, Signal)
            
            currentCmdArgIndex = 4
            if(argc > currentCmdArgIndex + 1):
                # Fourth argument: name of reference file
                ReferenceName = (argv[currentCmdArgIndex])[:MAX_BUF_SIZE]

                # Fifth argument: reference level
                currentCmdArgIndex = 5
                CmdArgBuffer = (argv[currentCmdArgIndex])[:MAX_BUF_SIZE]
                
                Loudness_ISO532_1_helper.Write_results_to_file.f_replace_comma_with_dot(CmdArgBuffer, MAX_BUF_SIZE)

                ReferenceLevel = float(CmdArgBuffer)
                if(ReferenceLevel < 20 or ReferenceLevel > 120):
                    f_print_err_msg_and_exit("please choose 20 < 'Calibration level in dB rms' < 120")
                
                # Read reference file
                if(Loudness_ISO532_1_helper.Read_WAVE_file.f_read_wavfile(ReferenceName, RefSignal) != 1):
                    f_print_err_msg_and_exit("Reference file contains no integer data")
                
                # Calculate calibration factor
                pData = 0
                IntensSum = 0
                for IdxTime in range(RefSignal.numSamples):
                    IntensSum += (RefSignal.pData[pData] ** 2)
                    pData += 1
                IntensSum /= RefSignal.numSamples
                CalFactor = math.sqrt((10 ** (ReferenceLevel / 10)) * I_REF / IntensSum)
                
                # Apply calibration factor to input signal
                pData = 0
                for IdxTime in range(Signal.numSamples):
                    Signal.pData[pData] *= CalFactor
                    pData += 1
                
                currentCmdArgIndex = 6
            else:
                if(ReferenceFileNeeded == 1):
                    f_print_err_msg_and_exit("For integer data please specify calibration file and calibration level")
                
            # Fourth or sixth argument
            # when Method == LoudnessMethodStationary: time skip
            if(Method == LoudnessMethodStationary):
                if(argc > currentCmdArgIndex):
                    CmdArgBuffer = argv[currentCmdArgIndex][:MAX_BUF_SIZE]

                    Loudness_ISO532_1_helper.Write_results_to_file.f_replace_comma_with_dot(CmdArgBuffer, MAX_BUF_SIZE)

                    TimeSkip = float(CmdArgBuffer)
                    if(TimeSkip < 0 or TimeSkip > 1):
                        f_print_err_msg_and_exit("0 <= <time skip value> / s <= 1")
                    if(TimeSkip >= Signal.numSamples / Signal.sampleRate):
                        f_print_err_msg_and_exit("<time skip value> >= signal duration")
                else:
                    f_print_err_msg_and_exit("Input argument <time skip value> missing.")
        else:
            CalculationMode = CalculationModeFromLevels

            NumSamplesLevel = 1

            ThirdOctaveLevel = [[0 for _ in range(NumSamplesLevel)] for _ in range(N_LEVEL_BANDS)]

            # Check loudness method
            if(Method == LoudnessMethodTimeVarying):
                f_print_err_msg_and_exit("Direct input of third octave levels only supported for stationary method")

            # Copy argument
            CmdArgBuffer = argv[currentCmdArgIndex][:MAX_BUF_SIZE]
            # If colon separated list, this argument is a list of third octave levels
            print(f"1. {CmdArgBuffer}")
            if(Loudness_ISO532_1_helper.Write_results_to_file.f_is_colon_separated_list(CmdArgBuffer, MAX_BUF_SIZE)):
                print(f"2. {CmdArgBuffer}")
                Loudness_ISO532_1_helper.Write_results_to_file.f_replace_comma_with_dot(CmdArgBuffer, MAX_BUF_SIZE)
                
                retval = Loudness_ISO532_1_helper.Write_results_to_file.f_levels_from_list(ThirdOctaveLevel, CmdArgBuffer, MAX_BUF_SIZE)
                if(retval < 0):
                    f_print_err_msg_and_exit("Extraction of level values from input argument failed")

            # otherwise it is assumed to be the filename of a file containing the third octave levels
            else:
                print(f"3. {CmdArgBuffer}")
                retval = Loudness_ISO532_1_helper.Write_results_to_file.f_levels_from_file(ThirdOctaveLevel, CmdArgBuffer)
                if(retval < 0):
                    f_print_err_msg_and_exit("Reading levels from file failed")
    
    # Set locate back to default
    locale.setlocale(locale.LC_ALL, "")

    if(Method == LoudnessMethodTimeVarying): # Always from signal
        SampleRateLevel = SR_LEVEL
        SampleRateLoudness = SR_LOUDNESS
        DecFactorLevel = (int)(Signal.sampleRate / SampleRateLevel)
        DecFactorLoudness = (int)(SampleRateLevel / SampleRateLoudness)
        NumSamplesLevel = Signal.numSamples // DecFactorLevel
        NumSamplesLoudness = NumSamplesLevel // DecFactorLoudness
    
    # Memory Allocation
    OutLoudness = [0. for _ in range(NumSamplesLevel)]
    OutSpecLoudness = [[0. for _ in range(NumSamplesLevel)] for _ in range(N_BARK_BANDS)]
    TimeSkip = 0

    # Actual loudness calculation
    if(CalculationMode == CalculationModeFromSignal):
        retval = Loudness_ISO532_1.LoudnessCalculation.f_loudness_from_signal(Signal, SoundField, Method, TimeSkip, \
                                            OutLoudness, OutSpecLoudness, NumSamplesLevel)
    elif(CalculationMode == CalculationModeFromLevels):
        retval = Loudness_ISO532_1.LoudnessCalculation.f_loudness_from_levels(ThirdOctaveLevel, NumSamplesLevel, SoundField, \
                                            Method, OutLoudness, OutSpecLoudness)
    else:
        f_print_err_msg_and_exit("Internal error occured")
    if(retval < 0):
        if(retval == LoudnessErrorOutputVectorTooSmall):
            f_print_err_msg_and_exit("result vector too small")
        else:
            f_print_err_msg_and_exit("An error occurred during loudness calculation")
    
    NumSamplesLevel = retval

    # PostProcessing

    if(SoundField == SoundFieldDiffuse):
        SoundFieldString = "diffuse field"
    elif(SoundField == SoundFieldFree):
        SoundFieldString = "free field"
    else:
        f_print_err_msg_and_exit("Invalid sound field type")
    
    # Downsampling to SR_LOUDNESS for time varying loudness
    if(Method == LoudnessMethodTimeVarying):
        Loudness_ISO532_1_helper.Write_results_to_file.f_write_specloudness_to_file(OutSpecLoudness, NumSamplesLevel, DecFactorLoudness,\
                                         SPECL_OUT_NAME, SoundField, SampleRateLoudness, OUTPUT_PREC, P_OUTPUT)

        NumSamplesLoudness = Loudness_ISO532_1_helper.Write_results_to_file.f_downsampling(OutLoudness, OutLoudness, NumSamplesLevel, DecFactorLoudness)
        Maximum = Loudness_ISO532_1_helper.Maximum_and_percentile_calculation.f_max_of_buffer(OutLoudness, NumSamplesLoudness)
        Percentile = Loudness_ISO532_1_helper.Maximum_and_percentile_calculation.f_calc_percentile(OutLoudness, P_OUTPUT, NumSamplesLoudness)

        Loudness_ISO532_1_helper.Write_results_to_file.f_write_loudness_to_file(OutLoudness, NumSamplesLoudness, 1, LOUD_OUT_NAME, Maximum, Percentile, \
                                     SoundField, SampleRateLoudness, OUTPUT_PREC, P_OUTPUT)
        LoudnessLevel = Loudness_ISO532_1_helper.Write_results_to_file.f_sone_to_phon(Percentile)

        print(f"\nLoudness (Nmax) / sone ({SoundFieldString}): {Maximum : 6.2f}\n\nLoudness (N{P_OUTPUT}) / sone ({SoundFieldString}): {Percentile : 6.2f}")
        return (f"{Maximum : 6.2f}", f"{Percentile : 6.2f}", OutSpecLoudness)
    else:
        Loudness_ISO532_1_helper.Write_results_to_file.f_write_specloudness_to_file(OutSpecLoudness, NumSamplesLevel, DecFactorLoudness, SPECL_OUT_NAME, \
                                         SoundField, SampleRateLoudness, OUTPUT_PREC, P_OUTPUT)

        Loudness_ISO532_1_helper.Write_results_to_file.f_write_loudness_to_file(OutLoudness, NumSamplesLevel, 1, LOUD_OUT_NAME, OutLoudness[0], OutLoudness[0], \
                                     SoundField, SampleRateLoudness, OUTPUT_PREC, P_OUTPUT)
        
        LoudnessLevel = Loudness_ISO532_1_helper.Write_results_to_file.f_sone_to_phon(OutLoudness[0])
        print(f"\nLoudness (N) / sone ({SoundFieldString}): {OutLoudness[0] : 6.2f}\n\nLoudness level (LN) / phon ({SoundFieldString}): {LoudnessLevel : 5.1f}")
        return (f"{OutLoudness[0] : 6.2f}", f"{LoudnessLevel : 5.1f}", OutSpecLoudness)
    

        