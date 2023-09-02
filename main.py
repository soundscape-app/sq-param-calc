from core.loudness.modules.loudness_ISO532_1_main import *
from core.roughness.roughness import *
from core.sharpness.sharpness import *
import sys
import os
import csv
import copy

files = os.listdir(f"./{sys.argv[3]}")
file_dir = sys.argv[3]
pFileName = "Result.csv"
pfile = open(pFileName, "w", newline="")
wr = csv.writer(pfile)  
first_row = ["filename", "Loudness level", "Loudness", "Roughness", "Sharpness(Zwicker Method)"]
wr.writerow(first_row)
for f in files:
    sys.argv[3] = f"./{file_dir}/{f}"
    to_write = loudness_main(sys.argv)
    specLoudness = to_write[2]
    roughness = Roughness.acousticRoughness(specLoudness)
    sharpness = Sharpness.calc_sharpness(to_write[0], specLoudness)
    wr.writerow([f, to_write[0], to_write[1], roughness, sharpness[0]])
pfile.close()