'''
Loudness calculation according to ISO 532-1
methods for stationary and time varying signals
Helper methods
'''

import math
from .loudness_ISO532_1 import *
from .core import *
import struct

#constant
M_PI = math.pi

class KaiserBessel:
    def __init__(self):
        self.BetaKaiser = 0
        self.BesselOfBeta = 0
        self.Length = 0
        self.SquareLenHalf = 0
    

def f_print_err_msg_and_exit(Msg):
    print(f"An error occured:\n{Msg}\n")
    exit(-1)

class Loudness_ISO532_1_helper:
    class Resampling:
        #For resampling
        @staticmethod
        def f_modified_bessel0(X):
            X2 = X*X
            DS = 1.0
            DD = 0.0
            Y = 1.0

            while(True):
                DD += 2.0
                DS *= X2 / (DD * DD)
                Y += DS
                if(not(DS >= 1e-14 * Y)):
                    break

            return Y
        
        #For resampling
        @staticmethod
        def f_kaiser_bessel_init(KB : KaiserBessel, Length, Denominator):
            #Formfactor kaiser window -> 90dB damping
            BETA_KAISER_MAX = 8.96
            #Formfactor kaiser window -> 70dB damping
            BETA_KAISER_MIN = 6.75
            DELTA_F_MAX = 0.07

            BetaKaiser = BETA_KAISER_MAX
            DeltaF = Denominator * (BetaKaiser / 0.1102 + 0.7) / \
            (2.0 * M_PI * 2.285 * Length)

            if (DeltaF > DELTA_F_MAX):
                BetaKaiser = (2.285 * Length * 2.0 * M_PI * DELTA_F_MAX - 0.7) *\
                0.1102 / Denominator
            if (BetaKaiser < BETA_KAISER_MIN):
                BetaKaiser = BETA_KAISER_MIN
            
            KB.BetaKaiser = BetaKaiser
            KB.Length = Length
            KB.BesselOfBeta = Loudness_ISO532_1_helper.Resampling.\
                f_modified_bessel0(BetaKaiser)
            KB.SquareLenHalf = (Length / 2.0) ** 2

        #For resampling
        @staticmethod
        def f_kaiser_bessel_calculate(X, KB : KaiserBessel):
            ArgBessel = None #double
            ArgSqrt = 1.0 - X * X / KB.SquareLenHalf
            
            if (ArgSqrt >= 0.0):
                ArgBessel = KB.BetaKaiser * math.sqrt(ArgSqrt)
            else:
                ArgBessel = 0.0
                
            return Loudness_ISO532_1_helper.Resampling.f_modified_bessel0(ArgBessel)\
                /KB.BesselOfBeta
            
        #Si function
        @staticmethod
        def f_si(X):
            if(X == 0):
                return 1
            else:
                return (math.sin(X) / X)
            
        #Calculates impulse response of FIR filter: filter coefficients for resampling lowpass
        @staticmethod
        def f_create_resampling_filter(NumImpResp, Numerator, KB : KaiserBessel, pFiltImpResp):
            CoefSum = 0
            pCoeffs = 0 #pointer idx
            
            #for loop
            IdxImpR = 0
            X = -0.5 * math.floor(NumImpResp - 1)
            while(IdxImpR < NumImpResp):
                pFiltImpResp[pCoeffs] = Loudness_ISO532_1_helper.Resampling.f_si(M_PI / Numerator * X) \
                    * Loudness_ISO532_1_helper.Resampling.f_kaiser_bessel_calculate(X, KB)
                CoefSum += pFiltImpResp[pCoeffs]
                pCoeffs += 1
                IdxImpR += 1
                X += 1.0
            
            if (CoefSum != 0):
                Factor = Numerator / CoefSum
                
                pCoeffs = 0
                
                for IdxImpR in range(0, NumImpResp):
                    pFiltImpResp[pCoeffs] *= Factor
                    pCoeffs += 1
            #Lowpass filtering and decimation
            @staticmethod
            def f_resample_filter(pInput, pOutput, pFiltImpResp, NumInSamples,\
            NumOutSamples, NumCoeffs, Denominator, Numerator, Delay):
                IdxOut, IdxLastS, IdxIn, IdxImpR, Diff, Offset = None #int
                pOutputIdx = 0
                for IdxOut in range(Delay, NumOutSamples + Delay):
                    pCoeffs = 0
                    
                    Diff = (IdxOut * Denominator) % Numerator
                    
                    IdxLastS = IdxOut * Denominator / Numerator
                    
                    pCoeffs +=Diff
                    IdxImpR = Diff
                    
                    if(IdxLastS - NumInSamples >= 0):
                        Offset = (IdxLastS - NumInSamples + 1) * Numerator
                        pCoeffs += Offset
                        IdxImpR += Offset
                        IdxLastS = NumInSamples - 1
                        
                    IdxIn = IdxLastS
                    pIn = IdxIn
                    while(IdxIn >= 0 and IdxImpR <= NumCoeffs):
                        pOutput[pOutputIdx] += pInput[pIn] * pFiltImpResp[pCoeffs]
                        pCoeffs += Numerator
                        pIn -= 1
                        IdxIn -= 1
                        IdxImpR += Numerator
                    pOutputIdx += 1
            
            #Resamples signal from 44.1kHz or 32kHz to 48kHz
            @staticmethod
            def f_resample_to_48kHz(pSignal : InputData):
                FilterOrder = 256
                NumSamplesOld = pSignal.numSamples
                SampleRateOld = pSignal.SampleRate
                KB = KaiserBessel()
                
                if(SampleRateOld == 32000):
                    Numerator = 3
                    Denominator = 2
                elif(SampleRateOld == 44100):
                    Numerator = 160
                    Denominator = 147
                else:
                    Numerator = 1
                    Denominator = 1
                
                NumImpResp = FilterOrder * Numerator
                NumImpResp = (int)(math.floor(NumImpResp / 2.0) * 2 + 1)
                LHalf = (NumImpResp - 1) / 2
                Lhalf -= (Lhalf % Denominator)
                NumImpResp = 2 * Lhalf + 1
                Delay = Lhalf / Denominator
                
                Loudness_ISO532_1_helper.Resampling.f_kaiser_bessel_init(KB, NumImpResp, Denominator)
                pFiltImpResp = [0 for i in range(NumImpResp)]
                Loudness_ISO532_1_helper.Resampling.f_create_resampling_filter(NumImpResp, Numerator, \
                    KB, pFiltImpResp)
                NumSamples = (NumSamplesOld * Numerator) / Denominator
                
                pResampledSignal = [0 for i in range(NumSamples)]
                
                f_resample_filter(pSignal.pData, pResampledSignal, pFiltImpResp,\
                    NumSamplesOld, NumSamples, NumImpResp, Denominator, Numerator, Delay)
                pSignal.pData = pResampledSignal
                pSignal.sampleRate = 48000
                pSignal.numSamples = NumSamples
                
                return 0
    class Read_WAVE_file:
        #Read wav input-file
        @staticmethod
        def f_read_wavfile(pFileName, Input : InputData):
            class wavfile:
                def __init__(self):
                    self.Id = None
                    self.FormatTag = 0
                    self.Channels = 0
                    self.BlockAlign = 0
                    self.BitsPerSample = 0
                    self.pTemp16 = None
                    self.pTemp32 = None
                    self.Size = 0
                    self.FormatLength = 0
                    self.SampleRate = 0
                    self.BytesSec = 0
                    self.DataSize = 0
                    self.Successful = 0
                    self.ExtraParam = 0
                    self.NumSamples = 0
                    self.pData = None
            Signal = wavfile()
            pfile = open(pFileName, "rb")
            if (pfile):
                #ID, Should be RIFF
                Signal.Id = pfile.read(4)
                if(Signal.Id == "RIFF".encode()):
                    #Size-8
                    Signal.Size = int.from_bytes(pfile.read(1 * 4), "little")
                    #ID, Should be WAVE
                    Signal.Id = pfile.read(4)
                    if(Signal.Id == "WAVE".encode()):
                        #Format string
                        Signal.Id = pfile.read(4)
                        #Format length
                        Signal.FormatLength = int.from_bytes(pfile.read(1 * 4), "little")
                        #Format tag
                        Signal.FormatTag = int.from_bytes(pfile.read(1 * 2), "little")
                        if (Signal.FormatTag == PCM or Signal.FormatTag == IEEE_FLOAT):
                            #Channels, only one channel supported
                            Signal.Channels = int.from_bytes(pfile.read(1 * 2), "little")
                            if(Signal.Channels == 1):
                                #Sample rate
                                Signal.SampleRate = int.from_bytes(pfile.read(1 * 4), "little")
                                #Bytes/second
                                Signal.BytesSec = int.from_bytes(pfile.read(1 * 4), "little")
                                #Frame size, number of bytes/sample
                                Signal.BlockAlign = int.from_bytes(pfile.read(1 * 2), "little")
                                #Bits/sample
                                Signal.BitsPerSample = int.from_bytes(pfile.read(1 * 2), "little")
                                if(Signal.FormatLength != 16):
                                    Signal.ExtraParam = int.from_bytes(pfile.read(1 * 2), "little")
                                #Signature, should be 'data'
                                Signal.Id = pfile.read(4)
                                if(Signal.Id == "data".encode()):
                                    #Number of bytes in data block
                                    Signal.DataSize = int.from_bytes(pfile.read(1 * 4), "little")
                                    Signal.NumSamples = Signal.DataSize // Signal.BlockAlign
                                    if(Signal.BitsPerSample == 16):
                                        Input.pData = [0.0 for _ in range(Signal.NumSamples)]
                                        Signal.pTemp16 = [0 for _ in range(Signal.NumSamples)]
                                        for i in range(Signal.NumSamples):
                                            Signal.pTemp16[i] = int.from_bytes(pfile.read(1 * 2), "little")
                                        pData = Input.pData
                                        pTemp16 = Signal.pTemp16
                                        for IdxTime in range(Signal.NumSamples):
                                            pData[IdxTime] = (float)(pTemp16[IdxTime]) / 32768
                                        Input.numSamples = Signal.NumSamples
                                        Input.sampleRate = (float)(Signal.SampleRate)
                                    elif(Signal.BitsPerSample == 32):
                                        Input.pData = [0.0 for _ in range(Signal.NumSamples)]
                                        Signal.pTemp32 = [0.0 for _ in range(Signal.NumSamples)]
                                        for i in range(Signal.NumSamples):
                                            byte_arr = pfile.read(1 * 4, "little")
                                            binary_str = b''.join(byte_arr)
                                            Signal.pTemp16[i] = struct.unpack('<f', binary_str)[0]
                                        pData = Input.pData
                                        pTemp32 = Signal.pTemp32
                                        NanFoundInFile = 0
                                        for IdxTime in range(Signal.NumSamples):
                                            if(math.isnan(pTemp32[IdxTime])):
                                                pData[IdxTime] = 0.0
                                                NanFoundInFile = 1
                                            else:
                                                pData[IdxTime] = (float)(pTemp32[IdxTime])
                                        Input.numSamples = Signal.NumSamples
                                        Input.sampleRate = (float)(Signal.SampleRate)
                                        if(NanFoundInFile == 1):
                                            f_print_err_msg_and_exit("WAVE file may not contain NaN values")
                                    else:
                                        f_print_err_msg_and_exit("only 16-bit and 32-bit WAVE files are allowed")
                                else:
                                    f_print_err_msg_and_exit("invalid header")
                            else:
                                f_print_err_msg_and_exit("only files containing on channel are allowed")
                        else:
                            f_print_err_msg_and_exit("only PCM and IEEE FLOAT wav files are allowed")
                    else:
                        f_print_err_msg_and_exit("not a WAVE file")
                else:
                    f_print_err_msg_and_exit("not a RIFF file")
                pfile.close()
            else:
                f_print_err_msg_and_exit("file not found")
                
            if(Signal.SampleRate != 48000):
                if(Signal.SampleRate == 32000 or Signal.SampleRate == 44100):
                    retval = Loudness_ISO532_1_helper.Resampling.f_resample_to_48kHz(Input)
                    if(retval < 0):
                        f_print_err_msg_and_exit("Resampling failed")
                else:
                    f_print_err_msg_and_exit("only sampling rates of 32kHz, 44.1kHz or 48kHz supported")
            
            if(Signal.BitsPerSample == 32):
                return 0
            else:
                return 1
            
    class Maximum_and_percentile_calculation:
        #returns maximum value of buffer
        @staticmethod
        def f_max_of_buffer(pSignal, NumSamples):
            Maximum = 0
            
            for IdxTime in range(NumSamples):
                if(pSignal[IdxTime] > Maximum):
                    Maximum = pSignal[IdxTime]
                    
            return Maximum
        
        #Comparing function for qsort
        @staticmethod
        def f_compare(a, b):
            if(a < b):
                return -1
            return (a > b)
        
        #Sorts buffer and computes percentile value
        @staticmethod
        def f_calc_percentile(pSignal, Percentile, NumSamples):
            Np = (int)((1 - Percentile / 100.) * NumSamples)
            
            pSortBuffer = [0. for _ in range(NumSamples)]
            for IdxTime in range(NumSamples):
                pSortBuffer[IdxTime] = pSignal[IdxTime]
            
            pSortBuffer.sort(key = \
                Loudness_ISO532_1_helper.Maximum_and_percentile_calculation.f_compare)
            
            PercentileValue = 0.                  
            
            if(Percentile == 0):
                PercentileValue = pSortBuffer[NumSamples - 1]
            elif(Percentile == 100):
                PercentileValue = pSortBuffer[0]
            else:
                PercentileValue = (pSortBuffer[Np - 1] + pSortBuffer[Np]) / 2
            
            return PercentileValue

    class Write_results_to_file:
        #Output: write specific loudness to file
        @staticmethod
        def f_write_specloudness_to_file(pData, NumSamples, DecFactor, pFileName, \
            SoundField, SampleRateLoudness, OutputPrecision, OutputPercentile):
            TimeRes = 1. / SampleRateLoudness * 1000
            NameWithEnding = pFileName + ".csv"
            pFile = open(NameWithEnding, "w")
            SoundFieldStrine = None
            if(not pFile):
                Count = 1
                while(not pFile and Count < 10):
                    NameWithEnding = f"{pFileName}({Count}).csv"
                    Count += 1
                if(Count == 10):
                    Str1 = f"Could not write to file {NameWithEnding}"
                    f_print_err_msg_and_exit(Str1)
            
            if(SoundField == SoundFieldDiffuse):
                SoundFieldString = "diffuse field"
            elif(SoundField == SoundFieldFree):
                SoundFieldString = "free field"
            
            if(NumSamples > 1):
                pFile.write("Specific loudness calculation according to ISO532 for time varying sounds;\n;")
            else:
                pFile.write("Specific loudness calculation according to ISO 532-1 for stationary sounds;\n;")
            pFile.write(f"N' / (sone / Bark) ({SoundFieldString})\n;", end = "")
            pFile.write(f"t / s \\ Bark;", end = "")
            for IdxFB in range(N_BARK_BANDS):
                pFile.write(f"{((float)(IdxFB + 1) / 10) : .{OutputPrecision}f};", end = "")
            pFile.write()
            for IdxTime in range(NumSamples):
                pFile.write(f"{(float)(IdxTime) / (float)(SampleRateLoudness) / (float)(DecFactor) : .{OutputPrecision}f};", end = "")
                for IdxFB in range(N_BARK_BANDS):
                    pFile.write(f"{pData[IdxFB][IdxTime] : .{OutputPrecision}f};", end = "")
                pFile.write()
            pFile.close()
            
        #Output: write loudness buffer to file
        @staticmethod
        def f_write_loudness_to_file(pData, NumSamples, DecFactor, pFileName,\
            Maximum, Percentile, SoundField, SampleRateLoudness, OutputPrecision, OutputPercentile):
            TimeRes = 1. / SampleRateLoudness * 1000
            NameWithEnding = f"{pFileName}.csv"
            Strf = f".{OutputPrecision}f"
            pFile = open(NameWithEnding, "w")
            if(not pFile):
                Count = 1
                while(not pFile and Count < 10):
                    NameWithEnding = f"{pFileName}({Count}).csv"
                    pFile = open(NameWithEnding, "w")
                if(Count == 10):
                    Str1 = f"could not write to file {NameWithEnding}"
                    f_print_err_msg_and_exit(Str1)
            
            if(SoundField == SoundFieldDiffuse):
                SoundFieldString = "diffuse field"
            elif(SoundField == SoundFieldFree):
                SoundFieldString = "free field"
            
            if(NumSamples > 1):
                pFile.write("Loudness calculation according to ISO 532-1 for time varying sounds;\n;")
                
                Str1 = f"{Maximum : {Strf}}"
                pFile.write(f"Nmax / sone ({SoundFieldString}); {Str1}")
                
                Str1 = f"{Percentile : {Strf}}"
                pFile.write(f"N{OutputPercentile} / sone ({SoundFieldString}); {Str1}")
                
                pFile.write(f";\nt / s; N / sone ({SoundFieldString})")
                
                pDataIdx = 0
                for IdxTime in range(NumSamples // DecFactor):
                    pFile.write(f"{(float)(IdxTime) / (float)(SampleRateLoudness) : {Strf}};{pData[pDataIdx] : {Strf}}")
                    pDataIdx += DecFactor
            else:
                pFile.write("Loudness calculation according to ISO 532-1 for stationary sounds;\n;")
                
                Str1 = f"{Maximum : {Strf}}"
                pFile.write(f"N / sone ({SoundFieldString}); {Str1}")
            
                Str1 = f"{Loudness_ISO532_1_helper.Write_results_to_file.f_sone_to_phon(Maximum) : {Strf}}"
                pFile.write(f"LN / phon ({SoundFieldString}); {Str1}")
            pFile.close()
        
        #Decimation by DecFactor
        @staticmethod
        def f_downsampling(pInput, pOutput, NumInSamples, DecFactor):
            NumOutSamples = NumInSamples / DecFactor
            
            pX = 0 #pInput
            pY = 0 #pOutput
            for IdxTime in range(NumOutSamples):
                pOutput[pY] = pInput[pX]
                pX += DecFactor
                pY += 1
            
            return NumOutSamples
        
        #Conversion from sone to phon
        @staticmethod
        def f_sone_to_phon(Loudness):
            LoudnessLevel = None
            if (Loudness < 1.):
                LoudnessLevel = 40. * ((Loudness + .0005) ** .35)
                if(LoudnessLevel < 3.):
                    LoudnessLevel = 3.
            else:
                LoudnessLevel = 10. * ((math.log(Loudness))) / math.log(2.) + 40.
            return LoudnessLevel
        
        #Replace commas in a string with a dot
        @staticmethod
        def f_replace_comma_with_dot(value, length):
            ret = ""
            for i in range(len(value)):
                if(value[i] == ',' and i < length):
                    ret += '.'
                else:
                    ret += value[i]
            return ret
        
        #Check if the stirng is a colon separated list, i.e. contains at least one colon
        @staticmethod
        def f_is_colon_separated_list(value, length):
            counter = 0
            for i in range(length):
                if(value[i] == ':'):
                    counter += 1
            if(counter == N_LEVEL_BANDS - 1):
                return 1
            return 0
        
        #Read 28 third octave levels from a colon separated list
        @staticmethod
        def f_levels_from_list(ThirdOctaveLevels, listString, length):
            valueCounter = 0
            startPosition = 0
            endPosition = 0
            
            while(valueCounter < N_LEVEL_BANDS - 1 and endPosition < length):
                if(listString[endPosition] != ':'):
                    endPosition += 1
                else:
                    endPosition += 1
                    value = float(listString + startPosition)
                    ThirdOctaveLevels[valueCounter][0] = value
                    valueCounter += 1
                    startPosition = endPosition
            
            if(valueCounter == N_LEVEL_BANDS - 1 and startPosition < length):
                value = float(listString + startPosition)
                ThirdOctaveLevels[valueCounter][0] = value
            else:
                return -1
            return 0
        
        #Check if string is an empty line, i.e. only white space
        @staticmethod
        def f_is_empty_line(buffer, bufferSize):
            for i in range(bufferSize):
                if(buffer[i] == 0):
                    break
                if(buffer[i] != ' ' and buffer[i] != '\t' and buffer[i] != '\n'):
                    return 0
            return 1
        
        #Read next non-commment and non-empty line from text file
        @staticmethod
        def f_read_next_line(buffer, bufferSize, file):
            while(True):
                buffer = file.readline()
                if((not buffer) or len(buffer) == bufferSize - 1):
                    return -1
                if(buffer[0] != '#' and Loudness_ISO532_1_helper.Write_results_to_file.f_is_empty_line(buffer, MAX_BUF_SIZE) == 0):
                    return len(buffer)

        #Read 28 third octave levels from file
        @staticmethod
        def f_levels_from_file(ThirdOctaveLevels, filename):
            valueCounter = 0
            line = None
            pfile = open(filename, "rb")
            if(pfile):
                valueCounter = 0
                while(valueCounter < N_LEVEL_BANDS):
                    resultLength = Loudness_ISO532_1_helper.Write_results_to_file.f_read_next_line(line, MAX_BUF_SIZE, pfile)
                    if(resultLength < 0):
                        f_print_err_msg_and_exit("Error while reading file.")
                    
                    Loudness_ISO532_1_helper.Write_results_to_file.f_replace_comma_with_dot(line, resultLength)
                    
                    startPosition = 0
                    while(startPosition < resultLength and line[startPosition] != ':'):
                        startPosition += 1
                    startPosition += 1
                    
                    if(startPosition < resultLength):
                        value = float(line + startPosition)
                        ThirdOctaveLevels[valueCounter][0] = value
                        valueCounter += 1
                    else:
                        f_print_err_msg_and_exit("Invalid line in file.")
            else:
                f_print_err_msg_and_exit("Opening file failed.")
            pfile.close()
            return 0