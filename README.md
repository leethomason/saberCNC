# saberCNC
A collection of CNC code for saber construction.

# NanoPCB
Nano PCB takes an text-art PCB and creates gcode for sending to a CNC.
Basically markdown from printed circuit board cutting.

## Goals:
1. Simple: from a text file to gcode in one step
2. Basic CNC machine. The CNC machine I wrote it for is basic and inaccurate.
   The NanoPCB is tailored to a low end machine:
   - Isolate circuit, drill, and cut PCB without a bit change. (I use 1.0mm
     bits, although 0.8mm might be better.)
   - Account for significant runout. NanoPCB creates straight cuts that are
     as long as possible. It doesn't use any curves or detail work.

Currently it only works single-sided. It would be straightforward to support
the flip, the code just needs a way to define the two sides and the flipping
axis.

## Info mode
There are several command line options. The most useful - before you generate
gcode - is to use -i (--info) to print information about the circuit.

## Examples:

This drills 3 holes, isolates them, and will be cut square to fit.
````
o--o
|  |
o--+

# The symbols -, |, and + draw traces.
# Most other things are interpreted as drill holes.
````
- nDrill points = 3
- rows/cols = 6,5
- size (on tool center) = 6.35,5.08


This drills 6 holes, isolates them, and will be cut square to fit.
````
1 2 3
| | |
o o o

# 1, 2, 3 are all drill holes, but allow you to comment
# 1 ground
# 2 vcc
# 3 clock
````
- nDrill points = 6
- rows/cols = 7,5
- size (on tool center) = 7.62,5.08


This drills 6 holes, isolates them, and will be cut to larger bounds.
````
[           ]
    g v c
    | | |
    o o o
[           ]

# The [ and ] characters make the cutting bounds larger. It will be
# cut so that the brackets are NOT removed. (So they expand the bounds
# just like drill holes do...except without the drill holes.)
````
- nDrill points = 6
- rows/cols = 15,7
- size (on tool center) = 17.78,7.62


If you want to specify a cutting path, you may do so. Use the percent
character; just be sure to define a full path. NanoPCB follows the
percent character to trace out a path.

````
%%   %%%%%%   %%
%              %
  oo        oo

  oo        oo

% oo        oo %
%              %
%%%%%      %%%%%
    %      %

      o--o
    %      %
    %%    %%
````
- nDrill points = 14
- rows/cols = 18,16
- size (on tool center) = 19.05,16.51





