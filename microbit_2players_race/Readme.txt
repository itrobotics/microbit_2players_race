Project : Micro:Bit 2-player racing game
Author: Josmy
date: November 14, 2019
==========

Idea
=====
2-player racing game. Each player will carry a microbit and will run (or simulate it). There is a racing track on the screen with two players. The computer will receive the data from the two microbits carried by the players and process it. The players' progress will be shown in the screen (with the destination on sight) and the first player to reach the destination wins.

Method: 
=======

3 microbits are used for this project. One microbit(the moderator) is connected to the computer and sends informations(e.g. when to start) via radio to the 2 other microbits (the players). In return, the players will send their movements to the moderator which transfer this data to the computer for processing.

Computer --- Serial ---> Moderator --- Radio ---> Players --- Radio ---> Moderator -- Serial ---> Computer (iterative)


Directory Layout:
===============
      
'03_microbit_2players_race/'
├─microbit_programs
|   └─moderator.hex
|   └─player.hex
|   
└─microbit_1v1_race.ipynb


microbit_programs =====> Includes the microbit codes for the moderator and the players

microbit_1v1_race.py =====> Python code to run on your computer. It contains the tkinter GUI and changes it according to the racing informations sent by the microbits


#Required Module
python -m serial.tools.list_ports
pip install pygame
pip install pyserial

#Tkinter 
race_track.jpg  (800*160)
