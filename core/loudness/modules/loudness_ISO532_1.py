'''
ISO532-1에 따른 Loudness 계산 모듈입니다.
'''
import math
import time
from .core import *

# 상수 정의
N_LCBS = 3 
N_LCB_BANDS = 11
N_CORE_LOUDN = 21
N_RAP_RANGES = 8
N_RNS_RANGES = 18
N_CB_RANGES = 8
N_FILTER_STAGES = 3
N_FILTER_COEFS = 6
NL_ITER = 24
LP_ITER = 24
TSHORT = .005
TLONG = .015
TVAR = .075
TINY_VALUE = 1e-12

# 클래스 정의
class NlLpData:
    def __init__(self, sampleRate):
        self.B = [0.0 for _ in range(6)]
        self.UoLast = 0.0
        self.U2Last = 0.0

    def init_helper(self, sampleRate):
        Tvar = TVAR
        Tshort = TSHORT
        Tlong = TLONG

        deltaT      = 1 / sampleRate
        P           = (Tvar + Tlong) / (Tvar * Tshort)
        Q           = 1 / (Tshort * Tvar)
        lambda1     = -P/2 + math.sqrt(P*P/4 - Q)
        lambda2     = -P/2 - math.sqrt(P*P/4 - Q)
        den         = Tvar * (lambda1 - lambda2)
        e1          = math.exp(lambda1 * deltaT)
        e2          = math.exp(lambda2 * deltaT)

        self.B[0] = (e1 - e2) / den
        self.B[1] = ((Tvar * lambda2 + 1) * e1 - (Tvar * lambda1 + 1) * e2) / den
        self.B[2] = ((Tvar * lambda1 + 1) * e1 - (Tvar * lambda2 + 1) * e2) / den
        self.B[3] = (Tvar * lambda1 + 1) * (Tvar * lambda2 + 1) * (e1 - e2) / den
        self.B[4] = math.exp(-deltaT / Tlong)
        self.B[5] = math.exp(-deltaT / Tvar)

    def f_nl_lp(self, Ui):
        if Ui < self.UoLast:
            if self.UoLast > self.U2Last:
                U2 = self.UoLast * self.B[0] - self.U2Last * self.B[1]
                Uo = self.UoLast * self.B[2] - self.U2Last * self.B[3]
                
                if Uo < Ui:
                    Uo = Ui
                if U2 > Uo:
                    U2 = Uo
            else:
                Uo = self.UoLast * self.B[4]
                if Uo < Ui:
                    Uo = Ui
                U2 = Uo
        else:
            if math.fabs(Ui - self.UoLast) < 1e-5:
                Uo = Ui
                if Uo > self.U2Last:
                    U2 = (self.U2Last - Ui) * self.B[5] + Ui
                else:
                    U2 = Ui
            else:
                Uo = Ui
                U2 = (self.U2Last - Ui) * self.B[5] + Ui
        
        self.UoLast = Uo
        self.U2Last = U2

        return Uo

# 함수 정의
def f_nl(coreLoudness, sampleRate, numSamples):
    NlLp = NlLpData(sampleRate * NL_ITER)

    for i in range(N_CORE_LOUDN):
        NlLp.UoLast = 0
        NlLp.U2Last = 0
        idx = i

        for time in range(numSamples - 1):
            nextInput = coreLoudness[idx + 1]
            delta = (nextInput - coreLoudness[idx]) / NL_ITER

            Ui = coreLoudness[idx]
            coreLoudness[idx] = NlLp.f_nl_lp(Ui)
            Ui += delta

            for j in range(1, NL_ITER):
                Uo = NlLp.f_nl_lp(Ui)
                Ui += delta

            idx += 1
        
        coreLoudness[idx] = NlLp.f_nl_lp(coreLoudness[idx])

    return coreLoudness

# Third-Octave Filtering 입니다.
thirdOctaveFilterRef = [
    [1, 2, 1, 1, -2, 1],
    [1, 0, -1, 1, -2, 1],
    [1, -2, 1, 1, -2, 1],
]

thirdOctaveFilters = [   
    [ [0,0,0,0,-6.70260e-004,6.59453e-004],
      [0,0,0,0,-3.75071e-004,3.61926e-004],
      [0,0,0,0,-3.06523e-004,2.97634e-004] ],

    [ [0,0,0,0,-8.47258e-004,8.30131e-004],
      [0,0,0,0,-4.76448e-004,4.55616e-004],
      [0,0,0,0,-3.88773e-004,3.74685e-004] ],

    [ [0,0,0,0,-1.07210e-003,1.04496e-003],
      [0,0,0,0,-6.06567e-004,5.73553e-004],
      [0,0,0,0,-4.94004e-004,4.71677e-004] ],

    [ [0,0,0,0,-1.35836e-003,1.31535e-003],
      [0,0,0,0,-7.74327e-004,7.22007e-004],
      [0,0,0,0,-6.29154e-004,5.93771e-004] ],

    [ [0,0,0,0,-1.72380e-003,1.65564e-003],
      [0,0,0,0,-9.91780e-004,9.08866e-004],
      [0,0,0,0,-8.03529e-004,7.47455e-004] ],

    [ [0,0,0,0,-2.19188e-003,2.08388e-003],
      [0,0,0,0,-1.27545e-003,1.14406e-003],
      [0,0,0,0,-1.02976e-003,9.40900e-004] ],

    [ [0,0,0,0,-2.79386e-003,2.62274e-003],
      [0,0,0,0,-1.64828e-003,1.44006e-003],
      [0,0,0,0,-1.32520e-003,1.18438e-003] ],

    [ [0,0,0,0,-3.57182e-003,3.30071e-003],
      [0,0,0,0,-2.14252e-003,1.81258e-003],
      [0,0,0,0,-1.71397e-003,1.49082e-003] ],

    [ [0,0,0,0,-4.58305e-003,4.15355e-003],
      [0,0,0,0,-2.80413e-003,2.28135e-003],
      [0,0,0,0,-2.23006e-003,1.87646e-003] ],

    [ [0,0,0,0,-5.90655e-003,5.22622e-003],
      [0,0,0,0,-3.69947e-003,2.87118e-003],
      [0,0,0,0,-2.92205e-003,2.36178e-003] ],

    [ [0,0,0,0,-7.65243e-003,6.57493e-003],
      [0,0,0,0,-4.92540e-003,3.61318e-003],
      [0,0,0,0,-3.86007e-003,2.97240e-003] ],

    [ [0,0,0,0,-1.00023e-002,8.29610e-003],
      [0,0,0,0,-6.63788e-003,4.55999e-003],
      [0,0,0,0,-5.15982e-003,3.75306e-003] ],

    [ [0,0,0,0,-1.31230e-002,1.04220e-002],
      [0,0,0,0,-9.02274e-003,5.73132e-003],
      [0,0,0,0,-6.94543e-003,4.71734e-003] ],

    [ [0,0,0,0,-1.73693e-002,1.30947e-002],
      [0,0,0,0,-1.24176e-002,7.20526e-003],
      [0,0,0,0,-9.46002e-003,5.93145e-003] ],

    [ [0,0,0,0,-2.31934e-002,1.64308e-002],
      [0,0,0,0,-1.73009e-002,9.04761e-003],
      [0,0,0,0,-1.30358e-002,7.44926e-003] ],

    [ [0,0,0,0,-3.13292e-002,2.06370e-002],
      [0,0,0,0,-2.44342e-002,1.13731e-002],
      [0,0,0,0,-1.82108e-002,9.36778e-003] ],

    [ [0,0,0,0,-4.28261e-002,2.59325e-002],
      [0,0,0,0,-3.49619e-002,1.43046e-002],
      [0,0,0,0,-2.57855e-002,1.17912e-002] ],

    [ [0,0,0,0,-5.91733e-002,3.25054e-002],
      [0,0,0,0,-5.06072e-002,1.79513e-002],
      [0,0,0,0,-3.69401e-002,1.48094e-002] ],

    [ [0,0,0,0,-8.26348e-002,4.05894e-002],
      [0,0,0,0,-7.40348e-002,2.24476e-002],
      [0,0,0,0,-5.34977e-002,1.85371e-002] ],

    [ [0,0,0,0,-1.17018e-001,5.08116e-002],
      [0,0,0,0,-1.09516e-001,2.81387e-002],
      [0,0,0,0,-7.85097e-002,2.32872e-002] ],

    [ [0,0,0,0,-1.67714e-001,6.37872e-002],
      [0,0,0,0,-1.63378e-001,3.53729e-002],
      [0,0,0,0,-1.16419e-001,2.93723e-002] ],

    [ [0,0,0,0,-2.42528e-001,7.98576e-002],
      [0,0,0,0,-2.45161e-001,4.43370e-002],
      [0,0,0,0,-1.73972e-001,3.70015e-002] ],

    [ [0,0,0,0,-3.53142e-001,9.96330e-002],
      [0,0,0,0,-3.69163e-001,5.53535e-002],
      [0,0,0,0,-2.61399e-001,4.65428e-002] ],

    [ [0,0,0,0,-5.16316e-001,1.24177e-001],
      [0,0,0,0,-5.55473e-001,6.89403e-002],
      [0,0,0,0,-3.93998e-001,5.86715e-002] ],

    [ [0,0,0,0,-7.56635e-001,1.55023e-001],
      [0,0,0,0,-8.34281e-001,8.58123e-002],
      [0,0,0,0,-5.94547e-001,7.43960e-002] ],

    [ [0,0,0,0,-1.10165e+000,1.91713e-001],
      [0,0,0,0,-1.23939e+000,1.05243e-001],
      [0,0,0,0,-8.91666e-001,9.40354e-002] ],

    [ [0,0,0,0,-1.58477e+000,2.39049e-001],
      [0,0,0,0,-1.80505e+000,1.28794e-001],
      [0,0,0,0,-1.32500e+000,1.21333e-001] ],

    [ [0,0,0,0,-2.50630e+000,1.42308e-001],
      [0,0,0,0,-2.19464e+000,2.76470e-001],
      [0,0,0,0,-1.90231e+000,1.47304e-001] ],
]

filterGain = [   
    [4.30764e-011,1,1],
    [8.59340e-011,1,1],
    [1.71424e-010,1,1],
    [3.41944e-010,1,1],
    [6.82035e-010,1,1],
    [1.36026e-009,1,1],
    [2.71261e-009,1,1],
    [5.40870e-009,1,1],
    [1.07826e-008,1,1],
    [2.14910e-008,1,1],
    [4.28228e-008,1,1],
    [8.54316e-008,1,1],
    [1.70009e-007,1,1],
    [3.38215e-007,1,1],
    [6.71990e-007,1,1],
    [1.33531e-006,1,1],
    [2.65172e-006,1,1],
    [5.25477e-006,1,1],
    [1.03780e-005,1,1],
    [2.04870e-005,1,1],
    [4.05198e-005,1,1],
    [7.97914e-005,1,1],
    [1.56511e-004,1,1],
    [3.04954e-004,1,1],
    [5.99157e-004,1,1],
    [1.16544e-003,1,1],
    [2.27488e-003,1,1],
    [3.91006e-003,1,1] 
]

class Loudness_ISO532_1:
    class Filtering:
        # 1차 low-pass filter
        @staticmethod
        def f_lowpass(pInput, pOutput, tau, sampleRate, numSamples):
            A1 = math.exp(-1 / (tau * sampleRate))
            B0 = 1 - A1
            Y1 = 0

            iX = 0
            iY = 0

            for time in range(numSamples):
                pOutput[iY] = B0 * pInput[iX] + A1 * Y1
                Y1 = pOutput[iY]
                iX += 1
                iY += 1

        # 2차 filter
        @staticmethod
        def f_filter_2ndOrder(pInput, pOutput, coeffs, numSamples, gain):
            iX = 0
            iY = 0
            Wn0 = 0
            Wn1 = 0
            Wn2 = 0

            for time in range(numSamples):
                Wn0 = pInput[iX] * gain - coeffs[4] * Wn1 - coeffs[5] * Wn2
                pOutput[iY] = coeffs[0] * Wn0 + coeffs[1] * Wn1 + coeffs[2] * Wn2
                Wn2 = Wn1
                Wn1 = Wn0
                iX += 1
                iY += 1
        
        # lowpass 1차 필터를 3번 사용해 Squaring, Smoothing
        @staticmethod
        def f_square_and_smooth(pInput, centerFrequency, sampleRate, numSamples, method, timeSkip):
            iX = 0

            if method == LoudnessMethodTimeVarying:
                if centerFrequency <= 1000:
                    tau = 2 / (3 * centerFrequency)
                else:
                    tau = 2 / (3 * 1000)

                for time in range(numSamples):
                    pInput[iX] = math.pow(pInput[iX], 2)
                    iX += 1
                
                for i in range(3):
                    Loudness_ISO532_1 \
                        .Filtering \
                        .f_lowpass(
                            pInput, pInput, tau, sampleRate, numSamples
                        )
            else:
                out = 0
                numSkip = int(math.floor(timeSkip * sampleRate))
                if numSkip >= numSamples:
                    return LoudnessErrorSignalTooShort

                iX += numSkip
                for time in range(numSkip, numSamples):
                    out += math.pow(pInput[iX], 2)
                    iX += 1

                pInput[iX] = out / (numSamples - numSkip)
            
            return 0

        # 3차 filtering, squaring, smoothing, level calculation & downsampling by decFactor to SR_LEVEL
        @staticmethod
        def f_calc_third_octave_levels(pSignal: InputData, thirdOctaveLevel, decFactor, method, timeSkip):
            coeffs = [0.0 for _ in range(N_FILTER_COEFS)]
            gain = 0.0
            
            numSamples = pSignal.numSamples
            numDecSamples = numSamples / decFactor

            pOutput = [0.0 for _ in range(numSamples)]

            for i in range(N_LEVEL_BANDS):
                for j in range(N_FILTER_STAGES):
                    for k in range(N_FILTER_COEFS):
                        coeffs[k] = thirdOctaveFilterRef[j][k] - thirdOctaveFilters[i][j][k]
                    gain = filterGain[i][j]

                    Loudness_ISO532_1 \
                        .Filtering \
                        .f_filter_2ndOrder(
                            pSignal.pData, pOutput, coeffs, numSamples, gain
                        )
                    
                    pSignal.pData = pOutput
                
                centerFrequency = math.pow(10, (i - 16) / 10) * 1000
                err = Loudness_ISO532_1 \
                    .Filtering \
                    .f_square_and_smooth(
                        pOutput, centerFrequency, pSignal.sampleRate, numSamples, method, timeSkip
                    )

                if err < 0:
                    return err

                iO = i
                iX = 0

                for time in range(numDecSamples):
                    thirdOctaveLevel[iO] = 10 * math.log10((pSignal.pData[iX] + TINY_VALUE) / I_REF)        
                    iX += decFactor
                    iO += 1
                
            return 0

    class TemporalWeighting:
        @staticmethod
        def f_lowpass_intp(pInput, pOutput, tau, sampleRate, numSamples):
            iX = 0
            iY = 0

            A1 = math.exp(-1 / (tau * sampleRate * LP_ITER))
            B0 = 1 - A1
            Y1 = 0

            for time in range(numSamples):
                X0 = pInput[iX]
                iX += 1

                Y1 = B0 * X0 + A1 * Y1
                pOutput[iY] = Y1
                iY += 1

                if time < numSamples - 1:
                    Xd = (pInput[iX] - X0) / LP_ITER
                
                    for i in range(1, LP_ITER):
                        X0 += Xd
                        Y1 = B0 * X0 + A1 * Y1
            
            return pOutput

        @staticmethod
        def f_temporal_weight_loudness(loudness, sampleRate, numSamples):
            iL = 0
            iL1 = 0
            iL2 = 0

            pLoudness_t1 = [0.0 for _ in range(numSamples)]
            pLoudness_t2 = [0.0 for _ in range(numSamples)]

            tau = 3.5e-3
            Loudness_ISO532_1 \
                .TemporalWeighting \
                .f_lowpass_intp(
                    loudness, pLoudness_t1, tau, sampleRate, numSamples
                )
            
            tau = 70e-3
            Loudness_ISO532_1 \
                .TemporalWeighting \
                .f_lowpass_intp(
                    loudness, pLoudness_t2, tau, sampleRate, numSamples
                )
            
            for time in range(numSamples):
                loudness[iL] = 0.47 * pLoudness_t1[iL1] + 0.53 * pLoudness_t2[iL2]
                iL += 1
                iL1 += 1
                iL2 += 1

            return 0

    class LoudnessCalculation:
        RAP = [45., 55., 65., 71., 80., 90., 100., 120.]
        DLL = [  
            [-32.,-24.,-16.,-10.,-5.,0.,-7.,-3.,0.,-2.,0.],
            [-29.,-22.,-15.,-10.,-4.,0.,-7.,-2.,0.,-2.,0.],
            [-27.,-19.,-14., -9.,-4.,0.,-6.,-2.,0.,-2.,0.],
            [-25.,-17.,-12., -9.,-3.,0.,-5.,-2.,0.,-2.,0.],
            [-23.,-16.,-11., -7.,-3.,0.,-4.,-1.,0.,-1.,0.],
            [-20.,-14.,-10., -6.,-3.,0.,-4.,-1.,0.,-1.,0.],
            [-18.,-12., -9., -6.,-2.,0.,-3.,-1.,0.,-1.,0.],
            [-15.,-10., -8., -4.,-2.,0.,-3.,-1.,0.,-1.,0.]
        ]
        LTQ = [30.,18.,12.,8.,7.,6.,5.,4.,3.,3.,3.,3.,3.,3.,3.,3.,3.,3.,3.,3.]
        A0 = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,-0.5,-1.6,-3.2,-5.4,-5.6,-4.0,-1.5,2.0,5.0,12.0]
        DDF = [0.0, 0.0, 0.5, 0.9, 1.2, 1.6, 2.3, 2.8, 3.0, 2.0, 0.0,-1.4,-2.0,-1.9,-1.0, 0.5,3.0, 4.0, 4.3, 4.0]
        DCB = [-.25,-0.6,-0.8,-0.8,-0.5,0.0,0.5,1.1,1.5,1.7,1.8,1.8,1.7,1.6,1.4,1.2,0.8,0.5,0.0,-0.5]
        ZUP = [0.9,1.8,2.8,3.5,4.4,5.4,6.6,7.9,9.2,10.6,12.3,13.8,15.2,16.7,18.1,19.3,20.6,21.8,22.7,23.6,24.0]
        RNS = [21.5,18.0,15.1,11.5,9.0,6.1,4.4,3.1,2.13,1.36,0.82,0.42,0.30,0.22,0.15,0.10,0.035,0.0]
        USL = [   
            [ 13.00,8.20,6.30,5.50,5.50,5.50,5.50,5.50],
            [ 9.00,7.50,6.00,5.10,4.50,4.50,4.50,4.50],
            [ 7.80,6.70,5.60,4.90,4.40,3.90,3.90,3.90],
            [ 6.20,5.40,4.60,4.00,3.50,3.20,3.20,3.20],
            [ 4.50,3.80,3.60,3.20,2.90,2.70,2.70,2.70],
            [ 3.70,3.00,2.80,2.35,2.20,2.20,2.20,2.20],
            [ 2.90,2.30,2.10,1.90,1.80,1.70,1.70,1.70],
            [ 2.40,1.70,1.50,1.35,1.30,1.30,1.30,1.30],
            [ 1.95,1.45,1.30,1.15,1.10,1.10,1.10,1.10],
            [ 1.50,1.20,0.94,0.86,0.82,0.82,0.82,0.82],
            [ 0.72,0.67,0.64,0.63,0.62,0.62,0.62,0.62],
            [ 0.59,0.53,0.51,0.50,0.42,0.42,0.42,0.42],
            [ 0.40,0.33,0.26,0.24,0.22,0.22,0.22,0.22],
            [ 0.27,0.21,0.20,0.18,0.17,0.17,0.17,0.17],
            [ 0.16,0.15,0.14,0.12,0.11,0.11,0.11,0.11],
            [ 0.12,0.11,0.10,0.08,0.08,0.08,0.08,0.08],
            [ 0.09,0.08,0.07,0.06,0.06,0.06,0.06,0.05],
            [ 0.06,0.05,0.03,0.02,0.02,0.02,0.02,0.02] 
        ]

        @staticmethod
        def f_corr_third_octave_intensities(thirdOctaveLevel, thirdOctaveIntens, idxTime):
            for i in range(N_LCB_BANDS):
                idxLevelRange = 0
                while thirdOctaveLevel[i][idxTime] > ( \
                    Loudness_ISO532_1.LoudnessCalculation.RAP[idxLevelRange] - Loudness_ISO532_1.LoudnessCalculation.DLL[idxLevelRange][i] \
                    ) and idxLevelRange < N_RAP_RANGES - 1:
                    idxLevelRange += 1
                corrLevel = thirdOctaveLevel[i][idxTime] + Loudness_ISO532_1.LoudnessCalculation.DLL[idxLevelRange][i]
                thirdOctaveIntens[i][idxTime] = math.pow(10., corrLevel / 10)

        @staticmethod
        def f_calc_lcbs(thirdOctaveIntens, lcb, idxTime):
            pcbi = lcb[0]
            pIntens = thirdOctaveIntens[0]
            pcbi[idxTime] = pIntens[idxTime]

            for i in range(1, 6):
                pIntens = thirdOctaveIntens[i]
                pcbi[idxTime] += pIntens[idxTime]

            pcbi = lcb[1]
            pIntens = thirdOctaveIntens[6]
            pcbi[idxTime] = pIntens[idxTime]

            for i in range(7, 9):
                pIntens = thirdOctaveIntens[i]
                pcbi[idxTime] += pIntens[idxTime]

            pcbi = lcb[2]
            pIntens = thirdOctaveIntens[9]
            pcbi[idxTime] = pIntens[idxTime]

            for i in range(10, N_LCB_BANDS):
                pIntens = thirdOctaveIntens[i]
                pcbi[idxTime] += pIntens[idxTime]

            for i in range(N_LCBS):
                pcbi = lcb[i]
                if pcbi[idxTime] > 0.:
                    pcbi[idxTime] = 10 * math.log10(pcbi[idxTime])

        @staticmethod
        def f_calc_core_loudness(ThirdOctaveLevel, Lcb, CoreLoudness, SoundField, IdxTime):
            
            pLtqIdx = 0
            pLtq = Loudness_ISO532_1.LoudnessCalculation.LTQ

            for IdxCL in range(N_CORE_LOUDN - 1):
                if(IdxCL < N_LCBS):
                    pLe = Lcb[IdxCL] 
                else:
                    pLe = ThirdOctaveLevel[IdxCL + 8]
                pCoreL = CoreLoudness[IdxCL]

                pLe[IdxTime] -= Loudness_ISO532_1.LoudnessCalculation.A0[IdxCL]
                pCoreL[IdxTime] = 0.

                if(SoundField == SoundFieldDiffuse):
                    pLe[IdxTime] += Loudness_ISO532_1.LoudnessCalculation.DDF[IdxCL]
                
                if(pLe[IdxTime] > pLtq[pLtqIdx]):
                    pLe[IdxTime] += -Loudness_ISO532_1.LoudnessCalculation.DCB[IdxCL]
                    S = .25
                    MP1 = .0635 * (10. ** (0.025 * (pLtq[pLtqIdx])))
                    MP2 = ((1. - S + S * (10. ** (0.1 * (pLe[IdxTime] - pLtq[pLtqIdx])))) ** .25) - 1.0
                    pCoreL[IdxTime] = MP1 * MP2
                    if(pCoreL[IdxTime] <= 0.):
                        pCoreL = 0.
                pLtqIdx += 1
            
            #Set last Critical band to zero
            pCoreL = CoreLoudness[N_CORE_LOUDN - 1]
            pCoreL[IdxTime] = 0.

        @staticmethod
        def f_corr_loudness(CoreLoudness, IdxTime):
            pCoreLoudness = CoreLoudness[0]
            CorrCL = 0.4 + 0.32 * (pCoreLoudness[IdxTime] ** .2)
            if(CorrCL < 1.):
                pCoreLoudness[IdxTime] *= CorrCL

        @staticmethod
        def f_calc_slopes(CoreLoudness, Loudness, SpecLoudness, IdxTime):
            IdxCL = None; IdxNS = None; IdxCBN = None; IdxRNS = None #short
            NextCriticalBand = None #int
            N1 = None; N2 = None; Z = None; Z1 = None; Z2 = None; ZK = None; DZ = None #double
            _USL = None; _ZUP = None; CoreL = None # double
            pLoudness = Loudness; pCoreL = None
            NS = [None for _ in range(N_BARK_BANDS)]

            N1          = 0.
            Z           = 0.1
            Z1          = 0.
            IdxRNS      = 0
            IdxNS       = 0
            pLoudness[IdxTime] = 0

            for IdxCL in range(N_CORE_LOUDN):
                pCoreL = CoreLoudness[IdxCL]
                CoreL = pCoreL[IdxTime]
                _ZUP = Loudness_ISO532_1.LoudnessCalculation.ZUP[IdxCL]
                _ZUP += .0001
                IdxCBN = IdxCL - 1
                if(IdxCBN > N_CB_RANGES - 1):
                    IdxCBN = N_CB_RANGES - 1
                NextCriticalBand = 0
                while True:
                    print(N1, end = ' ')
                    print(N2, end = ' ')
                    print(CoreL, end = ' ')
                    print(_USL, end = ' ')
                    print(IdxRNS)
                    time.sleep(1)
                    if(N1 > CoreL):
                        _USL = Loudness_ISO532_1.LoudnessCalculation.USL[IdxRNS][IdxCBN]
                        N2 = Loudness_ISO532_1.LoudnessCalculation.RNS[IdxRNS]
                        
                        if(N2 < CoreL):
                            N2 = CoreL
                        DZ = (N1 - N2) / _USL
                        Z2 = Z1 + DZ
                        if(Z2 > _ZUP):
                            NextCriticalBand = 1
                            Z2 = _ZUP
                            DZ = Z2 - Z1
                            N2 = N1 - DZ * _USL
                        pLoudness[IdxTime] += DZ * (N1 + N2) / 2.

                        ZK = Z
                        while(ZK <= Z2):
                            NS[IdxNS] = N1 - (ZK - Z1) * _USL
                            SpecLoudness[IdxNS][IdxTime] = NS[IdxNS]
                            IdxNS += 1
                            ZK += 0.1
                        Z = ZK
                    else:
                        if(N1 < CoreL):
                            IdxRNS = 0
                            while((IdxRNS < N_RNS_RANGES) and Loudness_ISO532_1.LoudnessCalculation.RNS[IdxRNS] >= CoreL):
                                IdxRNS += 1
                        NextCriticalBand = 1
                        Z2 = _ZUP
                        N2 = CoreL
                        pLoudness[IdxTime] += N2 * (Z2 - Z1)
                        ZK = Z
                        while(ZK <= Z2):
                            NS[IdxNS] = N2
                            SpecLoudness[IdxNS][IdxTime] = NS[IdxNS]
                            IdxNS += 1
                            ZK = ZK + 0.1
                        Z = ZK
                    
                    while((N2 <= Loudness_ISO532_1.LoudnessCalculation.RNS[IdxRNS]) and (IdxRNS < N_RNS_RANGES - 1)):
                        IdxRNS += 1
                    if(IdxRNS > N_RNS_RANGES - 1):
                        IdxRNS = N_RNS_RANGES - 1
                    Z1 = Z2
                    N1 = N2
                    if(NextCriticalBand):
                        break
            if(pLoudness[IdxTime] < 0.):
                pLoudness[IdxTime] = 0        

        @staticmethod
        def f_loudness_from_levels(ThirdOctaveLevel, NumSamplesLevel, SoundField, Method, OutLoudness, OutSpecLoudness):
            CoreLoudness = [[0 for _ in range(NumSamplesLevel)] for _ in range(N_CORE_LOUDN)]
            ThirdOctaveIntens = [[0 for _ in range(NumSamplesLevel)] for _ in range(N_LCB_BANDS)]
            Lcb = [[0 for _ in range(NumSamplesLevel)] for _ in range(N_LCBS)]

            IdxTime = None
            SampleRateLevel = None
            retval = None

            SampleRateLevel = SR_LEVEL

            #Calculate core Loudness
            for IdxTime in range(NumSamplesLevel):
                Loudness_ISO532_1.LoudnessCalculation.f_corr_third_octave_intensities(ThirdOctaveLevel, ThirdOctaveIntens, IdxTime)
                Loudness_ISO532_1.LoudnessCalculation.f_calc_lcbs(ThirdOctaveIntens, Lcb, IdxTime)
                Loudness_ISO532_1.LoudnessCalculation.f_calc_core_loudness(ThirdOctaveLevel, Lcb, CoreLoudness, SoundField, IdxTime)
            
            #Correction of specific loudness within lowest critical band
            for IdxTime in range(NumSamplesLevel):
                Loudness_ISO532_1.LoudnessCalculation.f_corr_loudness(CoreLoudness, IdxTime)
            
            #Time-varying loudness: nonlinearity
            if (Method == LoudnessMethodTimeVarying):
                f_nl(CoreLoudness, SampleRateLevel, NumSamplesLevel)
            for i in range(len(CoreLoudness)):
                print(CoreLoudness[i])
            #Calculation of sepcific loudness
            for IdxTime in range(NumSamplesLevel):
                Loudness_ISO532_1.LoudnessCalculation.f_calc_slopes(CoreLoudness, OutLoudness, OutSpecLoudness, IdxTime)
            
            #Time-carying loudness: temporal weighting
            if (Method == LoudnessMethodTimeVarying):
                retval = Loudness_ISO532_1.TemporalWeighting.f_temporal_weight_loudness(OutLoudness, SampleRateLevel, NumSamplesLevel)
                if(retval < 0):
                    return retval
            
            return NumSamplesLevel
        
        @staticmethod
        def f_loudness_from_signal(pSignal : InputData, SoundField, Method, TimeSkip, OutLoudness, OutSpecLoudness, SizeOutput):
            ThirdOctaveLevel = [[0 for _ in NumSamplesLevel] for _ in range(N_LEVEL_BANDS)]
            SampleRateLevel = 1
            DecRactorLevel = 1
            NumSamplesTime = 1
            NumSamplesLevel = 1

            retval = None

            if (Method == LoudnessMethodStationary):
                DecFactorLevel = (int)(pSignal.NumSamples)
            elif (Method == LoudnessMethodTimeVarying):
                SampleRateLevel = SR_LEVEL

                DecFactorLevel = (int)(pSignal.SampleRate / SampleRateLevel)

                NumSamplesTime = pSignal.NumSamples
                NumSamplesLevel = NumSamplesTime / DecFactorLevel
            else:
                return LoudnessErrorUnsupportedMethod
            
            if (SizeOutput < NumSamplesLevel):
                return LoudnessErrorOutputVectorTooSmall
            
            #Calculate third octave levels
            retval = Loudness_ISO532_1.Filtering.f_calc_third_octave_levels(pSignal, ThirdOctaveLevel, DecFactorLevel, Method, TimeSkip)
            if(retval < 0):
                return retval
            
            retval = Loudness_ISO532_1.LoudnessCalculation.f_loudness_from_levels(ThirdOctaveLevel, NumSamplesLevel, SoundField, Method, OutLoudness, OutSpecLoudness)

            return retval
