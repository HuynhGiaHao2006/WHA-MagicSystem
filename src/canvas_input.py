import tkinter as tk
import math
import itertools
import numpy as np
import cv2
from PIL import Image, ImageDraw
from scipy.spatial.distance import cdist
from recognizer import Parser, Scorer, resample, reposition_and_resize

minRadius = 150
def ringCheck(ringGroups, lockedRing, inputStroke, threshold = 5):
    # Kasa circle fitting
    def Kasa_compute(group_strokes): # Used for updating locked ring's center and radius
        flatten = np.asarray(list(itertools.chain.from_iterable(group_strokes)), dtype=float)
        x = flatten[:, 0]
        y = flatten[:, 1]
        ones = np.ones_like(x)
    
        M = np.column_stack((x, y, ones))
        b = x**2 + y**2
    
        A, B, C = np.linalg.lstsq(M, b, rcond=None)[0]
    
        x_center = A/2
        y_center = B/2
        radius = np.sqrt(C + x_center**2 + y_center**2)
        return (group_strokes, (x_center, y_center), radius)

    def Kasa_check(group_strokes): # Used for checking for a ring
        flatten = np.asarray(list(itertools.chain.from_iterable(group_strokes)), dtype=float)
        x = flatten[:, 0]
        y = flatten[:, 1]
        ones = np.ones_like(x)
    
        M = np.column_stack((x, y, ones))
        b = x**2 + y**2
    
        A, B, C = np.linalg.lstsq(M, b, rcond=None)[0]
    
        x_center = A/2
        y_center = B/2
        radius = np.sqrt(C + x_center**2 + y_center**2)

        # Calculate circularity
        points = list(itertools.chain.from_iterable(group_strokes))
        offsets = []
        for i in range(len(x)):
            offsets.append(abs(math.sqrt((x[i] - x_center)**2 + (y[i] - y_center)**2) - radius))
        circularity = (sum(offsets)*300/len(offsets))/radius # Score is proportionate to size, otherwise smaller = more circular

        # Calculate angular coverage (by computing biggest missing angular gap)
        angles = sorted(math.atan2(y - y_center, x - x_center) for (x, y) in flatten)
        gaps = list((angles[i+1]-angles[i]) for i in range(len(angles) - 1)) + [2*math.pi + angles[0] - angles[-1]]
        biggest_gap = max(gaps)
        
        condition = [biggest_gap < math.pi, radius > minRadius, circularity < 25] # Can change the circularity threshold later
        Ring = (group_strokes, (x_center, y_center), radius) if all(condition) else ([], (0, 0), 0)
        return Ring

    if lockedRing[0]:
        min_dist = cdist(inputStroke, list(itertools.chain.from_iterable(lockedRing[0]))).min()
        if min_dist < threshold:
            new_locked_strokes = [inputStroke] + lockedRing[0]
            lockedRing = Kasa_compute(new_locked_strokes)
        return lockedRing, ringGroups
    
    updated_groups_list = []
    new_group_strokes = [inputStroke]
    for group in ringGroups:
        min_dist = cdist(inputStroke, list(itertools.chain.from_iterable(group))).min()
        if min_dist < threshold:
            new_group_strokes += group
            continue
        else: updated_groups_list.append(group)
    updated_groups_list.append(new_group_strokes)

    lockedRing = Kasa_check(new_group_strokes)
    return lockedRing, updated_groups_list

# Strokes grouping and symbol recognition
def groupStrokes(current_groups, inputStroke, type = 'signs', threshold = 25):
    groups_list = [group for group in current_groups]
    if not groups_list:
        symbol, standardized = Parser([inputStroke], 64, type)
        score, angle = Scorer(standardized, symbol)
        groups_list.append(([inputStroke], symbol, score, angle))
        return groups_list

    updated_groups_list = []
    new_group_strokes = [inputStroke]
    for group in groups_list:
        min_dist = cdist(inputStroke, list(itertools.chain.from_iterable(group[0]))).min()
        if min_dist < threshold:
            new_group_strokes += group[0]
            continue
        else: updated_groups_list.append(group)
    new_group_symbol, standardized = Parser(new_group_strokes, 64, type)
    new_group_score, new_group_angle = Scorer(standardized, new_group_symbol)
    updated_groups_list.append((new_group_strokes, new_group_symbol, new_group_score, new_group_angle))
    return updated_groups_list

def rasterize(strokes, canvasWidth, canvasHeight, brushSize):
    from PIL import Image, ImageDraw
    import numpy as np

    img = Image.new('L', (canvasWidth, canvasHeight), 255)
    draw = ImageDraw.Draw(img)
    for stroke in strokes:
        draw.circle(stroke[0], brushSize / 2, fill = 0)
        draw.circle(stroke[-1], brushSize / 2, fill = 0)
        draw.line(stroke, fill = 0, width = brushSize, joint = 'curve')
    array = np.array(img)
    return array

def addStrokeRasterized(inputStroke, array, brushSize):
    img = Image.fromarray(array, 'L')
    draw = ImageDraw.Draw(img)
    draw.circle(inputStroke[0], brushSize / 2, fill = 0)
    draw.circle(inputStroke[-1], brushSize / 2, fill = 0)
    draw.line(inputStroke, fill = 0, width = brushSize, joint = 'curve')
    return_array = np.array(img)
    return return_array

FONT_LABEL = ("Palatino Linotype", 10)
class Quire(tk.Frame):
    def __init__(self, master = None):
        super().__init__(master)
        self.states = [{'signGroups': [], # List of groups in the form of a tuple of strokes coords [0], symbol [1], score [2] and angle [3]
                        'sigilGroups': [], 
                        'ringGroups': [], # List of groups in the form of a list of strokes coords
                        'lockedRing': ([], (0, 0), 0), # Tuple of stroke coords [0], center_coords [1] and radius [2]
                        'rasterized': [] # 2D binary array of the canvas, depicting which pixels are filled
                        }]
        self.labels = []
        self.currentStrokeCoords = []
        self.strokes = []
        self.signGroupingThreshold = 25
        self.sigilGroupingThreshold = 50

        self.brushSize = 5
        self.canvasWidth = 800
        self.canvasHeight = 600
        self.last_x = 0
        self.last_y = 0

        self.canvas = tk.Canvas(self, width=self.canvasWidth, height=self.canvasHeight, bg = 'beige')
        self.canvas.bind('<Button-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<ButtonRelease-1>', self.release)
        self.canvas.focus_set()
        self.canvas.bind('<z>', self.undo)
        self.canvas.bind('<c>', self.clear)
        self.canvas.pack()
        self.label()

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

        # Checking for minimum stroke length
        stroke_length = 0
        prev_coords = self.strokes[-1][0]
        for coords in self.strokes[-1][1:]:
            stroke_length += math.sqrt((coords[0] - prev_coords[0])**2 + (coords[1] - prev_coords[1])**2)
            prev_coords = coords
        if stroke_length < 10:
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

        # Actual process on release
        else:
            new_signGroups = self.states[-1]['signGroups']
            new_sigilGroups = self.states[-1]['sigilGroups']
            new_rasterized = self.states[-1]['rasterized']
            new_lockedRing, new_ringGroups = ringCheck(self.states[-1]['ringGroups'], self.states[-1]['lockedRing'], self.strokes[-1])
            if self.states[-1]['lockedRing'][0]:
                new_rasterized = addStrokeRasterized(self.strokes[-1], self.states[-1]['rasterized'], self.brushSize)
                if not self.strokes[-1] is new_lockedRing[0][0]: # new stroke has to be put at the start of the list
                    new_signGroups = groupStrokes(self.states[-1]['signGroups'], self.strokes[-1], 'signs', self.signGroupingThreshold)
                    new_sigilGroups = groupStrokes(self.states[-1]['sigilGroups'], self.strokes[-1], 'sigils', self.sigilGroupingThreshold)
            else:
                if new_lockedRing[0]:
                    new_rasterized = rasterize(self.strokes, self.canvasWidth, self.canvasHeight, self.brushSize)
                    self.signGroupingThreshold = min(25, 0.125*new_lockedRing[2])
                    self.sigilGroupingThreshold = min(40, 0.2*new_lockedRing[2])
                    for stroke in self.strokes:
                        if not any(stroke is s for s in new_lockedRing[0]):
                            new_signGroups = groupStrokes(new_signGroups, stroke, 'signs', self.signGroupingThreshold)
                            new_sigilGroups = groupStrokes(new_sigilGroups, stroke, 'sigils', self.sigilGroupingThreshold)
            new_state = {'signGroups': new_signGroups, 'sigilGroups': new_sigilGroups,
                        'ringGroups': new_ringGroups, 'lockedRing': new_lockedRing, 'rasterized': new_rasterized}
            self.states.append(new_state)

            if self.labels:
                for id in self.labels:
                    self.canvas.delete(id)
            self.label()

    def label(self):
        def drawRing(x, y, radius):
            self.labels.append(self.canvas.create_oval(x + radius*1.03, y + radius*1.03, x - radius*1.03, y - radius*1.03, dash=(50,50), outline = 'burlywood', 
                                                       width = 2))
            self.canvas.tag_lower(self.labels[-1])
            self.labels.append(self.canvas.create_oval(x + radius*0.97, y + radius*0.97, x - radius*0.97, y - radius*0.97, dash=(50,50), outline = 'burlywood', 
                                                                   width = 2))
            self.canvas.tag_lower(self.labels[-1])
            self.labels.append(self.canvas.create_oval(x + radius/3, y + radius/3, x - radius/3, y - radius/3, dash=(50,50), outline = 'burlywood', 
                                                       width = 2)) # Rough area for sigil
            self.canvas.tag_lower(self.labels[-1])

        self.labels = []
        if self.states[-1]['lockedRing'][0]:
            x, y = self.states[-1]['lockedRing'][1]
            radius = self.states[-1]['lockedRing'][2]
        else:
            x = self.canvasWidth/2
            y = self.canvasHeight/2
            radius = 225
        drawRing(x, y, radius)

        # Currently only support 1 sigil
        if self.states[-1]['sigilGroups']:
            sigil = max(self.states[-1]['sigilGroups'], key=lambda g: g[2])
            sigil_coords = list(itertools.chain.from_iterable(sigil[0]))
            min_x = min(x for x, y in sigil_coords)
            min_y = min(y for x, y in sigil_coords)
            max_x = max(x for x, y in sigil_coords)
            max_y = max(y for x, y in sigil_coords)
            if sigil[1] != 'No match':
                self.labels.append(self.canvas.create_rectangle(min_x - 3, min_y - 3, max_x + 3, max_y + 3, outline='#73C9BC', width=2))
                self.labels.append(self.canvas.create_text(min_x - 5, min_y - 3, fill='black', font=FONT_LABEL, 
                                                           text=f'{sigil[1]} {sigil[2]} {sigil[3]}', anchor = 'e',))

        if self.states[-1]['signGroups']:
            for sign in self.states[-1]['signGroups']:
                if not self.states[-1]['sigilGroups'] or sigil[1] == 'No match' or not any(sign[0][0] is s for s in sigil[0]):
                    coords = list(itertools.chain.from_iterable(sign[0]))
                    min_x = min(x for x, y in coords)
                    min_y = min(y for x, y in coords)
                    max_x = max(x for x, y in coords)
                    max_y = max(y for x, y in coords)
                    self.labels.append(self.canvas.create_rectangle(min_x - 3, min_y - 3, max_x + 3, max_y + 3, outline='#73C9BC', width=2))
                    if sign[1] != 'No match':
                        self.labels.append(self.canvas.create_text(min_x - 5, min_y - 3, fill='black', font=FONT_LABEL, 
                                                                    text=f'{sign[1]} {sign[2]} {sign[3]}', anchor = 'e',))

    def undo(self, event = None): # Undo stroke using 'Z'
        if not self.strokes:
            return
        self.canvas.delete('!keep')
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
                        'ringGroups': [],
                        'lockedRing': ([], (0, 0), 0),
                        'rasterized': []
                        }]

if __name__ == "__main__":
    root = tk.Tk()
    quire = Quire(root)
    quire.pack()
    root.mainloop()
    array = quire.states[-1]['rasterized']
    img = Image.fromarray(array, 'L')
    img.show()
    
