# August 2026

### 09/08
- Learn how to document projects on GitHub.
### 10/08
- Learn how to format text in markdown.
- Create a basic drawing canvas using tkinter.
### 11/08
- Improve canvas visuals by smoothing out the stroke.
- Create undo and clear keys
### 12/08
- Learn about $-family and recognizers
### 13/08
- Implement the first step of $P style recognizer: the resampling/standardizing
### 14/08
- Reimplement the alloting algorithm of the resampling step, adjust the point placing algorithm in accordance
- Implement the second step of $P style recognizer: the repositioning and resizing
- Learn about the Hungarian algorithm
### 15/08
- Make save_new_templates and templates_visualizer
- Work on the point-cloud evaluation
### 16/08
- Test different potential data sources for recognizer, create a processor to assist the process
- Finish up the point-cloud evaluation with a placeholder acceptance threshold
- Begin working on the rotate and the strokes grouper.
### 17/08
- Finish the 'base' of the strokes grouper (pure distance check without taking ring, sigil detection into account)
- Play around with infrastructural ideas to handle ring detection, inside and outside of ring detection, sigil detection and ring closure detection. (got nowhere sadly :P)
### 18/08
- Test strokes grouping and the concept of multiple thresholds for the types of components
### 25/08
- Finish strokes grouping for sigil and signs, including the on-canvas labeling
### 26/08
- Test current recognizer's accuracy on different symbols
### 27/08
- Redistribute the number of samples each symbol gets based on how great its natural variance and other factors (symbol like fire doesnt need as much while symbol like earth needs a lot of samples).
- Learn about Kabsch and Singular Value Decomposition (SVD), and Iterative Closest Point (ICP)
- Implement the ICP/Kabsch algorithm to match input point cloud against clean drawn template accurately for better scoring while having the input be rotation-invariance.
- Finish the scoring algorithm
### 28/08
- Create the clean templates used for scoring
### 29/08 - 30/09
- Uni exams so no progress :P
### 1/10
- Get back into the project, see where things got left off
### 2/10
- Implement a ringCheck algorithm using kasa circle fitting. Currently includes checking for min angular coverages and min radius. Will add a circularity check in the future.
### 3/10
- Learn about floodfilling and cv2.findContours and how they can be used for ring closure checking while dealing with weird strokes dividing inner regions into smalller counterparts and what not
- Redesign (not yet implemented) the flow of strokes parsing, having symbols grouping wait until a locked ring occurs, in order to have grouping thresholds proportionate to the spell size (which minimizes false grouping for small spell) and remove the need to implement an algorithm to remove a stroke from an existing group and reparse it.
### 4/10

### 5/10

