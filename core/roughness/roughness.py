import math

class Roughness:
    def __init__():
        dz = 0.1
    
    @staticmethod
    def acousticRoughness(specificLoudness, fmod = 70):
        specificLoudnessdiff = [0 for _ in range(specificLoudness)]
        for i in range(specificLoudness):
            if (i == 0):
                specificLoudnessdiff[i] = specificLoudness[i]
            else:
                specificLoudnessdiff[i] = abs(specificLoudness[i] - specificLoudness[i-1])
        R = 0.3 * (fmod/1000) * sum(Roughness.dz * specificLoudnessdiff)
        
        return R
                    