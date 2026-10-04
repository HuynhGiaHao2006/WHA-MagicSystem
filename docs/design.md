# WHA-MagicSystem — Problems & Solutions Log

A running record of non-trivial problems hit during development and how they were solved. Not chronological.

---

## Canvas / Input Layer

### Ragged strokes on curves
**Problem:** Drawing each `<B1-Motion>` segment as an independent `create_line` left visible gaps/wedges at joints between segments, worse on tight curves or slow mouse movement.
**Root cause:** Default `capstyle='butt'` cuts each segment's ends flat, perpendicular to that segment — flat cuts from adjacent segments don't align at an angle, exposing background.
**Solution:** `capstyle='round'` on every `create_line` call closes the gaps automatically (rounded end caps overlap cleanly at joints), no manual patching (ovals, fudge factors) needed.
**Note:** True anti-aliasing/feathering is out of scope for tkinter's `Canvas` — it doesn't support it. Would require rendering to an offscreen image (e.g. via Pillow) instead of native canvas primitives. Deferred as a "nice to have, later."

---

## Resampling Pipeline (`recognizer.py`)

### Multi-stroke point allocation
**Problem:** A fixed total point budget (e.g. 64) needs to be split across multiple strokes proportionally to each stroke's length, while still respecting edge cases (short/degenerate strokes, more strokes than points).
**Approach:** Give every stroke a baseline of `1.0`, then distribute the remaining budget proportionally by stroke length. Used `iteround.saferound` initially, later hand-rolled a **largest-remainder** style distribution for full control:
- If `number_of_points >= len(strokes)`: floor each stroke's proportional share, then hand out leftover points one-by-one to the strokes with the largest fractional remainder, until the total matches exactly.
- If `number_of_points < len(strokes)`: baseline is `1.0` each; strip a point from the strokes with the smallest fractional share first, preserving total budget rather than guaranteeing 1 point per stroke (deliberate tradeoff — total point-cloud size needs to stay consistent for downstream matching, more important than per-stroke minimums in this regime).

---

## Recognition (`resample` → `reposition_and_resize` → `evaluate`)

### Why point-cloud ($P/$Q) over ordered ($1/$N) matching
Order/stroke-direction shouldn't matter for recognition (drawing the same shape in a different stroke order should still match) — $P/$Q compare unordered point clouds via optimal one-to-one pairing (the "assignment problem"), solved cheaply via `scipy.optimize.linear_sum_assignment` (a Jonker-Volgenant-style solver — different algorithm from the classic textbook "Hungarian method," but solves the identical problem and always gives the same optimal answer).  
**Tradeoff surfaced later:** full rotation-invariance conflicts with wanting orientation to matter for keystones/signs (both semantically and for later "spell direction" mechanics) — resolved by deliberately *not* making matching rotation-invariant by default, and instead treating "find the best-fit rotation angle" as an explicit search step that doubles as computing the component's orientation for downstream use.

### Two separate template sets for two separate questions
Recognition ("what shape is this") and neatness ("how well was it drawn") are different questions needing different reference data:
- **Recognition templates:** benefit from natural variation (multiple real hand-drawn examples, ideally drawn naturally rather than deliberately imagined as "errors" — real noise generalizes better than authored noise).
- **Neatness templates:** should be idealized/"perfect" references (mathematically generated for regular shapes; traced over a reference image for irregular/hand-designed sigils) since scoring needs a fixed ideal to measure distance from.

---

## Stroke Grouping

### Persistent-history state for free undo
Instead of trying to reverse-compute a prior grouping state on undo, store complete snapshots after every stroke: `states` is a list of "current full state" entries, where each entry is `[(group_strokes, parsed_result), ...]`. On a new stroke, only the affected group(s) get rebuilt/re-parsed; all untouched groups are carried forward **by reference**, not recomputed. Undo = `history.pop()`. This is a known pattern ("persistent" / structural-sharing data structures) — specifically valuable because it makes undo close to free and naturally limits recomputation to only what actually changed each step.  
**Bug caught:** The empty-groups base case did `current_groups.append(...)` — mutating the input list in place rather than returning a new one, which would have silently corrupted earlier history entries sharing that same list reference. Fixed to always return a fresh list, consistent with the rest of the function.

### Single distance threshold can't serve all component types at once
**Problem:** Ring strokes need near-total overlap to group correctly; sign strokes are close but not overlapping; sigil strokes can be legitimately far apart (e.g. deliberately separated decorative strokes) — one global proximity threshold can't satisfy "don't merge nearby-but-distinct signs" and "do merge far-apart sigil strokes" simultaneously, no matter how it's tuned.  
**Direction chosen:** Separate thresholds per component type rather than one global value — reflects a genuine structural difference between the three component types, not just a magic-number tuning problem.
**Final design:** Make a stroke grouping algorithm base on the closest distance between any points of 2 strokes. Since sigil grouping has a higher threshold, sign groups will be completely inside or outside of the sigils. This means that we can exclude sign groups that is used in the sigil from being evaluated for the spell by checking a representative stroke. The ring will have its own algorithm since the many features it has (check for strokes inside vs outside ring, check for closure,...) can't be handled with threshold base strokes grouping alone.

### Brute force rotation checking is expensive
**Problem:** Due to a large number of templates for the components, if checking for the right rotation is done using brute force, computational cost will be significantly increase.  
**First approach:** The dataset for hand-drawn components found online have samples with random rotation whose angle offsets from upright are tracked. If this dataset is used as the template for the recognizer, the angle offset can also be extracted and can be used to narrow the rotation search window to its proximity. **The downside** of this approach lies in the fact that the computational cost does not disappear but rather shifts from matching against N templates × M rotation angles to matching against M pre-rotated samples per symbol. **Another tradeoff surfaced during testing:** Symbols susceptible to rotation (such as the wind directs air sigil) have their evaluation lowered drastically with angle offsets even lower ones, resulting in frequence recognizer mismatchs (mistakening wind-directs-air to water being the most prominent) while using a rotation-inclusive dataset due to insufficient number of sample required to cover the full 360 degrees.  
**Approach chosen**: Implement the Iterative Closest Point(ICP)-Kabsch algorithm to find the most accurate rotation needed to perform on the input. Still use the rotation-inclusive dataset. Angle offset provided from the data will be used as a starting point for the ICP-Kabsch algorithm to reduce iteratives needed per sample and minimize cases where the algorithm get stuck in a local minima. The computational cost problem with using the dataset will be dealt with by reducing the number of templates for symmetrical symbols such as fire or light, while keeping it relatively high for asymmetrical symbols and those who have a similar point-cloud structure to each others.

### Ring check and false grouping
**Problem 1:** Ring check is implemented using the Kasa circle fitting algorithm, checking for a minimum angular coverage, minimum radius and circularity. Once one ring group pass the requirement, it will be locked as the ring (the strokes used for the ring alongside its radius and center can still be adjusted as new strokes get added to the group, but it won't switch to other ring group because they have a better fit). Ring strokes will be relatively close to symbol groups in most cases, meaning a symbol group can falsely absorb the ring strokes, resulting in inaccurate parsing. A filter is necessary in order to prevent any ring strokes of the currently locked ring from being taken into account when dealing with strokes grouping for symbols. Additionally, as things are right now, sigils and signs grouping happens right from the start, meaning when a locked ring is drawn after some grouping already happened, removing filtered out stroke from existing groups is needed(this is probably going to be much more complexed since a group can be split into smaller groups if the removed stroke is a "connecting stroke" of sort).
**Problem 2:** Unless the minimum radius is excessively high, completely disallowing small to medium size drawing and only allowing exclusively large size spell, a flat threshold for each type of strokes grouping  is going to lead to many false grouping, especially when a spell is small and symbols are cramped into a tight space. As such, the thresholds should be proportionate to the spell size, specifically the radius of the first initial locked ring (having the threshold update every single time the radius updates will results in massive computational cost, the radius of the first locked ring snapshot should be good enough). This further support the idea of delaying the grouping of symbols.
**Parsing flow redesign:** Strokes grouping for signs and sigils will now wait until there is a locked ring. After which, grouping thresholds will be calculated and locked in based on the rings radius. Strokes used for the existing locked ring and any incoming stroke that get grouped with the locked ring's group will not be pass into the normal symbol grouping flow. This result in a noticeable lag spike if many symbols is drawn before a locked ring occur.

### Ring closure and weird strokes handling
**Problem:** With ring detection being implemented using the Kasa circle fitting algorithm (with an angular coverage threshold of at least 50%), there are many different scenarios to ring closure that a simple floodfill algorithm (check if theres a path connecting a point inside the circle and one outside of it without crossing a stroke) simply cannot cover. As such, the current 2 step verification for closure includes a ring check, along side a closure check, and this is not an adequate filter to determine if a spell should be casted. An of shape that would be casted but shouldn't be is half a circle with the two ends being connected by a straight line. This passes as a ring and also passes the floodfill algorithm for closure checking, but really shouldn't be a valid spell cast.
**First approach and its problem:** Have another step in the verification checking for minimum angular coverage 