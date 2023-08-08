'''
Loudness calculation according to ISO 532-1
methods for stationary and time varying signals
Helper methods
'''

import math
ld = __import__("loudness_ISO532-1")
from core import *

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
                Signal.Id = pfile.read(4)
                if(Signal.Id == "RIFF".encode()):
                    Signal.Size = int.from_bytes(pfile.read(1 * 4), "big")
                    Signal.Id = pfile.read(4)
                    if(Signal.Id == "WAVE".encode()):
                        
                    
                    
                    
                
                    
                
                
                
                    
                        
                
                            
                    
            
            
                
            


#For debugging
if __name__ == "__main__":
    pass