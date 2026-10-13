#!/usr/bin/env python
# coding: utf-8
# the imports

import sys
import serial
import serial.tools.list_ports
from time import sleep
from threading import Timer
import tkinter as tk
from tkinter import *
from PIL import ImageTk, Image
import random
import pygame

game_mode='multi' #'single' or 'multi'
game_over = False # flag to set when the game is over or not
count_down_n=3 # countdown before the game starts
step_size=10 # the steps of each player on the x axis
device_list = [] # keep a list of the connected devices
numOfPlayers=0
ser=None # serial port device
#player={device_name:{nickname,count,image,icon}}
player={}

# function to reset the game   
def reset():
    
    
    global game_over
    global player,numOfPlayers
    numOfPlayers=0
   
    player={}
    clearGrid()
    game_over=True
    device_list.clear()
    print('reset')
    canvas.delete('players') #clear canvas sprite with same tags
 
    label['text'] =  str(numOfPlayers)+ ' players'
    sleep(.1)
    print('reset')
    ser.flush()
    ser.write(b'reset\n')    
    ser.flush()


def win_close():
    if ser : ser.close()
    root.destroy()
    
def _win_close(event):
    exit_button.invoke()


def start_racing():
    global numOfPlayers
    global game_mode
    global game_over
    
    game_over=True
    
    if numOfPlayers==0 : 
        messagebox.showerror ("Error","No user! you need to connect to the device!")#提出错误对话窗
        return 
    
    if 'Computer' in device_list:  #for just restart game
        device_list.remove('Computer')
        numOfPlayers-=1
        
    game_mode='multi' if numOfPlayers > 1 else 'single' 
               
    if game_mode =='single': # against computer
        device_list.append('Computer')
        add_player('Computer') 
              
    init_player()   
    countdown(count_down_n)
    
# Countdown before the game starts
def countdown(count):
    global game_over

    label['text'] = count

    if count > 0: 
        counter_sound()      
        root.after(900, countdown, count-1)
    else:
        # change game over to False so the game can start
        game_over=False
        print('start running')

   
#################
# tkinter layout
root = tk.Tk()
root.title("micro:bit racing game")

# fullscreen
#root.geometry("800x600")
root.attributes('-fullscreen', True)
canvas = tk.Canvas(root)
canvas.pack(expand=YES, fill=BOTH)

#Grid.rowconfigure(root, 0, weight=1)
#Grid.columnconfigure(root, 0, weight=1)
canvas.update() # to get the full width and height of the canvas

# Frame for Players to add nickname choose picture and view their status
playersInfoFrame = tk.Frame(root, bg='#FA8072', bd=2)
playersInfoFrame.place(relx=0.01, rely=0.02, relwidth=0.12, relheight=0.2, anchor='nw')

Label(playersInfoFrame, text="name").grid(column=0, row=0,columnspan=2,sticky="nsew")
Label(playersInfoFrame, text="Image").grid(column=2, row=0,columnspan=2,sticky="nsew")
Label(playersInfoFrame, text="Status").grid(column=4, row=0,columnspan=2,sticky="nsew")

# List of images players can choose
IMAGES = [
    "image 1",
    "image 2",
    "image 3",
    "image 4"
]  


imgPath=[]  # list of  StringVar 
status=[]
pName=[] #list of device name
pPath=[]
tk_dev_name=[ StringVar() for i in range(4)]

for i in range(4):
   img1 = StringVar(root)
   img1.set(IMAGES[i])   # initialize the images
   imgPath.append(img1)   
   p1Path = OptionMenu(playersInfoFrame, img1, *IMAGES)
   img1.trace('w',lambda *args: update_sprite())
   status1 = Label(playersInfoFrame, background='green')   
   status.append(status1)
   p1Name = Entry(playersInfoFrame, width=5,textvariable=tk_dev_name[i])
   pName.append(p1Name)
   pPath.append(p1Path)

# tkinter frame
frame = tk.Frame(root, bg='green', bd=2)
frame.place(relx=0.5, rely=0.1, relwidth=0.3, relheight=0.1, anchor='n')

# button
button = tk.Button(frame, text="Start Race", font="Helvetica 25 bold", bg = "blue", foreground = "white",command=start_racing)
button.place(relx=0, rely=0,relwidth=1, relheight=1)

upper_frame = tk.Frame(root, bg='black', bd=5)
upper_frame.place(relx=0.5, rely=0.25, relwidth=0.65, relheight=0.20, anchor='n')
label = tk.Label(upper_frame,font = "Helvetica 50 bold italic")
label.place(relwidth=1, relheight=1)


# reset
reset_frame = tk.Frame(root, bg='white', bd=5)
reset_frame.place(relx=0.5, rely=0.9, relwidth=0.2, relheight=0.1, anchor='n')

reset_button = tk.Button(reset_frame, text="Reset",bd=5, font=40, bg = "red",foreground = "white",command=reset)
reset_button.place(relx=0, rely=0, relheight=1, relwidth=0.4)

exit_button = tk.Button(reset_frame, text="Exit", font=40, bd=5,bg = "black",foreground = "white",command=win_close)
exit_button.place(relx=0.5, rely=0, relheight=1, relwidth=0.4)
# welcome message to start
label['text'] = "Welcome"
###########################################


def open_serial(baudrate=115200):

    # open serial port
    ports = serial.tools.list_ports.comports(include_links=False)
    
    if len(ports)==0:
        print("Can not open serial port")
        messagebox.showerror ("Error","Can not open serial port")#提出错误对话窗
        win_close()
        sys.exit("Can not open serial port")
        
    device = ports[-1].device
    print('open serieal device:',device)
    ser_port = serial.Serial(device, baudrate, timeout=0)
    ser_port.flush()
    return ser_port

  
def preprocessData():
    ''' This function preprocesses the data received, checks the connected microbits
    and then call update_move() to get the race started when some conditions are met'''

    global game_over,numOfPlayers
    
    line = ser.readline().strip()
    wholeData = line.decode('ascii')
    name=''
    if wholeData:
        if ('_' in wholeData):
            name_steps_raw = wholeData.split('_')
            name = name_steps_raw[0]            
            # make sure a value is returned for steps instead of empty string
            step_count = 0 if name_steps_raw[1] == '' else name_steps_raw[1]
            player[name]['count']+=int(step_count)*step_size
            if (game_over == False):
                    update_move(name,int(step_count)*step_size,list(device_list))  

        else:
            name = wholeData
            step_count = 0   
            msg=name+'_'+'connect ok\n'
            ser.write(str(msg).encode('ascii')) # send signal for the players to move
            print(msg)          
            # add a new player in the list if the player is not already in
            device_list.append(name) if name not in device_list else device_list            
            add_player(name) 
 
            
            label['text'] = str(numOfPlayers)+ ' players'

        print('player',player)
        # move the players when game_over is false
    print(game_over,game_mode)
    if game_over == False and game_mode=='single' :
            step_count=int(random.randint(0,5))
            player['Computer']['count']+=step_count
            update_move('Computer',step_count,list(device_list))   
        
          
    Timer(0.2, preprocessData).start()

# In[ ]

def init_player():
    i=0
    for name in player:
        player[name]['count']=0
        canvas.coords(player[name]['icon'],player_starting_pos_x, player_starting_pos_y+playerStarting_y_delta*i)
        i+=1

    update_sprite()
    
def add_player(name):
    global numOfPlayers
    player[name]={'id':0,'nickname':'','count':0,'icon':None}   
    player[name]['id']=numOfPlayers     
    u1 = canvas.create_image(player_starting_pos_x, player_starting_pos_y+playerStarting_y_delta*numOfPlayers, image=None,tags='players')
    player[name]['icon']=u1
    numOfPlayers+=1
    updateGridForNumberOfPlayers(player[name]['id'])
    update_sprite()

# sound to play along with the counter
def counter_sound():
    pygame.mixer.init()
    pygame.mixer.music.load("audio/counter.mp3")
    pygame.mixer.music.play()

# sound to play when a player wins
def winning_sound():
    pygame.mixer.init()
    pygame.mixer.music.load("audio/win.mp3")
    pygame.mixer.music.play()

# function to clear the grid (name, path, status) on reset 
def clearGrid():
    
    for i in range(4):
        pName[i].grid_forget()
        pPath[i].grid_forget()
        status[i].grid_forget()

# function to update the grid 
# (Ex: if there is only one player, the grid will show only this player's grid)

def updateGridForNumberOfPlayers(n_user):
        
    #for i in range(4):
        i=n_user        
        pName[i].grid(row=i+1, column=0,columnspan=2, sticky=W+E+S+N)
        pPath[i].grid(row=i+1, column=2,columnspan=2, sticky=W+E+S+N)
        status[i].grid(column=4, row=i+1,columnspan=2, sticky=W+E+S+N)
        tk_dev_name[i].set(device_list[i])

        
# In[ ]: 

# proportional goal, starting y, starting x, player height and width
# track height, distance between the players on the y axis
player_width = int(canvas.winfo_width()*0.04)
player_height = int(canvas.winfo_width()*0.05)
goal = canvas.winfo_width()*0.85
print(goal)
track_height = int(canvas.winfo_height()*0.4)
player_starting_pos_x = int(canvas.winfo_width()*0.05)
player_starting_pos_y = int(canvas.winfo_height()*0.57)
playerStarting_y_delta = int(canvas.winfo_height()*0.08)

track_resize = Image.open(r"images/race_track.jpg").resize((canvas.winfo_width(), track_height), Image.ANTIALIAS)
track = ImageTk.PhotoImage(track_resize)
canvas.create_image(int(canvas.winfo_width()/2), int(canvas.winfo_height()*0.7), image=track)

# function to transform the user choice into image link
def chooseImage(userChoice):
    if userChoice == "image 1":
        return "images/run1.png"
    elif userChoice == "image 2":
        return "images/run2.gif"
    elif userChoice == "image 3":
        return "images/run3.png"
    elif userChoice == "image 4":
        return "images/run4.png"
  
sprite_list=[]
# In[ ]:    
def update_sprite():
    '''
    1. This function returns namePathList which is a list of lists
    containing the names and image paths of each players

    2. This function also update the canvas proportional to the number of
    players detected (Ex: if only two players are detected, only these two will be shown)
    '''
    print(player)

    namePathList = [[pName[i].get(), imgPath[i].get()] for i in range(4)]
    sprite_list.clear() # don't use =[], should keep the image at the same memory location

    # Show canvas proportional to the number of players online
    
    for i,name in enumerate(player): 
        icon_path=chooseImage(namePathList[i][1])
        s1= Image.open(icon_path).resize((player_width, player_height), Image.ANTIALIAS )
        sprite_list.append(ImageTk.PhotoImage(s1))
        canvas.itemconfig(player[name]['icon'], image=sprite_list[i]) 
        canvas.itemconfigure(player[name]['icon'], state='normal')  
        

    return namePathList  

# button to confirm the number of players, their names and images
#confirmButton = tk.Button(playersInfoFrame, text="Apply", font=60, bg = "blue", foreground = "white", command=update_sprite)
#confirmButton.place(relx=0, rely=0.8, relheight=0.2, relwidth=1)

# In[ ]:
# get the players moving
def update_move(name,step,device_list):

   # upon receiving the data, update the players' position
    # each step is multiplied by the step_size to make the player's movement faster
    global game_over

    info=""
    
    
    for idx,user in enumerate(device_list):  
        n=player[user]['count']
        info+=str(n)+','
        if name == device_list[idx]: 
            #moves forward
            canvas.move(player[user]['icon'],step, 0)           
      
        if n >= goal: 
                winner=user
                game_over=True
                break
        
    if game_over==True: 
        text = winner +" wins!"
        label['text'] = text
        winning_sound()
        message = winner + '_' + 'finish'                  
        ser.write(str(message).encode('ascii'))
        ser.write(b'\n')         
    else:
        label['text']=info[:-1]  #remove last character ','

# In[ ]:

if __name__=='__main__':
    
    
    ser=open_serial(baudrate=115200)

    update_sprite()
    #add_playersInfo()
    root.bind('<Escape>',_win_close)
    root.protocol("WM_DELETE_WINDOW", win_close)
    
    #use <F11> to switch Fullscreen mode
    root.bind("<F11>", lambda event: root.attributes("-fullscreen",
                         not root.attributes("-fullscreen")))
    preprocessData()
    root.mainloop()






