import json
import matplotlib.pyplot as plt
import itertools

name = input('Input the name of the component: ')
with open('templates.json', 'r') as f:
        templates = json.load(f)
        strokes = templates[name]

for stroke in strokes:     
    resampled_x = []
    resampled_y = []
    for coord in stroke:
        resampled_x.append(coord[0])
        resampled_y.append(coord[1])
    plt.plot(resampled_x, resampled_y, color = 'black')

plt.gca().invert_yaxis()  # tkinter's y-axis grows downward; flip so it looks right-side-up
plt.axis('equal')          # keep x/y scale proportional so shapes aren't visually distorted
plt.show()