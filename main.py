from core.loudness.modules.loudness_ISO532_1_main import *
import sys
import os
import csv
import copy

files = os.listdir(f"./{sys.argv[3]}")
file_dir = sys.argv[3]
pFileName = "Result.csv"
pfile = open(pFileName, "w")
wr = csv.writer(pfile)
wr.writerow(["filename", "N / Nmax", "LN / N"])
for f in files:
    sys.argv[3] = f"./{file_dir}/{f}"
    to_write = loudness_main(sys.argv)
    wr.writerow([f, to_write[0], to_write[1]])
pfile.close()