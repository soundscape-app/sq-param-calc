import math
class Sharpness:
    @staticmethod
    def float_range(start, end, jump):
        arr = []
        i = start
        while(i < end):
            arr.append(i)
            i += jump
        return arr

    @staticmethod
    def calc_sharpness(loudness, specificLoudness):
        loudness = float(loudness)
        if(loudness == 0):
            loudness = 1e-8
        n = len(specificLoudness)

        gz_Z = [1 for _ in range(n)]
        for z in range(158, n):
            gz_Z[z] = 0.15 * math.e ** (0.42 * ((z + 1) / 10 - 15.8)) + 0.85
        suma = 0
        for i, z in enumerate(Sharpness.float_range(0.1, n / 10 + 0.1, 0.1)):
            suma += specificLoudness[i][0] * gz_Z[i] * round(z, 1) * 0.1
        sharpnessZwicker = 0.11 * suma / loudness

        gz_VB = [1 for _ in range(n)]
        for z in range(150, n):
            gz_VB[z] = 0.2 * math.e ** (0.308 * ((z + 1) / 10 - 15)) + 0.8
        suma = 0
        for i, z in enumerate(Sharpness.float_range(0.1, n/10 + 0.1, 0.1)):
            suma += specificLoudness[i][0] * gz_VB[i] * round(z, 1) * 0.1
        sharpnessVonBismarck = 0.11 * suma / loudness

        gz_VB = [1 for _ in range(n)]
        for z in range(0, n):
            zi = (float)(z + 1) / (float)(10)
            gz_VB[z] = (0.078 * math.e ** (0.171 * (zi)) / zi) * loudness / math.log(0.05 * loudness + 1)
        suma = 0
        for i, z in enumerate(Sharpness.float_range(0.1, n/10 + 0.1, 0.1)):
            suma += specificLoudness[i][0] * gz_VB[i] * round(z, 1) * 0.1
        sharpnessAures = 0.11 * suma / loudness

        return round(sharpnessZwicker, 2), round(sharpnessVonBismarck, 2), round(sharpnessAures, 2)