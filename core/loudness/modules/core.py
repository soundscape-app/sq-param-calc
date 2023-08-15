# Loudness Method
LoudnessMethodStationary = 0
LoudnessMethodTimeVarying = 1

# Sound Field Type
SoundFieldFree = 0
SoundFieldDiffuse = 1

# Error Codes
LoudnessErrorOutputVectorTooSmall = -1
# LoudnessErrorMemoryAllocFailed = -2
LoudnessErrorUnsupportedMethod = -3
LoudnessErrorSignalTooShort = -4

# Input Data Class
class InputData:
    def __init__(self):
        self.numSamples = 0
        self.sampleRate = 0
        self.pData = None

# Constants
I_REF = 4e-10
SR_LEVEL = 2000
N_LEVEL_BANDS = 28
N_BARK_BANDS = 240  

PCM = 1
IEEE_FLOAT = 3
MAX_BUF_SIZE = 256