from modules.loudness import *
from modules.roughness import *
from modules.sharpness import *
import sys
import csv
import copy
import os.path

def error_with_message(message):
    print(message)
    exit(1)

class fileWrite:
    def __init__(self, filename, analysis, cal):
        self.filename = filename
        self.analysis = analysis
        self.UNIT = {"Loudness": "soneGF", "Roughness": "asper",\
        "Sharpness": "acum", "Fluctuation Strength": "vacil", "Tonality": "tu"}
        self.cal = cal


    def find(self, path, csvname):
        if not os.path.exists(path + '/' + csvname + '.csv'):
            return csvname
        index = 1
        while True:
            if(index == 100):
                error_with_message("[Error] Too many files")
            next_check = csvname + f'({index})'
            if not os.path.exists(path + '/' + next_check + '.csv'):
                return next_check
            index += 1
    
    def calculation(self, dir):
        if(self.analysis == 'Loudness'):
            LN = Loudness(dir, self.cal)
            return [LN.value(), []]
        
        if(self.analysis == 'Sharpness'):
            SN = Sharpness(dir, self.cal)
            return [SN.value(), []]

        
        if(self.analysis == 'Roughness'):
            RN = Roughness(dir, self.cal)
            return [RN.value(), []]

        #Match the corresponding function with if-else
        return [0, []] 

    def write_result(self, dir, path, csvname):
        csvname_numbered = self.find(path, csvname) + ".csv"
        if not os.path.exists(path):
            os.makedirs(path)
        csvfile = open(path + '/' + csvname_numbered, 'w',  newline='')
        wr = csv.writer(csvfile)
        wr.writerow(["Filename: ", self.filename])
        wr.writerow(["Analysis: ", self.analysis + " vs. Time"])
        wr.writerow(["Abscissa 1: ", "s"])
        wr.writerow(["Channel 1: ", self.analysis, self.UNIT[self.analysis]])
        result = self.calculation(self.filename)
        wr.writerow(["Value: ", result[0]])
        wr.writerow("")
        for value in result[1]:
            wr.writerow([value[0], value[1]])

def main(filepath, cal):
    filenames = os.listdir(path = filepath)
    factors = ['Loudness', 'Sharpness', 'Roughness']
    for filename in filenames:
        for fac in factors:
            fw = fileWrite(filepath + '/' + filename, fac, cal)
            fw.write_result(filepath, f"results/{filename[:-4]}", f"{filename[:-4]}-{fac}")

#py main.py path cal
main(sys.argv[1], int(sys.argv[2])) 
