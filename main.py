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
            return [LN.value(), LN.timeseg()]
        
        if(self.analysis == 'Sharpness'):
            SN = Sharpness(dir, self.cal)
            return [SN.value(), SN.timeseg()]

        if(self.analysis == 'Roughness'):
            RN = Roughness(dir, self.cal)
            return [RN.value(), RN.timeseg()]

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
        for i in range(6, 19):
            wr.writerow("")
        wr.writerow(["0;0"])
        for i in range(0, len(result[1][0])):
            wr.writerow([(str)(result[1][0][i]) + ';' + (str)(result[1][1][i])])

class Csvfile:
    def __init__(self, filename):
        self.filename = filename
    
    def to_graph(self):
        file = open(self.filename, 'r', encoding='utf-8')
        rdr = csv.reader(file)
        total = []
        for line in rdr:
            total.append(line)
        x = []
        y = []
        for(i, line) in enumerate(total):
            if(i < 19):
                continue
            newx, newy = line[0].split(';')
            x.append(float(newx))
            y.append(float(newy))
        plt.plot(x, y)
        plt.savefig(f'{self.filename}.png')
        plt.clf()

def main(filepath):
    cal = 1
    #using DFS
    filenames = os.listdir(path = filepath)
    resultFile = ['results']
    factors = ['Loudness', 'Sharpness', 'Roughness']
    RealFileStack = [[filepath]]
    ResultFileStack = [resultFile]
    while len(RealFileStack):
        RealFileTop = RealFileStack.pop()
        ResultFileTop = ResultFileStack.pop()
        if(os.path.isdir(''.join(RealFileTop))):
            new_filenames = os.listdir(''.join(RealFileTop))
            for fn in new_filenames:
                RealFileStack += [RealFileTop + ['/' + fn]]
                ResultFileStack += [ResultFileTop + ['/' + fn]]
        else:
            for fac in factors:
                fw = fileWrite(''.join(RealFileTop), fac, cal)
                fw.write_result(''.join(RealFileTop), f"{(''.join(ResultFileTop))[:-4]}", f"{fac}")
                csv = Csvfile(f"{(''.join(ResultFileTop))[:-4]}/{fac}.csv")
                csv.to_graph()

#py main.py path cal
main(sys.argv[1])
