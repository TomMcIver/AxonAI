-- Seed: teach-step explanation cards for demo / item-bank concepts.
-- Skipping concept_id 278: checked live public.concepts on 2026-04-27 and it is absent (current ids 1..187).
-- Add a row for concept_id 278 when that concept exists in the graph.
-- Idempotent: safe to re-run.
INSERT INTO concept_explanations (concept_id, explanation_text, worked_example, common_misconception, year_level)
VALUES
(
  5,
  $e5$
A fraction is a way to say how much of a whole you are talking about, by counting equal parts. The number on the bottom says how many equal parts the whole is cut into, and the number on the top says how many of those parts you have. Equivalent fractions are two different ways of writing the same amount, and you need that idea for sharing, measuring, and for all the harder maths that comes next.
$e5$,
  $w5$
You and a friend share a large chocolate block. The block is in 2 equal rows, and you take 1 full row. You have 1 out of 2 equal parts, so you have 1/2 of the block.
The same block is re-marked into 4 equal rows (each row is half the size of the old row). You take 2 of the new rows. You still have the same amount of chocolate as before, but now you can count it as 2 out of 4 equal parts, so you have 2/4 of the block.
To see the two fractions are the same, line up the story: 1/2 and 2/4 both mean "half the block," and on a calculator 1 ÷ 2 = 0.5 and 2 ÷ 4 = 0.5, so the amount matches.
$w5$,
  $c5$
Students often think a bigger number on the top or bottom always means a bigger share, but actually 1/8 is a smaller amount than 1/2 because the whole is cut into more, smaller pieces.
$c5$,
  7
),
(
  75,
  $e75$
Data is the information you collect to answer a question, and the "type" of data tells you what you are allowed to do with it. Categorical data is words or labels (like "red" or "Year 10"), and numerical data is numbers you can measure or count. Knowing the type matters because it decides whether you can take an average, draw a certain graph, or use a formula that only works for numbers.
$e75$,
  $w75$
You ask everyone in your class how they travel to school. You write down each answer as one word: walk, bike, bus, car, train.
You count how many people chose each answer: walk 8, bike 5, bus 12, car 6, train 1.
Those labels are categorical data because they are names of choices, not measurements on a ruler.
You cannot correctly find "the mean travel mode" by averaging the words, but you can say which mode was most common (bus, with 12 people).
$w75$,
  $c75$
Students often think any set of numbers in a table is automatically "numerical data you can average," but actually if the numbers are just codes for labels (like 1 = red, 2 = blue), they are still categories in disguise.
$c75$,
  7
),
(
  77,
  $e77$
The center of a set of numbers (like the mean) tells you a typical value, but spread tells you how spread out the values are. Two classes can have the same average mark and still feel very different if one class has marks bunched together and the other has some very low and very high marks. Range and interquartile range (IQR) are simple ways to describe that spread so you do not mistake a risky, jumpy dataset for a steady one.
$e77$,
  $w77$
Here are seven test scores out of 100: 62, 64, 65, 66, 67, 68, 70.
Put them in order (they already are). The smallest value is 62 and the largest is 70.
The range is biggest minus smallest: 70 − 62 = 8 marks.
To find the IQR, first find the median: with seven numbers the median is the middle one, which is the 4th value: 66.
Split the lower half (62, 64, 65) and the upper half (67, 68, 70). The median of the lower half is 64; the median of the upper half is 68.
IQR is Q3 − Q1: 68 − 64 = 4 marks. So scores are fairly bunched: the middle 50% spans only 4 marks.
$w77$,
  $c77$
Students often think a large range always means the data is "messy," but actually one extreme outlier can make the range huge while most values are still close together, which is why the IQR is often safer for describing spread.
$c77$,
  9
),
(
  79,
  $e79$
A frequency table groups numbers into bins and counts how many values fall in each bin. A histogram is the picture of that table: each bar shows a bin, and the bar height shows the count (or density, depending on setup). That matters because it shows the shape of the data—where the pile of values is and whether there are gaps or a long tail.
$e79$,
  $w79$
You measure the time (in whole minutes) it takes 20 people to walk the same track, and these are the times: 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31.
Make bins 10–19 minutes, 20–29 minutes, and 30–39 minutes.
Count values in 10–19: 12 through 19 is 8 people.
Count values in 20–29: 20 through 29 is 10 people.
Count values in 30–39: 30 and 31 is 2 people.
Draw three bars side by side with heights 8, 10, and 2. The middle bar is tallest, so most walks land in the 20–29 minute range.
$w79$,
  $c79$
Students often think the bar width can be ignored as long as the bars look neat, but actually bins must not overlap and every value must land in exactly one bin, otherwise the counts and the shape of the histogram become wrong.
$c79$,
  9
),
(
  82,
  $e82$
Probability is a number between 0 and 1 that describes how likely an outcome is when something is random but fair and known. You work it out as "how many ways the event can happen" divided by "how many equally likely outcomes there are in total." Complement means the opposite outcome, and P(not A) is 1 − P(A), which is a shortcut you will use constantly.
$e82$,
  $w82$
You roll one normal six-sided die once. The sample space is the six faces: 1, 2, 3, 4, 5, 6. There are 6 equally likely outcomes in total.
Let A be "roll an even number." The even faces are 2, 4, and 6, which is 3 outcomes.
So P(A) = 3/6 = 1/2.
The complement is "not even," meaning odd: 1, 3, 5, which is also 3 outcomes, so P(not A) = 3/6 = 1/2.
Check the complement rule: P(not A) = 1 − P(A) = 1 − 1/2 = 1/2, which matches.
$w82$,
  $c82$
Students often think if a coin landed heads many times in a row, tails is "due," but actually for a fair coin each flip still has two equally likely sides, so the next flip is not pulled back by past flips.
$c82$,
  8
),
(
  84,
  $e84$
A tree diagram is a picture for multi-step chance: each branch split shows what can happen next, and you multiply along a path when steps are independent. That matters for real situations like "test twice" or "pick then pick again" because it keeps the order and the probabilities visible so you do not double-count outcomes.
$e84$,
  $w84$
You spin a fair 4-part spinner labeled 1, 2, 3, 4 twice. Each spin is equally likely to land on any of the four numbers, so each branch from a spin has probability 1/4.
From Start, draw 4 branches for the first spin, each labeled 1/4.
From each first-spin end, draw 4 more branches for the second spin, each labeled 1/4.
Pick the path "first spin is 3" and then "second spin is 4." Multiply as you walk: (1/4) × (1/4) = 1/16.
So P(3 then 4) = 1/16.
$w84$,
  $c84$
Students often add branch probabilities when they should multiply along one path, but actually multiplication is for one full story in order, and addition is when you combine different separate stories that achieve the same kind of win.
$c84$,
  10
),
(
  92,
  $e92$
The chain rule is the tool for a function built as "something inside something else," like temperature through the day changing, and another process depending on that temperature. You find the overall rate by multiplying two smaller rates: how fast the inside part changes as the input moves, times how fast the outside part changes as the inside part moves. That is why people say "multiply the derivatives" for layers of functions.
$e92$,
  $w92$
Let y = (2x + 3)^3. Think of an inside part u = 2x + 3 and an outside part y = u^3.
Find du/dx: u = 2x + 3, so du/dx = 2.
Find dy/du: y = u^3, so dy/du = 3u^2.
Apply the chain rule: dy/dx = (dy/du) × (du/dx) = 3u^2 × 2 = 6u^2.
Substitute u back: u = 2x + 3, so dy/dx = 6(2x + 3)^2.
Check at x = 1: u = 2(1) + 3 = 5, and dy/dx = 6 × 5^2 = 6 × 25 = 150.
$w92$,
  $c92$
Students often forget to multiply by the derivative of the inside function, but actually if the inside changes more slowly or more quickly, the overall rate must pick that up or the answer is missing a whole factor.
$c92$,
  13
),
(
  93,
  $e93$
A rate of change is how fast one quantity moves compared to another, when the second quantity is moving smoothly. In many NCEA settings you use a derivative to read that rate from a formula: for example, distance changing with time gives speed as a rate, and cost changing with quantity gives marginal cost as a rate. That is why the same differentiation idea shows up in motion, graphs, and word problems that ask "how fast."
$e93$,
  $w93$
A drone's height above the ground in metres is h = t^3 − 6t^2 + 9t, where t is time in seconds after takeoff, for 0 ≤ t ≤ 4.
Find the rate height changes with time: differentiate, h'(t) = 3t^2 − 12t + 9.
At t = 2 seconds, substitute: h'(2) = 3(4) − 12(2) + 9 = 12 − 24 + 9 = −3.
The rate is −3 metres per second, which means at that instant the drone is moving downward at 3 metres per second.
$w93$,
  $c93$
Students often plug a time value into the original formula and call that "the rate," but actually the rate is the value of the derived function at that time, not the height or cost itself.
$c93$,
  12
),
(
  95,
  $e95$
An optimisation problem asks for the biggest or smallest value you can get, while still fitting a rule from the situation, like a fixed amount of fencing or a fixed budget. You build one main formula for the thing you want to maximise or minimise, express it using as few letters as possible, then use derivatives to find turning points and check which one fits the practical story.
$e95$,
  $w95$
You have 40 m of fencing to make a rectangular vegetable bed, and you will use an existing straight wall as one whole side so you only fence the other three sides.
Call the side parallel to the wall L metres, and each end width w metres. The fencing used is L + w + w = L + 2w, and that equals 40, so L = 40 − 2w.
The area is A = L × w = (40 − 2w) × w = 40w − 2w^2.
Differentiate: dA/dw = 40 − 4w. Set to zero: 40 − 4w = 0, so w = 10.
Then L = 40 − 2(10) = 20. Area A = 20 × 10 = 200 square metres.
Check endpoints: if w = 0, area 0; if w = 20, L = 0, area 0, so w = 10 gives the largest practical area.
$w95$,
  $c95$
Students often maximise the wrong thing, like maximising perimeter when the question asked for area, but actually you must write the quantity named in the problem as a function of one variable before you differentiate.
$c95$,
  13
),
(
  103,
  $e103$
A cell is packed with tiny parts called organelles, each with a job so the cell can stay alive and do its work. The membrane around the cell controls what goes in and out, the control centre holds instructions, many organelles build and ship materials, and some break waste down. You do not need every small detail for every question, but you do need to match organelle to job cleanly in writing and in diagrams.
$e103$,
  $w103$
Pick one cell that is working hard: a muscle cell in your leg during a sprint.
Mitochondria are where the cell gets useful energy from fuel; more work means you expect more mitochondria in muscle cells than in some other cell types.
Ribosomes build proteins; in a muscle cell they support the proteins that let the muscle contract.
The Golgi apparatus packages and sends materials so the cell can ship things in the right direction.
Rough endoplasmic reticulum has ribosomes on it and helps make and fold proteins that are meant to be sent out or placed in the membrane.
Lysosomes contain enzymes that break down worn-out cell parts safely inside the cell.
Say the story in order: energy in mitochondria, build in ribosomes on rough ER, finish and package in Golgi, recycle with lysosomes.
$w103$,
  $c103$
Students often say the nucleus is where energy is made, but actually the nucleus holds genetic instructions; the main organelle people link to releasing useful energy from fuel in many school-level stories is the mitochondria.
$c103$,
  9
),
(
  106,
  $e106$
Active transport is how a cell moves substances across a membrane when they need to go from low concentration to higher concentration, the "uphill" direction. That move does not happen by simple spreading alone, so the cell spends energy (often from ATP) to pump or carry the substance through. That matters for nerve signals, nutrient uptake, and keeping the inside of the cell stable even when the outside looks different.
$e106$,
  $w106$
Picture a sodium–potassium pump in a nerve cell membrane. Outside the cell, sodium ions are common, and inside, potassium ions are kept high for the resting state the cell needs.
The pump grabs three sodium ions from inside and forces them out, even when that is against the concentration direction the ions would drift.
It then brings two potassium ions in, again using energy to do the swap.
Each full cycle costs the cell energy (ATP is split to power the shape change of the pump), which is why this is active transport rather than passive spreading.
Net result: the cell maintains the ion gaps that keep the membrane ready for a signal.
$w106$,
  $c106$
Students often think diffusion and active transport are the same because both move substances across a membrane, but actually diffusion moves down a concentration gradient with no energy cost on its own, while active transport spends energy to move substances the other way when the cell needs it.
$c106$,
  10
)
ON CONFLICT (concept_id) DO UPDATE SET
  explanation_text = EXCLUDED.explanation_text,
  worked_example = EXCLUDED.worked_example,
  common_misconception = EXCLUDED.common_misconception,
  year_level = EXCLUDED.year_level,
  updated_at = NOW();
