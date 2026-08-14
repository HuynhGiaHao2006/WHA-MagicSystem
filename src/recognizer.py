import math
import iteround

def Parser(strokes):

    def resample(strokes): # Standardizing by having a fixed number of evenly spaced points across the drawing
        total_length = 0 
        number_of_points = 6
        strokes_points = [0] * len(strokes) # Alloted number of points for each stroke
        strokes_length = [] 
        resampled = [] 

        # Calculate the length of each stroke
        for stroke in strokes:
            stroke_length = 0
            prev_coords = stroke[0]
            for coords in stroke[1:]:
                stroke_length += math.sqrt((coords[0] - prev_coords[0])**2 + (coords[1] - prev_coords[1])**2)
                prev_coords = coords
            total_length += stroke_length
            strokes_length.append(stroke_length)

        # Allot a number of points for each stroke
        points_used = 0
        maximum = (-1, 0)
        for i in range(len(strokes) - 1):
            strokes_points[i] = max(1, round(strokes_length[i]*number_of_points/total_length))
            if strokes_points[i] > maximum[0]:
                maximum = (strokes_points[i], i)
            points_used += strokes_points[i]
        if points_used == number_of_points:
            strokes_points[-1] = 1
            strokes_points[maximum[1]] -= 1
        else: strokes_points[-1] = number_of_points - points_used

        # Walk the original strokes paths and place evenly spaced points
        for i in range(len(strokes)):
            if strokes_points[i] == 1:
                resampled.append([((strokes[i][0][0] + strokes[i][-1][0])/2, (strokes[i][0][1] + strokes[i][-1][1])/2)])
                continue

            standardized_stroke = [strokes[i][0]]
            segment_length = strokes_length[i] / (strokes_points[i] - 1)
            remaining = segment_length
            j = 1
            points_placed = 1
            prev_point = strokes[i][0]
            while True:
                distance = math.sqrt((strokes[i][j][0] - prev_point[0])**2 + (strokes[i][j][1] - prev_point[1])**2) # Distance between the current two points
                if distance < remaining:
                    remaining -= distance
                    prev_point = strokes[i][j]
                    j += 1
                else:
                    temp_x = prev_point[0] + (strokes[i][j][0] - prev_point[0])*remaining/distance
                    temp_y = prev_point[1] + (strokes[i][j][1] - prev_point[1])*remaining/distance
                    standardized_stroke.append((temp_x, temp_y))
                    points_placed += 1
                    prev_point = (temp_x, temp_y)
                    remaining = segment_length
                if points_placed == strokes_points[i] - 1:
                    standardized_stroke.append(strokes[i][-1])
                    break
            resampled.append(standardized_stroke)

        return resampled
                        
    def 

        