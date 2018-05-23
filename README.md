# saberCNC
A collection of CNC code for saber construction.

# NanoPCB
Nano PCB takes an text-art PCB and creates gcode for sending to a CNC.
Basically markdown for printed circuit board cutting.

## Goals:
1. Simple: from a text file to gcode in one step
2. Basic CNC machine.
   - Isolate circuit, drill, and cut PCB without a bit change. (I use 1.0mm
     bits, although 0.8mm might be better.)
   - Account for significant runout. NanoPCB creates straight cuts that are
     as long as possible. It doesn't use any curves or detail work.

Currently it only works single-sided. It would be straightforward to support
the flip, the code just needs a way to define the two sides and the flipping
axis. It can print the circuit flipped if you want to solder on the down side.

## Legend

* ````#````         Starts a comment line.
* ````[ ]````       Square brackets define a cutting border.
* ````%````         A percent defines a cutting path. The path must close, but can curve around for printing oddly shaped boards.
* ````a-z````       Letters define drill holes.
* ````# +M 2.2````  Defines a mounting hole, drill hole, etc. (Not isolated.)

## Example

````
#################################
# +M 2.2  Mounting
# # # # # # # # # # # # # # # # #
[               ]
  M           M 

V o     o-r g   b
| |         |   |
V o     o---o   o

G   o o   o   o
|
G---o-o---o---o
|
G o-o o-o o-o o-o 

  M           M 
[               ]
````
