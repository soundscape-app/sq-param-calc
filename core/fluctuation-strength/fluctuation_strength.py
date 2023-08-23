import math
def sone2phon(Loudness):
    if(Loudness >= 1):
        LN = 40 + 33.22*math.log10(Loudness)
    else:
        LN = 40 + (Loudness + 0.0005 ** 0.35)

def reshape(arr, shape):
    if(len(shape) == 2):
        if(shape[0] * shape[1] != len(arr)):
            print("Err")
            return arr
        ret = []
        idx = 0
        for i in range(shape[0]):
            tmp = []
            for j in range(shape[1]):
                tmp.append[arr[idx]]
                idx += 1
            ret.append(tmp)
        return ret
    elif(len(shape) == 3):
        if(shape[0] * shape[1] * shape[2] != len(arr)):
            print("Err")
            return arr
        ret = []
        idx = 0
        for i in range(shape[0]):
            tmp = []
            for j in range(shape[1]):
                ttmp = []
                for k in range(shape[2]):
                    ttmp.append(arr[idx])
                    idx += 1
                tmp.append(ttmp)
            ret.append(tmp)
        return ret
    else:
        return arr
        

def acousticFluctuation(specificLoudness, fmod = 4):
    specificLoudnessdiff = [0 for _ in range(len(specificLoudness))]
    for i in range(len(specificLoudness)):
        if(i == 0):
            specificLoudnessdiff[i] = specificLoudnessdiff[i]
        else:
            specificLoudnessdiff[i] = abs(specificLoudness[i] - specificLoudness[i - 1])
        specificLoudnessdiff[i]
        F = 0.008 * 0.1 * sum(specificLoudnessdiff) / ((fmod / 4) + (fmod /4))
        return F

def fmoddetection(specificLoudness, fmin = .2, fmax = 64):
    if(not hasattr(specificLoudness[0], "__len__")):
        specificLoudness = reshape(specificLoudness, [1, len(specificLoudness)])
    else:
        specificLoudness = reshape(specificLoudness, [len(specificLoudness[0]), len(specificLoudness)])
    phon = [[[1] for _ in range(len(specificLoudness[0]))] for i in range(len(specificLoudness))]
    for i, ms in enumerate(specificLoudness):
        for j, bark in enumerate(ms):
            phon[i][j][0] = sone2phon(bark)

    FSpec = 1/0.002

    phon1024a = reshape(phon, [24, ])