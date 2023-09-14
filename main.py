from core.loudness.modules.loudness_ISO532_1_main import *
from core.roughness.roughness import *
from core.sharpness.sharpness import *
from core.fluctuation_strength.fluctuation_strength import *
import sys
import csv
import copy
import os.path

def error_with_message(message):
    print(message)
    exit(1)

class fileWrite:
    def __init__(self, filename, analysis):
        self.filename = filename
        self.analysis = analysis
        self.UNIT = {"Loudness": "soneGF", "Roughness": "asper",\
        "Sharpness": "acum", "Fluctuation Strength": "vacil", "Tonality": "tu"}


    def find(path, csvname):
        if not os.path.exists(path + '/' + csvname):
            return csvname
        index = 1
        while True:
            if(index == 100):
                error_with_message("[Error] Too many files")
            next_check = csvname + f'({index})'
            if not os.path.exists(path + '/' + next_check):
                return next_check
    
    def calculation(self):
        #Match the corresponding function with if-else
        return [0, [(0, 0), (1, 1)]] 

    def write_result(self, path, csvname):
        csvname_numbered = find(path, csvname)
        csvfile = open(path + '/' + csvname_numbered, 'w')
        writer = csv.writer(csvfile)
        wr.writerow(["Filename: ", self.filename])
        wr.writerow(["Analysis: ", self.analysis + " vs. Time"])
        wr.writerow(["Abscissa 1: ", "s"])
        wr.writerow(["Channel 1: ", self.analysis, self.UNIT[self.analysis]])
        result = calculation()
        wr.writerow(["Value: ", result[0]])
        wr.writerow()
        for value in result[1]:
            wr.writerow([value[0], value[1]])
