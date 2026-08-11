import tkinter as tk

class Quire(tk.Frame):
    def __init__(self, master = None):
        super().__init__(master)
        self.coordinates = []
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
        self.coordinates.append((event.x, event.y))
        self.currentStrokeCoords.append((event.x, event.y))

    def drag(self, event):
        self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, width = self.brushSize,
                                 fill = 'black', smooth = True, splinesteps = 5, capstyle = 'round')
        self.last_x = event.x
        self.last_y = event.y
        self.coordinates.append((event.x, event.y))
        self.currentStrokeCoords.append((event.x, event.y))

    def release(self, event):
        self.coordinates.append((event.x, event.y))
        self.currentStrokeCoords.append((event.x, event.y))
        self.strokes.append(self.currentStrokeCoords)
        self.currentStrokeCoords = []

    def undo(self, event):
        if not self.strokes:
            return
        print('test')
        self.canvas.delete('all')
        self.coordinates = []
        self.strokes.pop()
        for stroke in self.strokes:
            for i in range(len(stroke) - 1):
                self.canvas.create_line(stroke[i][0], stroke[i][1], stroke[i + 1][0], stroke[i + 1][1], width = self.brushSize,
                                         fill = 'black', smooth = True, splinesteps = 5, capstyle = 'round')
                self.coordinates.append((stroke[i][0], stroke[i][1]))
            self.coordinates.append((stroke[-1][0], stroke[-1][1]))

    def clear(self,event):
        self.canvas.delete('all')
        self.coordinates = []
        self.strokes = []


root = tk.Tk()
quire = Quire(root)
quire.pack()
root.mainloop()
if quire.coordinates:
    print(quire.coordinates[-1])