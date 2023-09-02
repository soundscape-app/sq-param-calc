import math

dz = 0.1
class Roughness:
    @staticmethod
    def acousticRoughness(specificLoudness, fmod = 70):
        specificLoudnessdiff = [0 for _ in range(len(specificLoudness))]
        for i in range(len(specificLoudness)):
            if (i == 0):
                specificLoudnessdiff[i] = specificLoudness[i][0]
            else:
                specificLoudnessdiff[i] = abs(specificLoudness[i][0] - specificLoudness[i-1][0])
        R = 0.3 * (fmod/1000) * dz * sum(specificLoudnessdiff)
        
        return R
                    