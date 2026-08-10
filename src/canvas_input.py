import tkinter as tk

class Quire(tk.Frame):
    def __init__(self, master = None):
        super().__init__(master)
        self.coordinates = []

        self.brushSize = 5
        self.last_x = 0
        self.last_y = 0

        self.canvas = tk.Canvas(self, width=800, height=600, bg = 'beige')
        self.canvas.bind('<Button-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.pack()

    def press(self, event):
        self.canvas.create_oval(event.x - self.brushSize / 2, event.y - self.brushSize / 2, 
                                event.x + self.brushSize / 2, event.y + self.brushSize / 2, fill = 'black')
        self.last_x = event.x
        self.last_y = event.y
        self.coordinates.append((event.x, event.y))

    def drag(self, event):
        self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, width = self.brushSize, fill = 'black')
        self.last_x = event.x
        self.last_y = event.y
        self.coordinates.append((event.x, event.y))


root = tk.Tk()
quire = Quire(root)
quire.pack()
if quire.coordinates:
    print(quire.coordinates[-1])
root.mainloop()
