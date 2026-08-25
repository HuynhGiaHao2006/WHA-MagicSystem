import tkinter as tk
import math
import time
import itertools
from scipy.spatial.distance import cdist
from recognizer import Parser, resample, reposition_and_resize, Scorer
from templates_visualizer import visualize


def groupStrokes(current_groups, inputStroke, type = 'signs', threshold = 25):
    # Group new stroke with existing groups
    groups_list = [group for group in current_groups]
    if not groups_list:
        symbol, score = Parser([inputStroke], 64, type)
        # score = Scorer(new_group_strokes, new_group_symbol)
        groups_list.append(([inputStroke], symbol, score))
        return groups_list

    updated_groups_list = []
    new_group_strokes = [inputStroke]
    for group in groups_list:
        min_dist = cdist(inputStroke, list(itertools.chain.from_iterable(group[0]))).min()
        if min_dist < threshold:
            new_group_strokes += group[0]
            continue
        else: updated_groups_list.append(group)
    new_group_symbol, new_group_score = Parser(new_group_strokes, 64, type)
    # new_group_score = Scorer(new_group_strokes, new_group_symbol)
    updated_groups_list.append((new_group_strokes, new_group_symbol, new_group_score))
    return updated_groups_list

class Quire(tk.Frame):

    def __init__(self, master = None):
        super().__init__(master)
        self.states = [{'signGroups': [], # List of sign groups in the form of a tuple of strokes coords [0], symbol [1] and score [2]
                        'sigilGroups': [], # List of sigil groups 
                        }]
        self.currentStrokeCoords = []
        self.strokes = []
        self.labels = []


        self.brushSize = 5
        self.last_x = 0
        self.last_y = 0

        self.canvas = tk.Canvas(self, width=800, height=600, bg = 'beige')
        self.canvas.bind('<Button-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<ButtonRelease-1>', self.release)
        self.canvas.focus_set()
        self.canvas.bind('<z>', self.undo)
        self.canvas.bind('<c>', self.clear)
        self.canvas.pack()

    def press(self, event):
        self.canvas.create_line(event.x, event.y, event.x, event.y, width = self.brushSize,
                                                 fill = 'black', smooth = True, splinesteps = 5, capstyle = 'round')
        self.last_x = event.x
        self.last_y = event.y
        self.currentStrokeCoords.append((event.x, event.y))

    def drag(self, event):
        self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, width = self.brushSize,
                                 fill = 'black', smooth = True, splinesteps = 5, capstyle = 'round')
        self.last_x = event.x
        self.last_y = event.y
        self.currentStrokeCoords.append((event.x, event.y))

    def release(self, event):
        self.currentStrokeCoords.append((event.x, event.y))
        self.strokes.append(self.currentStrokeCoords)
        self.currentStrokeCoords = []


        stroke_length = 0
        prev_coords = self.strokes[-1][0]
        for coords in self.strokes[-1][1:]:
            stroke_length += math.sqrt((coords[0] - prev_coords[0])**2 + (coords[1] - prev_coords[1])**2)
            prev_coords = coords
        if stroke_length < 10: # Set a limit to how short a stroke can be
            self.canvas.delete('all')
            self.coordinates = []
            self.strokes.pop()
            for stroke in self.strokes:
                for i in range(len(stroke) - 1):
                    self.canvas.create_line(stroke[i][0], stroke[i][1], stroke[i + 1][0], stroke[i + 1][1], width = self.brushSize,
                                                fill = 'black', smooth = True, splinesteps = 5, capstyle = 'round')
                    self.coordinates.append((stroke[i][0], stroke[i][1]))
                self.coordinates.append((stroke[-1][0], stroke[-1][1]))
            self.label()
        else:
            new_signGroups = groupStrokes(self.states[-1]['signGroups'], self.strokes[-1])
            new_sigilGroups = groupStrokes(self.states[-1]['sigilGroups'], self.strokes[-1], 'sigils', 40)
            new_state = {'signGroups': new_signGroups, 'sigilGroups': new_sigilGroups}
            self.states.append(new_state)

            if self.labels:
                for id in self.labels:
                    self.canvas.delete(id)
            self.label()

    def label(self):
        self.labels = []
        if self.states[-1]['sigilGroups']:
            sigil = max(self.states[-1]['sigilGroups'], key=lambda g: g[2])
            sigil_coords = list(itertools.chain.from_iterable(sigil[0]))
            min_x = min(x for x, y in sigil_coords)
            min_y = min(y for x, y in sigil_coords)
            max_x = max(x for x, y in sigil_coords)
            max_y = max(y for x, y in sigil_coords)
            self.labels.append(self.canvas.create_rectangle(min_x - 3, min_y - 3, max_x + 3, max_y + 3, outline='#73C9BC', width=2))
            self.labels.append(self.canvas.create_text(min_x - 5, min_y - 3, fill='black', font='Helvetica 9', 
                                                    text=sigil[1], anchor = 'e',))

        if self.states[-1]['signGroups']:
            for sign in self.states[-1]['signGroups']:
                if not self.states[-1]['sigilGroups'] or sign[0][0] not in sigil[0]:
                    coords = list(itertools.chain.from_iterable(sign[0]))
                    min_x = min(x for x, y in coords)
                    min_y = min(y for x, y in coords)
                    max_x = max(x for x, y in coords)
                    max_y = max(y for x, y in coords)
                    self.labels.append(self.canvas.create_rectangle(min_x - 3, min_y - 3, max_x + 3, max_y + 3, outline='#73C9BC', width=2))
                    self.labels.append(self.canvas.create_text(min_x - 5, min_y - 3, fill='black', font='Helvetica 9', 
                                                            text=sign[1], anchor = 'e',))

    def undo(self, event = None): # Undo stroke using 'Z'
        if not self.strokes:
            return
        self.canvas.delete('all')
        self.coordinates = []
        self.strokes.pop()
        for stroke in self.strokes:
            for i in range(len(stroke) - 1):
                self.canvas.create_line(stroke[i][0], stroke[i][1], stroke[i + 1][0], stroke[i + 1][1], width = self.brushSize,
                                         fill = 'black', smooth = True, splinesteps = 5, capstyle = 'round')
                self.coordinates.append((stroke[i][0], stroke[i][1]))
            self.coordinates.append((stroke[-1][0], stroke[-1][1]))
        self.states.pop()
        self.label()


    def clear(self, event = None): # Clear canvas using 'C'
        self.canvas.delete('all')
        self.coordinates = []
        self.strokes = []
        self.states = [{'signGroups': [],
                        'sigilGroups': [],
                        }]

if __name__ == "__main__":
    root = tk.Tk()
    quire = Quire(root)
    quire.pack()
    root.mainloop()
    
