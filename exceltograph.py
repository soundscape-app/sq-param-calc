import sys
import csv
import copy
import os.path
import matplotlib.pyplot as plt

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

def main(filepath):
    csv = Csvfile(filepath)
    csv.to_graph()

main(sys.argv[1])
