import tkinter as tk
import math
import time
from recognizer import Parser, resample, reposition_and_resize
from templates_visualizer import visualize
from strokes_grouper import groupStrokes

class State:

    def __init__(self):
        pass

class Quire(tk.Frame):

    def __init__(self, master = None):
        super().__init__(master)
        self.states = [[]]
        self.currentStrokeCoords = []
        self.strokes = []

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

        self.states.append(groupStrokes(self.states[-1], self.strokes[-1]))

        stroke_length = 0
        prev_coords = self.strokes[-1][0]
        for coords in self.strokes[-1][1:]:
            stroke_length += math.sqrt((coords[0] - prev_coords[0])**2 + (coords[1] - prev_coords[1])**2)
            prev_coords = coords
        if stroke_length < 10: # Set a limit to how short a stroke can be
            self.undo()

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

    def clear(self,event): # Clear canvas using 'C'
        self.canvas.delete('all')
        self.coordinates = []
        self.strokes = []
        self.states = [[]]

if __name__ == "__main__":
    root = tk.Tk()
    quire = Quire(root)
    quire.pack()
    root.mainloop()
    for group in quire.states[-1]:
        print(Parser(group, 64))
