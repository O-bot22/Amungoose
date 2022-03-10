import sys
import socket
import rays
import pygame
from pygame.locals import *
import threading
import multiprocessing
import random
import time as timme
#used to get external IP
import urllib.request
#not worth it, I couldnt get it to work, and I dont care that much
# from shapely.geometry import Point
# from shapely.geometry.polygon import Polygon

status = input("Whould you like to join or host a game?['j'/'h'] ")
# status = "h"

def dist(a,b):
    return ((b[0]-a[0])**2+(b[1]-a[1])**2)**0.5
pygame.font.init()
def make_text(text,position,dis,color=(0,0,0),fonty=pygame.font.SysFont('Comic Sans MS', 60, False, False)):
    dis.blit(fonty.render(text, False, color),(position))
def wallagon(points):
    out = []
    oldPoint = points[0]
    for i in points[1:]:
        out.append(rays.Wall(oldPoint,i))
        # out.append(rays.Wall_vector(oldPoint,i[0]-oldPoint[0],i[1]-oldPoint[1]))
        #print(oldPoint,i)
        oldPoint = i
    # print(out[0].a,out[0].b)
    # print(out[-1].a,out[-1].b)
    return out
class Player():
    def __init__(self,id):
        self.id = id
        self.pos = (250,250)
        self.avatar = avatars[id]
        self.is_dead = False
        self.reported = False
        self.deadAvatar = deadAvatars[id]
        self.enemies = [] #people who voted for me
    def move(self,x,y):
        self.pos[0]+=x
        self.pos[1]+=y
    def getMove(self, dp):
        x,y = 0,0
        keyboard = pygame.key.get_pressed()
        if keyboard[K_UP] or keyboard[K_w]:
            d = rays.dist([250,250],point.cast_offset(map.walls)[2])
            #if distance too close, set player back
            if 0<d and d<=10 or dp>=d: #if the wall above is currently too close or will be too close
                # print("0 < "+str(d)+" < 10")
                y=d-10#back it up
            else:
                y=dp#carry on
        if keyboard[K_DOWN] or keyboard[K_s]:
            d = rays.dist([250,250],point.cast_offset(map.walls)[0])
            if (0<d and d<=30) or dp>=d: #if the wall below is too close or will be too close
                y=30-d
            else:
                y=-dp
        if keyboard[K_RIGHT] or keyboard[K_d]:
            d = rays.dist([250,250],point.cast_offset(map.walls)[1])
            if 0<d and d<=15 or dp>=d: #if the wall to right is too close or will be too close
                x=15-d
            else:
                x=-dp
        if keyboard[K_LEFT] or keyboard[K_a]:
            d = rays.dist([250,250],point.cast_offset(map.walls)[3])
            if 0<d and d<=10 or dp>=d: #if the wall to left is too close or will be too close
                x=d-10
            else:
                x=dp
        return int(-x),int(-y)
    def drawRel(self,pos):
        pos = [int(pos[0]),int(pos[1])]
        rp = [self.pos[0]+250-pos[0], self.pos[1]+250-pos[1]]
        # if pygame.key.get_pressed()[pygame.K_SPACE]:
        #     print(self.id)
        #     print(self.pos)
        #     print(pos)
        #     print("="+str(rp))
        if self.is_dead:
            SCREEN.blit(self.deadAvatar, rp)
        else:
            SCREEN.blit(self.avatar, rp)
        # print("draw: "+str([self.pos[0]+250-pos[0],self.pos[1]+250-pos[1]]))
    def draw(self):
        SCREEN.blit(self.avatar, (200,200))
class Wire():
    def __init__(self, strt, end):
        self.n = strt
        colors = [(255,0,0),(0,255,0),(0,0,255),(255,255,0)]
        self.color = colors[strt]
        # self.startPos = [150,150+50*strt]
        self.startRect = pygame.Rect(150,150+50*strt, 20,20)
        self.endRect = pygame.Rect(350,150+50*end, 20,20)
        self.pos = []
        self.selected = False
        self.bounce = False
        self.done = False
    def do(self):
        global taskbar
        if self.done:
            pygame.draw.line(SCREEN, self.color, [self.startRect.x,self.startRect.y], self.pos, 10)
        elif pygame.mouse.get_pressed()[0]:
            if self.selected:
                self.bounce = True
                self.pos = pygame.mouse.get_pos()
                pygame.draw.line(SCREEN, self.color, [self.startRect.x,self.startRect.y], self.pos, 10)
            else:#if this has never been touched
                self.selected = self.startRect.collidepoint(pygame.mouse.get_pos())
        elif self.bounce:
            # print("released")
            self.done = self.endRect.collidepoint(self.pos)
            self.selected = False
            self.bounce = False
        else:
            self.selected = False
        pygame.draw.rect(SCREEN, self.color, self.startRect)
        pygame.draw.rect(SCREEN, self.color, self.endRect)
def shuffle(deck):
    out = []
    d = deck
    for i in range(len(deck)):
        s = random.randint(0,len(d)-1)
        out.append(d[s])
        d.pop(s)
    return out
class WireBox():
    def __init__(self, pos):
        # self.img = pygame.image.load("images/wires.png")
        self.rect = pygame.Rect(pos,(40,30))
        #owen,what is a xRect?
        self.xRect = pygame.Rect(400,100,50,50)
        self.is_activated = False
        self.wires = []
        self.done = False
        self.assigned = False
        r = shuffle([0,1,2,3])
        rr = shuffle([0,1,2,3])
        for i in range(4):
            self.wires.append(Wire(rr[i],r[i]))
    def move(self, x,y):
        # self.rect.x+=x
        # self.rect.y+=y
        self.rect.move(x,y)
    def do(self):
        global visible
        if self.is_activated:#show task screen
            visible = False
            pygame.draw.rect(SCREEN, (200,200,200), pygame.Rect(100,100, 300,300))
            pygame.draw.rect(SCREEN, (200,0,0), self.xRect)
            f = True
            for i in self.wires:
                i.do()
                f = f and i.done #if they are all done
            self.done = f
            if self.done:
                self.is_activated = False
            if pygame.mouse.get_pressed()[0]:
                self.is_activated = not self.xRect.collidepoint(pygame.mouse.get_pos())
                if self.is_activated:
                    visible = False
        else:#draw like on map
            # print(self.pos)
            visible = True
            if not self.done:
                pygame.draw.rect(SCREEN, (255,255,0), self.rect.inflate(6,6))
            pygame.draw.rect(SCREEN, (0,50,100), self.rect)
            if pygame.mouse.get_pressed()[0]:
                #still opens if in another task, but maybe that is ok
                self.is_activated = self.rect.collidepoint(pygame.mouse.get_pos())
    def draw_screen(self):
        global visible
        if self.is_activated:#show task screen
            visible = False
            pygame.draw.rect(SCREEN, (200,200,200), pygame.Rect(100,100, 300,300))
            pygame.draw.rect(SCREEN, (200,0,0), self.xRect)
            f = True
            for i in self.wires:
                i.do()
                f = f and i.done #if they are all done
            self.done = f
            if self.done:
                self.is_activated = False
            if pygame.mouse.get_pressed()[0]:
                self.is_activated = not self.xRect.collidepoint(pygame.mouse.get_pos())
                if self.is_activated:
                    visible = False
    def draw_icon(self,offset):
        global visible
        if not(self.is_activated):#draw like on map
            # print(self.pos)
            visible = True
            self.rel_rect = self.rect.move(self.rect.x-offset[0],self.rect.y-offset[1])
            if not self.done:
                pygame.draw.rect(SCREEN, (255,255,0), self.rel_rect.inflate(6,6))
            pygame.draw.rect(SCREEN, (0,50,100), self.rel_rect)
            if pygame.mouse.get_pressed()[0]:
                #still opens if in another task, but maybe that is ok
                self.is_activated = self.rel_rect.collidepoint(pygame.mouse.get_pos())
class Map():
    def __init__(self,walls,floor,tasks,grafix):
        # self.walls_og = walls
        self.walls = walls
        self.floor = floor
        self.tasks = tasks
        # print(grafix)
        self.point = rays.Point((250,250),grafix)
        self.pos = [0,0]
        self.polygon = -1
    def move(self,x,y):
        '''for i in self.walls:
            i.a[0]+=x
            i.a[1]+=y
            i.b[0]+=x
            i.b[1]+=y
        for i in self.tasks:
            i.move(x,y)'''
        self.floor = self.floor.move(x,y)
        # for i in self.tasks:
        #     i.rect = i.rect.move(x,y)
    def move_to(self,pos):
        pos = [int(pos[0]),int(pos[1])]
        # if pygame.key.get_pressed()[pygame.K_SPACE]:
        #     print("pos alter to Map in move_to:"+str(pos))
        self.pos = pos #use your illusion
        # old- I know that it is still relative, but the walls are built to be, and ?
        '''if self.pos!=pos:
            dx = self.pos[0]-pos[0]
            dy = self.pos[1]-pos[1]
            # print("change detected")
            if pygame.key.get_pressed()[pygame.K_SPACE]:
                print(dx,dy)
            for i in self.walls:
                i.a[0]+=dx
                i.a[1]+=dy
                i.b[0]+=dx
                i.b[1]+=dy
            for i in self.tasks:
                i.move(x,y)
            self.pos = pos'''
        '''#make a copy
        self.walls = self.walls_og[0:]
        #move the copy
        for i in self.walls:
            i.a[0]+=pos[0]
            i.a[1]+=pos[1]
            i.b[0]+=pos[0]
            i.b[1]+=pos[1]'''
        '''for i in self.walls:
            i.pos = pos
            i.updateAB()
        # self.walls[-1].pos = pos
        # self.walls[-1].updateAB()
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            print(self.walls[-1].pos)
            print(self.walls[-1].a,self.walls[-1].b)'''
    def draw(self):
        pygame.draw.rect(SCREEN, (50,50,50), self.floor)
        for i in self.walls:
            # i.show(SCREEN,(0,0,0))
            i.show_off(SCREEN,self.pos,(0,0,0))
        for i in self.tasks:
            i.draw_icon(self.pos)
    def calc_shade(self):
        #ray cast walls and get points
        points = self.point.cast_offset(self.walls)
        #make polygon of points
        poly_surf = pygame.Surface((500,500))
        poly = pygame.draw.polygon(poly_surf,(255,255,255),points)
        #make a polygon in the shapely class
        # print(points)
        # self.polygon = Polygon(points)
        #used to determine which pixles are 1 or 0 in mask
        poly_surf.set_colorkey((0,0,0))
        #create mask of field of view
        poly_mask = pygame.mask.from_surface(poly_surf)
        #maybe intersect with circle to create limit visibility
        #also intersect with tasks to see if they are viewable, and therefore clickable
        #create black bg
        bg = pygame.Surface((500,500))
        #draw whit pixles of fied of view to the baclground
        poly_mask.to_surface(bg)
        #convert white pixles to alhpa when blitting
        bg.set_colorkey((255,255,255))
        #display background
        self.bg = bg
    # def test_shade(self, point):
    #     p = [point[0]-self.pos[0]+250,point[1]-self.pos[1]+250]
    #     print(p)
    #     try:
    #         return self.polygon.contains(p)
    #     except AttributeError:
    #         return False
    def draw_shade(self):
        SCREEN.blit(self.bg,(0,0))
    def draw_tasks(self):
        for i in self.tasks:
            i.draw_screen()
    def getCompletedTasks(self):
        t = 0
        for i in self.tasks:
            if i.done and not i.assigned:
                t+=1
        return t

loopLock = threading.Lock()
loop = True
def getLoop():
    global loop
    loopLock.acquire()
    try:
        localRequest = loop==True
    finally:
        loopLock.release()
    return localRequest
def setLoop(x):
    global loop
    loopLock.acquire()
    try:
        loop = x
    finally:
        loopLock.release()

sharedList = {'loop':True, 'reporter':-1, 'voteCount':0, 'winner':-1, 'taskbar':0, 'start':False}
sharedListLock = threading.Lock()
def getsharedList(attribute):
    global sharedList
    sharedListLock.acquire()
    try:
        locala = sharedList[attribute]
    finally:
        sharedListLock.release()
    return locala
def setsharedList(attribute,value):
    global sharedList
    sharedListLock.acquire()
    try:
        sharedList[attribute] = value
    finally:
        sharedListLock.release()
def incrementSharedList(attribute, a):
    # adds value a to the attribute
    global sharedList
    sharedListLock.acquire()
    try:
        sharedList[attribute] += a
    finally:
        sharedListLock.release()

#on server<-client
#send info from client as server->othe r clients
#is called as a thread for each client
def serverListener(sockets,idnum,p,sendRequest, imposterN, tasksk): # listens to a client's movements
    #do stuff talking to client
    # global sendRequest
    global dead
    global enemies
    global bodyCount
    mySock = sockets[idnum]
    msg = str(idnum)+"{"+str(imposterN)+'{'
    for i in tasksk:
        msg+=str(i)+','
    # print(msg)
    msg = msg[:-1]
    # print("sent "+msg)
    mySock.send(bytes(msg, 'utf-8'))
    # print(mySock.recv(1024).decode('utf-8'))
    while getLoop():
        try:
            msg = mySock.recv(1024).decode('utf-8')
            # print("server recived '"+msg+"' from player #"+str(idnum))
            typeCode = msg[1:2]
            if typeCode=="p":
                msg = msg.split(",")
                try:
                    x = int(msg[0][3:])
                    y = int(msg[1][:-1])
                except ValueError:
                    x = 0
                    y = 0
                p.pos = [x-10,y-10]
                msg = str(x)+","+str(y)+"}"
                for i in range(len(sockets)):
                    if i!=idnum:#for all the client players, exluding the one this is talking to,
                        msg = "{p-"+str(idnum)+":"+msg #send the position and id of the player that we just learned moved
                        sockets[i].send(bytes(msg,'utf-8'))
                        # print("server sent '"+msg+"' to player #"+str(i))
            elif typeCode=='k':
                id = int(msg[3])
                # print("recieved that player #"+str(id)+" was killed")
                if id==playerCount-1:
                    print("You were killed")
                    dead = True
                else:
                    players[id].is_dead = True
                bodyCount+=1
                for i in range(len(sockets)):
                    if i!=idnum:
                        sockets[i].send(bytes(msg,'utf-8')) #pass the sad news along. I dont even have to reformat it
                if bodyCount==playerCount-1:#if no one is left, or even right
                    print("imposter won")
                    setsharedList('winner', playerCount-1)
            elif typeCode=='r':
                reporter = int(msg[3])
                ded = int(msg[5])
                # print("recived that player #"+str(reporter)+" reported player #"+str(ded))
                # setv(reporter)
                setsharedList('reporter',reporter)
                if ded != len(players):#we already know that we are dead, but we arent in the list of players cuz owen broken
                    players[ded].is_dead = True
                #tell pygame thread to do meeting
                for i in range(len(sockets)):
                    if i!=idnum:
                        sockets[i].send(bytes(msg,'utf-8')) #pass the sad news along. I dont even have to reformat it
            elif typeCode=='v':
                accuser = int(msg[3])
                accused = int(msg[5])
                # print("recieved that player #"+str(accuser)+" accused #"+str(accused))
                if accused == len(players):
                    enemies.append(accuser)
                else:
                    players[accused].enemies.append(accuser)
                incrementSharedList('voteCount', 1)
                for i in range(len(sockets)):
                    if i!=idnum:
                        sockets[i].send(bytes(msg,'utf-8')) #pass the news along. I dont even have to reformat it
            elif typeCode=='t':
                # print("recieved taskbar update from #"+str(idnum))
                incrementSharedList('taskbar',1)
                for i in range(len(sockets)):
                    # if i!=idnum:
                    sockets[i].send(bytes(msg,'utf-8')) #pass the news along. I dont even have to reformat it
                        # print("send it to #"+str(idnum))
                    # else:
                        # print("Dont send it to #"+str(idnum))
                # print(" ")
        except ConnectionAbortedError:
            print("you lost connection(abort error)")
            setLoop(False)
        except ConnectionResetError:
            if getLoop():
                print("player #"+str(idnum)+" left the game")
                # print("either the player lost connection(quit, or lost wifi) or you lost wifi")
                setLoop(False)
            # else:
                #the game ended

def getRequest():
    global sendRequest
    requestLock.acquire()
    try:
        localRequest = sendRequest
    finally:
        requestLock.release()
    # print("the request was retrived")
    # timme.sleep(1)
    return localRequest
def setRequest(x):
    global sendRequest
    requestLock.acquire()
    try:
        sendRequest = x
    finally:
        requestLock.release()
    # print("the request was set")
#server->clients
def hostSender(socks):
    global loop
    # global sendRequest
    localRequest = ""
    while getLoop():
        localRequest = getRequest()
        if localRequest!="":
            for i in range(len(sockets)):#for all the client players
                sockets[i].send(bytes(localRequest,'utf-8'))
                # print("server sent '"+localRequest+"' to player #"+str(i)+" from the hostSender thread")
            # print("thing")
            setRequest("")
            # print(localRequest)

#client<-server
def clientListener():
    global players
    global s
    global idnum
    global imposter
    global avatar
    global dead
    global bodyCount
    global imposterNum
    global myTasks
    try:
        #why did I use 10?
        msg = s.recv(50).decode('utf-8')
    except OSError:
        print("could not find game")
    # print(msg)
    msg = msg.split('{')
    # print(msg)
    idnum = int(msg[0])
    avatar = avatars[idnum]
    deadAvatar = deadAvatars[idnum]
    imposterNum = int(msg[1])
    if imposterNum==idnum:
        print("You are the imposter")
        imposter = True
    else:
        print("You are a crewmate")
        imposter = False
    tsks = msg[2].split(',')
    # print(tsks)
    for i in tsks:
        myTasks.append(int(i))
    # print(myTasks)
    for i in range(len(map.tasks)):
        if not i in myTasks:
            map.tasks[i].done = True #deactivate all the tasks that arent theirs
            map.tasks[i].assigned = True #assign the task
    s.send(bytes("ID transmitted sucessfully",'utf-8'))
    #{code-id:x,y},{code-id:x,y}...
    while getLoop():
        try:
            msg = s.recv(1024).decode('utf-8') 
            # print("client recived "+msg)
            for i in msg.split('}'):
                if i!='':
                    typeCode = i[1:2]
                    # print(msg)
                    if typeCode=="p":
                        i = i.split(':')
                        # print(i)
                        # print(i[0]) 
                        id = int(i[0][3:])#first part but skip {p-
                        # print(id)
                        x,y = i[1].split(',')
                        x = int(x)
                        y = int(y)#cut off }
                        # print(id,x,y)
                        #the first time this happens, before the game starts, the original 250,250 is being read as 50,250, butonly for the host. maybe because I messed up the id and imposter thing above
                        players[id].pos = [x-10,y-10]
                        # print(players[id].pos)
                    elif typeCode=="k":
                        id = int(i[3])
                        # print("recievd that player #"+str(id)+" was killed")
                        if id==idnum:
                            print("You were killed")
                            dead = True
                        else:
                            players[id].is_dead = True
                        bodyCount+=1
                        if bodyCount==playerCount-1:
                            print("imposter won")
                            setsharedList('winner', playerCount-1)
                    elif typeCode=="r":
                        reporter = int(i[3])
                        ded = int(i[5])
                        # print("recived that player #"+str(reporter)+" reported player #"+str(ded))
                        #tell pygame thread to do meeting
                        # setv(reporter)
                        setsharedList('reporter',reporter)
                        players[ded].is_dead = True
                    elif typeCode=='v':
                        voter = int(i[3])
                        accused = int(i[5])
                        # print("recieved that player #"+str(voter)+" voted for player #"+str(accused))
                        players[accused].enemies.append(voter)
                        vc = getsharedList('voteCount')
                        incrementSharedList('voteCount', 1)
                        # print("set the voteCount to "+str(vc+1))
                    elif typeCode=='t':
                        # print("recieved taskbar update")
                        #he is recieving his own taskbar update. whY?????
                        incrementSharedList('taskbar',1)
                    elif typeCode=='w':
                        winner = int(i[3:])
                        # print(winner)
                        if winner==100:
                            print("crewmates won!")
                        else:
                            print("player #"+str(winner)+" won!")
                        setsharedList('winner',winner)
                    elif typeCode=='s':
                        setsharedList('start',True)
        except ConnectionResetError:
            print("host has disconnected")
            setLoop(False)
        except ConnectionAbortedError:
            print("you or the host has lost wifi")
            setLoop(False)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
playerCount = 3
killDistance = 50
cooldownMax = 5000
cooldown = cooldownMax
imposter = False
gameScope = 'local'
# while True:
#     try:
#         playerCount = int(input("How many players?[5-10] "))
#         break
#     except ValueError:
#         print("please try again")
grafix = 10
# while True:
#     try:
#         grafix = int(input("Shadow graphics quality?[1-10] "))
#         break
#     except ValueError:
#         print("please try again")
sendRequest = ""
pygame.init()
SCREEN = pygame.display.set_mode((500,500), pygame.HWSURFACE)
SCREEN.fill((50,0,100))
make_text("Waiting for players to connect...",[0,0],SCREEN,(255,255,255),pygame.font.SysFont('Comic Sans MS', 45, False, False))
pygame.display.update()
clock = pygame.time.Clock()
time = 0
#red,orange,yellow,green,blue,purple,black,brown,pink,cyan
avatars = [pygame.image.load("images/dude0.png").convert_alpha(), pygame.image.load("images/dude1.png").convert_alpha(),
    pygame.image.load("images/dude2.png").convert_alpha(), pygame.image.load("images/dude3.png").convert_alpha(),
    pygame.image.load("images/dude4.png").convert_alpha(), pygame.image.load("images/dude5.png").convert_alpha(),
    pygame.image.load("images/dude6.png").convert_alpha(), pygame.image.load("images/dude7.png").convert_alpha(),
    pygame.image.load("images/dude8.png").convert_alpha(), pygame.image.load("images/dude9.png").convert_alpha()]
avatar = avatars[0]
deadAvatars = [pygame.image.load("images/dead0.png").convert_alpha(), pygame.image.load("images/dead1.png").convert_alpha(),
    pygame.image.load("images/dead2.png").convert_alpha(), pygame.image.load("images/dead3.png").convert_alpha(),
    pygame.image.load("images/dead4.png").convert_alpha(), pygame.image.load("images/dead5.png").convert_alpha(),
    pygame.image.load("images/dead6.png").convert_alpha(), pygame.image.load("images/dead7.png").convert_alpha(),
    pygame.image.load("images/dead8.png").convert_alpha(), pygame.image.load("images/dead9.png").convert_alpha()]
deadAvatar = deadAvatars[0]
colors = [(255,0,0),(255,100,0),(255,255,0),(0,255,0),(0,0,255),(150,0,255),(0,0,0),(0,50,0),(255,50,255),(50,255,255)]
skull = pygame.image.load("images/skull+bones.png").convert_alpha()
check = pygame.image.load("images/check.png").convert_alpha()
floor = pygame.Rect(-100,-100,700,700)
                        #main room
# w = wallagon([[0,0],[100,100],[0,100]])
maps = {
        "spaceship":Map([rays.Wall([-100,-100],[-100,600]),rays.Wall([-100,-100],[600,-100]),rays.Wall([-100,600],[600,600]),rays.Wall([600,300],[600,400]),
                        #bottom right
                        rays.Wall([600,600],[1000,600]),rays.Wall([1000,600],[1000,400]),rays.Wall([1000,400],[600,400]),
                        #top left
                        rays.Wall([600,-100],[1000,-100]),rays.Wall([1000,-100],[1200,-100]),rays.Wall([1200,-100],[1200,200]),rays.Wall([1200,200],[1000,300]),rays.Wall([1000,300],[600,300])
                        ],
                        floor, 
                        [WireBox([200,200]), WireBox([400,200]), WireBox([200,400]), WireBox([100,100])],
                        grafix
                    ),
        "spaceship2":Map(
                        #*fixed something with the first and last lines make them move all whack-like
                        wallagon([[-450,50],[-450,100],[-350,100],[-350,200],[-600,200],[-600,300],[-100,300],[-100,200],[-250,200],[-250,100],[0,100],[0,450],[-100,450],[-100,400],[-300,400],[-300,600],[-100,600],[-100,500],[500,500],[500,700],[350,700],[350,850],[600,850],[600,500],[850,500],[850,300],[600,300],[600,400],[500,400],[500,200],[500,250],[700,250],[700,150],[500,150],[500,50],[-450,50]]),
                        pygame.Rect(0,0,0,0),
                        #I think the map is double sized after I did the update to absolute movement
                        [WireBox([-450,50]), WireBox([-600,200]), WireBox([-220,200]), WireBox([0,300]), WireBox([-120,400]), WireBox([-300,400]), WireBox([-120,585]), WireBox([350,700]), WireBox([600,300]), WireBox([830,300]), WireBox([500,220])],
                        (grafix*5+4)
                    ),
        "test":Map(
            wallagon([[250,100],[400,250],[250,400],[100,250],[250,100]]),
            # [
            # rays.Wall([250,100],[400,250]),rays.Wall([400,250],[250,400]),rays.Wall([250,400],[100,250]),rays.Wall([100,250],[250,100]),
            # rays.Wall_vector([100,100],0,200)
            # ],
            pygame.Rect(0,0,0,0),
            [WireBox([400,400])],
            10
        )
        }
map = maps["spaceship2"]
mapChange = True
myTasks = []
# taskbar = 0
oldTaskbar = 0
myOldTasks = 0
myCompletedTasks = 0
speed = 1
taskWidth = 460/len(map.tasks)

if status == "h":
    # gameScope = input("Local(same wifi) or Public Game(across interweb, must be port forawrded)?[local/public] ")
    gameScope = 'local'
    if gameScope=='public':
        myIp = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    else:
        myIp = socket.gethostbyname(socket.gethostname())
    print("The game code is: "+myIp)
    
    s.bind((myIp, 1234))#prep the socket to listen for requests to myIp
    s.listen(playerCount)
    #run threads
    threads = []
    players = []
    sockets = []
    avatar = avatars[(playerCount-1)]
    deadAvatar = deadAvatars[(playerCount-1)]
    imposterNum = random.randint(0,playerCount-1)
    if imposterNum==playerCount-1:
        print("You are the imposter")
        imposter = True
    else:
        print("You are a crewmate")
        imposter = False
    i = 0
    assignedTasks = []#shuffle(range(len(map.tasks)))
    for i in range(len(map.tasks)):
        assignedTasks.append(i)
    assignedTasks = shuffle(assignedTasks)
    #print(assignedTasks)
    #this would work,but it does that weird thing where one element in the list is the same memory location as the others
    playerAssignments = []
    i=0
    for i in range(playerCount):
        playerAssignments.append([-1])
    #print(playerAssignments)
    for i in range(len(assignedTasks)):
        p = i%playerCount #keep rolling over to assign tasks to first person, only problem is that first person connected will always have most tasks, but only 1 more. this is fixed by shuffling the assingmenets after
        if playerAssignments[p][0]==-1:  # the first time,
            playerAssignments[p][0] = assignedTasks[i] # just assign it
        else:#otherwise
            playerAssignments[p].append(assignedTasks[i])#add the index # of the task from the shuffled list of them
    playerAssignments = shuffle(playerAssignments)#make sure it isn't always the first players with more tasks
    # print(playerAssignments)
    myTasks = playerAssignments[-1]
    for i in range(len(map.tasks)):
        if not i in myTasks:
            map.tasks[i].done = True #deactivate all the tasks that arent mine
            map.tasks[i].assigned = True
    i=0
    while len(threads)<playerCount-1:
        socketbuf, addr = s.accept()
        sockets.append(socketbuf)
        # print("connection made with "+str(addr[0])+" "+str(addr[1]))
        print("Someone joined")
        players.append(Player(i))
        # print(i)
        # print(imposterNum)
        # print(playerAssignments[i])
        threads.append(threading.Thread(target = serverListener, args = (sockets,i,players[i],sendRequest,imposterNum,playerAssignments[i])))
        # print(threads)
        threads[i].daemon = True
        threads[i].start()
        i+=1
    requestLock = threading.Lock()
    townCryer = threading.Thread(target = hostSender, args=(sockets,))
    townCryer.start()
    print("all players have connected")
    #send start signal
    setRequest("{s")
else:
    SCREEN.fill((50,0,100))
    make_text("Enter game code...",[0,0],SCREEN,(255,255,255),pygame.font.SysFont('Comic Sans MS', 45, False, False))
    pygame.display.update()
    try:
        # s.connect((input("Game Code :"), 1234))
        s.connect(("192.168.1.55", 1234))
    except ConnectionRefusedError:
        print("could not connect")
        setLoop(False)
    except TimeoutError:
        print("host took too long to respond. This could be slow wifi")
        setLoop(False)
    except OSError:
        print("could not find game")
        setLoop(False)
    players = []
    for i in range(playerCount):
        players.append(Player(i))

SCREEN.fill((50,0,100))
make_text("Waiting for players...",[0,0],SCREEN,(255,255,255),pygame.font.SysFont('Comic Sans MS', 30, False, False))
pygame.display.update()

idnum = 0
visible = True
dead = False
bodyCount = 0
enemies = []
pos = [250,250]
old_pos = [0,0]
point = rays.Point([250,250],4)
player = Player(-1)
winner = -1
killBut = pygame.Rect(400,400,100,100)
reportBut = pygame.Rect(0,400,100,100)

if status == "j":
    pygame.display.set_caption("Among Us")
    listener = threading.Thread(target = clientListener)
    #I finally figured it out to use this, as it will make sure it dies when the main program does
    listener.daemon = True
    listener.start()
    # listener = multiprocessing.Process(target=clientListener) 
    # listener.start() that didnt work
    #wait for everyone to load in
    while True:
        timme.sleep(0.1)
        if getsharedList("start"):
            break
        for event in pygame.event.get():
            if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE]:
                setLoop(False)
        pygame.display.update()
    while loop:
        time_interval = clock.tick(60)
        time+=time_interval
        dp = int(time_interval/2)
        if dp>10:#the point of the timing thing is to not do this, but since the real, not absolute position is sent, it don matter 2 much cuz it won "drift away"-doobie gray
            dp = 10
        # time_interval = int(120/time_interval)
        SCREEN.fill((255,255,255))
        map.draw()
        for i in players:
            if i.id!=idnum:
                i.drawRel(pos)
                # i.draw()
        if mapChange:#most epicest optimization, no joke it cuts ping  in half
            mapChange = False
            map.calc_shade()
        map.draw_shade()
        map.draw_tasks()
        # task bar
        pygame.draw.rect(SCREEN, (150,150,150), pygame.Rect(20,20,460,40))
        if map.getCompletedTasks()>myOldTasks:
            # print("I have completed "+str(map.getCompletedTasks())+" tasks")
            myOldTasks += 1 # keep my tasks seperate from the group's
            incrementSharedList('taskbar',1)
            s.send(bytes('{t','utf-8'))
            # print("send {t")
        tb = getsharedList('taskbar')
        if tb!=oldTaskbar:
            oldTaskbar = tb
            # print(str(oldTaskbar)+" tasks have been completed")
            #I somehow doule count my own tasks, but not on host, maybe the socket message is sent back, so I substract it here
        pygame.draw.rect(SCREEN, (0,150,0), pygame.Rect(20,20,(oldTaskbar-myOldTasks)*taskWidth,40))
        if visible:
            #voting
            lv = getsharedList('reporter')
            if lv!=-1:
                l = True
                i_have_voted = False
                # print("start voting loop")
                while l:
                    # print('hello')
                    pygame.draw.rect(SCREEN, (150,150,255), pygame.Rect(60,60,380,380))
                    mPos = pygame.mouse.get_pos()
                    pres = pygame.mouse.get_pressed()[0]
                    # print("goodbye")
                    for i in range(playerCount):
                        # print("counting players")
                        x = i%2
                        y = int(i/2)
                        r = pygame.Rect(x*180+80,y*60+60,160,50)
                        if players[i].is_dead:
                            pygame.draw.rect(SCREEN, (100,0,0), r)
                            SCREEN.blit(avatars[i], (x*180+90,y*60+65))
                        else:
                            if i==lv:
                                pygame.draw.rect(SCREEN, (0,100,0), r)
                            else:
                                pygame.draw.rect(SCREEN, (255,255,255), r)
                            SCREEN.blit(avatars[i], (x*180+90,y*60+65))
                            if pres and not i_have_voted and not dead:#if that player is not dead, i havent voted, and mouse pressed, and I am not dead
                                if r.collidepoint(mPos):
                                    print("You voted for #"+str(i))
                                    s.send(bytes("{v-"+str(idnum)+":"+str(i)+"}", 'utf-8'))#send that I voted for i
                                    players[i].enemies.append(idnum)
                                    i_have_voted = True
                                    incrementSharedList('voteCount', 1)
                    if i_have_voted:
                        SCREEN.blit(check, (60,420))
                    if getsharedList('voteCount')==playerCount-bodyCount: # if we have all the votes from living pesronpeoples
                        l = False
                        setsharedList('reporter',-1)
                        for i in players:
                            i.reported = i.is_dead #dont let people report bodies that werent found before the meeting
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE]:
                            setLoop(False)
                            l = False
                            pygame.quit()
                    try:
                        pygame.display.update()
                    except pygame.error:
                        print("you closed the game")
                    # if getLoop():
                    #     pygame.quit()
                    #     l = False
                # print("display votes")
                mostVotes = -1
                mostVoted = -1
                tie = False
                for i in range(len(players)):
                    x = i%2
                    y = int(i/2)
                    # print("player "+str(i)+" had enemies "+str(players[i].enemies)+" thats "+str(len(players[i].enemies)))
                    v = len(players[i].enemies)
                    print("player #"+str(i)+" had "+str(v)+" votes")
                    if v==mostVotes:
                        tie = True
                        #I think that this isnt working when both vote for the host
                    elif v>mostVotes:
                        print("we have winner("+str(i))
                        mostVotes = v
                        mostVoted = i
                    for p in range(v):
                        pygame.draw.rect(SCREEN, colors[players[i].enemies[p]], pygame.Rect(x*180+125+25*p,y*60+95,15,15))
                try:
                    pygame.display.update()
                except pygame.error:
                    print("you closed the game")
                #sleep
                #display who was voted out
                if tie:
                    print("It was a tie, no one was voted out")
                else:
                    print(imposterNum)
                    if mostVoted==imposterNum:
                        print("the crewmates won")
                        setsharedList('winner',100)
                        # msg = "{w:100"
                        # s.send(bytes(msg,"utf-8"))
                    print("player #"+str(mostVoted)+" was voted out")
                    if mostVoted==idnum:
                        dead = True
                        print("you were voted out")
                    else:
                        players[mostVoted].is_dead = True
                for i in players:
                    i.enemies = []
            #dead
            if dead:
                SCREEN.blit(deadAvatars[idnum], (250-10,250-10))
                SCREEN.blit(skull, (0,470))
            #alive
            else:
                #drawing and motions stuff
                SCREEN.blit(avatar, (250-10,250-10))
                x,y = player.getMove(dp)
                x=x*speed
                y=y*speed
                mapChange = not (x==0 and y==0)
                #I think that I move the map twice somehow, so to not mess up the socket position, divide it by 2
                #example of dab programain
                # map.move(-x/2,-y/2)
                #new strat, do ablosulte map, not relative
                pos[0]+=x
                pos[1]+=y
                # print(pos)
                map.move_to(pos)
                #socket time
                if time>50:
                    if pos!=old_pos:
                        #send pos
                        # print(pos)
                        msg = "{p-"+str(int(pos[0]))+","+str(int(pos[1]))+"}"
                        # print(map.walls[0].a,map.walls[0].b)
                        # print(map.walls[-1].a,map.walls[-1].b)
                        s.send(bytes(msg,'utf-8'))
                        # print(msg)
                        old_pos = pos[0:]
                    time=0
                #find distances of dead players to report them
                r = -1
                for i in range(len(players)):
                    if i!=idnum and players[i].is_dead and not players[i].reported:
                        d = dist(pos, players[i].pos)
                        if d<100:
                            r=i
                #report
                if r!=-1:
                    pygame.draw.circle(SCREEN, (155,155,255), (50,450), 50)
                    if pygame.mouse.get_pressed()[0]:
                        if reportBut.collidepoint(pygame.mouse.get_pos()):
                            print("sent that I, player #"+str(idnum)+" reported player #"+str(r))
                            s.send(bytes("{r-"+str(idnum)+','+str(r)+"}",'utf-8'))
                            setsharedList('reporter',idnum)
                #kill
                if imposter:
                    if cooldown<=0:
                        cooldown = 0
                    else:
                        cooldown-=time_interval
                    if cooldown==0:
                        closest = -1
                        record = 1000
                        for i in range(len(players)):
                            if i!=idnum and not players[i].is_dead:
                                # if pygame.key.get_pressed()[K_SPACE]:
                                #     print(players[i].pos)
                                #     print(map.test_shade(players[i].pos))
                                #     print(" ")
                                d = dist(players[i].pos,pos)
                                if d<record and d<killDistance: #if its closer than others, and within the kill distance
                                    record = d
                                    closest = i
                        if closest!=-1: #if someone is around
                            pygame.draw.circle(SCREEN, (200,0,0,50), (450,450), 50)
                            if pygame.mouse.get_pressed()[0]:
                                if killBut.collidepoint(pygame.mouse.get_pos()):
                                    #kill
                                    msg = "{k-"+str(closest)+"}"
                                    s.send(bytes(msg,"utf-8"))
                                    # print(msg)
                                    cooldown = cooldownMax
                                    players[closest].is_dead = True
                                    bodyCount+=1
                                    if bodyCount==playerCount-1:
                                        print("imposter won")
                                        setsharedList('winner',idnum)
                                        # msg = "{w:"+str(idnum)
                                        # s.send(bytes(msg,"utf-8"))
                                        # winner=idnum
                        else:
                            pygame.draw.circle(SCREEN, (100,0,0,50), (450,450), 50)
                    else:
                        #display kill cool down
                        pygame.draw.circle(SCREEN, (100,0,0,50), (450,450), 50)
                        make_text(str(int(cooldown/1000)),[430,410],SCREEN,(255,255,255))
        # end of game display
        if getsharedList('winner')!=-1:
            # print('lol')
            shape_surf = pygame.Surface((500,500), pygame.SRCALPHA)
            shape_surf.fill((0,0,0,1))
            for i in range(255):
                #pygame.draw.rect(shape_surf, (0,0,0,10), shape_surf.get_rect())
                SCREEN.blit(shape_surf, (0,0))
                #pygame does not draw shapes with alpha values, so have to messy thing above
                # pygame.draw.rect(SCREEN, (0,0,0,254), pygame.Rect(0,0,500,500))
                pygame.display.update()
                timme.sleep(0.01)
            # SCREEN.fill((255,255,255))
            setLoop(False)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE]:
                setLoop(False)
        if pygame.key.get_pressed()[K_SPACE]:
            print(time_interval)
        pygame.display.update()
    pygame.quit()
    # print("main loop done")
    # listener.join()
    # listener.terminate()
    # print("other process killed")
elif status == 'h':
    pygame.display.set_caption("Among Us - host")
    while loop:
        #move stuff
        time_interval = clock.tick(60)
        time+=time_interval
        dp = int(time_interval/2)
        # print(dp)
        SCREEN.fill((255,255,255))
        map.draw()
        for i in players:
            i.drawRel(pos)
        if mapChange:
            mpaChange = False
            map.calc_shade()
        map.draw_shade()
        map.draw_tasks()
        # task bar
        pygame.draw.rect(SCREEN, (150,150,150), pygame.Rect(20,20,460,40))
        if map.getCompletedTasks()>myOldTasks:
            # print("I have completed "+str(map.getCompletedTasks())+" tasks")
            myOldTasks += 1 # keep my tasks seperate from the group's
            incrementSharedList('taskbar',1)
            # s.send(bytes('{t','utf-8'))
            setRequest("{t")
            # print("send {t")
        tb = getsharedList('taskbar')
        if tb!=oldTaskbar:
            oldTaskbar = tb
            # print(str(oldTaskbar)+" tasks have been completed")
            if oldTaskbar==len(map.tasks):
                print("crew won by tasks")
                setsharedList('winner',100)
                setRequest("{w:100")
        pygame.draw.rect(SCREEN, (0,150,0), pygame.Rect(20,20,oldTaskbar*taskWidth,40))
        # tb = getsharedList('taskbar')
        # if tb!=oldTaskbar:
            # oldTaskbar = tb
            # s.send(bytes('t','utf-8'))
        # pygame.draw.rect(SCREEN, (0,150,0), pygame.Rect(20,20,oldTaskbar*taskWidth,40))
        if visible:
            #find out to vote
            lv = getsharedList('reporter')
            if lv!=-1:
                l = True
                f = False
                i_have_voted = False
                # print("start voting loop")
                while l:
                    pygame.draw.rect(SCREEN, (150,150,255), pygame.Rect(60,60,380,380))
                    mPos = pygame.mouse.get_pos()
                    pres = pygame.mouse.get_pressed()[0]
                    for i in range(playerCount):
                        x = i%2
                        y = int(i/2)
                        r = pygame.Rect(x*180+80,y*60+60,160,50)
                        f = False
                        if i!=playerCount-1:#for all the other players
                            if players[i].is_dead:
                                pygame.draw.rect(SCREEN, (100,0,0), r)
                            elif i==lv:
                                pygame.draw.rect(SCREEN, (0,100,0), r)
                                f = True
                            else:
                                pygame.draw.rect(SCREEN, (255,255,255), r)
                                f = True
                        elif dead:#for the host, use diff variables
                            pygame.draw.rect(SCREEN, (100,0,0), r)
                        elif i==lv:
                            pygame.draw.rect(SCREEN, (0,100,0), r)
                            f = True
                        else:
                            pygame.draw.rect(SCREEN, (255,255,255), r)
                            f = True
                        SCREEN.blit(avatars[i], (x*180+90,y*60+65))
                        if pres and f and not i_have_voted and not dead:#if mouse pressed and the person isnt dead and i havent voted and I am alive:
                            if r.collidepoint(mPos):
                                print("You voted for #"+str(i))
                                setRequest("{v-"+str(playerCount-1)+":"+str(i)+"}")
                                if i==playerCount-1:
                                    enemies.append(playerCount-1)#vote for myself
                                else:
                                    players[i].enemies.append(idnum)#vote for others
                                setsharedList('reporter',-1)
                                incrementSharedList("voteCount", 1)
                                i_have_voted = True
                    if getsharedList('voteCount')==playerCount-bodyCount: # if we have all the votes from living peronpeoples
                        l = False
                        setsharedList('reporter',-1)
                        for i in players:
                            i.reported = i.is_dead #dont let people report bodies that werent found before the meeting
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE]:
                            setLoop(False)
                            pygame.quit()
                    pygame.display.update()
                # print("display votes")
                mostVotes = -1
                mostVoted = -1
                tie = False
                for i in range(len(players)):#for all the clients
                    x = i%2
                    y = int(i/2)
                    # print("player "+str(i)+" had enemies "+str(players[i].enemies)+" thats "+str(len(players[i].enemies)))
                    v = len(players[i].enemies)
                    if v==mostVotes:
                        tie = True
                    elif v>mostVotes:
                        mostVotes = v
                        mostVoted = i
                    for p in range(v):
                        # if players[i].enemies[p]==2:
                            # print("hi")
                            # print(colors[2])
                        pygame.draw.rect(SCREEN, colors[players[i].enemies[p]], pygame.Rect(x*180+125+25*p,y*60+95,15,15))
                #for host
                x = playerCount%2
                y = int(playerCount/2)
                # print("player "+str(i)+" had enemies "+str(players[i].enemies)+" thats "+str(len(players[i].enemies)))
                v = len(enemies)
                if v==mostVotes:
                    tie = True
                elif v>mostVotes:
                    mostVotes = v
                    mostVoted = i
                for p in range(v):
                    # if enemies[p]==2:
                        # print("you voted for yourself")
                        # print(colors[2])
                    pygame.draw.rect(SCREEN, colors[enemies[p]], pygame.Rect(x*180+125+25*p,y*60+95,15,15))
                pygame.display.update()
                #sleep
                #display who was voted out
                if tie:
                    print("It was a tie, no one was voted out")
                else:
                    print("player #"+str(mostVoted)+" was voted out")
                    if mostVoted==imposterNum:
                        print("the crewmates won")
                        setsharedList('winner',100)
                        # setRequest("{w:100")
                        #send the victory royale
                    if mostVoted==playerCount-1:
                        dead = True
                    else:
                        players[mostVoted].is_dead = True
                for i in players:
                    i.enemies = []  
            #dead
            if dead:
                SCREEN.blit(deadAvatar, (250-10,250-10))
                SCREEN.blit(skull, (0,470))
            #alive
            else:
                SCREEN.blit(avatar, (250-10,250-10))
                #move
                x,y = player.getMove(dp)
                mapChange = not (x==0 and y==0)
                x=x*speed
                y=y*speed
                pos[0]+=x
                pos[1]+=y
                map.move_to(pos)
                #socket time
                if time>10:
                    if pos!=old_pos:
                        #send pos
                        # print("calling set request")
                        setRequest("{p-"+str(playerCount-1)+":"+str(int(pos[0]))+","+str(int(pos[1]))+"}")
                        old_pos = pos[0:]
                    time=0

                #find distances of dead players to report them
                r = -1
                for i in range(playerCount-1):#cant report myself, so -1
                    if players[i].is_dead and not players[i].reported:
                        d = dist(pos, players[i].pos)
                        # print(d)
                        if d<100:
                            r=i
                #report
                if r!=-1:
                    pygame.draw.circle(SCREEN, (155,155,255), (50,450), 50)
                    if pygame.mouse.get_pressed()[0]:
                        if reportBut.collidepoint(pygame.mouse.get_pos()):
                            print("sent that I player #"+str(playerCount-1)+" reported player #"+str(r))
                            setRequest("{r-"+str(playerCount-1)+','+str(r)+"}")
                            setsharedList('reporter',playerCount-1)
                if imposter:
                    if cooldown<=0:
                        cooldown = 0
                    else:
                        cooldown-=time_interval
                    if cooldown==0:
                        closest = -1
                        record = 1000
                        for i in range(len(players)):
                            if i!=playerCount-1 and not players[i].is_dead:
                                d = dist(players[i].pos,pos)
                                if d<record and d<killDistance: #if its closer than others, and within the kill distance
                                    record = d
                                    closest = i
                        if closest!=-1: #if someone is around
                            pygame.draw.circle(SCREEN, (200,0,0,50), (450,450), 50)
                            if pygame.mouse.get_pressed()[0]:
                                if killBut.collidepoint(pygame.mouse.get_pos()): 
                                    #kill
                                    msg = "{k-"+str(closest)+"}"
                                    setRequest(msg)
                                    # print(msg)
                                    cooldown = cooldownMax
                                    players[closest].is_dead = True
                                    bodyCount+=1
                                    if bodyCount==playerCount-1:
                                        print("imposter won")
                                        # winner=playerCount-1
                                        setsharedList('winner', playerCount-1)
                                        setRequest("{w:"+str(playerCount-1))
                        else:
                            pygame.draw.circle(SCREEN, (100,0,0,50), (450,450), 50)
                    else:
                        pygame.draw.circle(SCREEN, (100,0,0,50), (450,450), 50)
                        make_text(str(int(cooldown/1000)),[430,410],SCREEN,(255,255,255))
        #end of game display
        if getsharedList('winner')!=-1:
            shape_surf = pygame.Surface((500,500), pygame.SRCALPHA)
            shape_surf.fill((0,0,0,1))
            for i in range(255):
                #pygame.draw.rect(shape_surf, (0,0,0,10), shape_surf.get_rect())
                SCREEN.blit(shape_surf, (0,0))
                #pygame does not draw shapes with alpha values, so have to messy thing above
                # pygame.draw.rect(SCREEN, (0,0,0,254), pygame.Rect(0,0,500,500))
                pygame.display.update()
                timme.sleep(0.01)
            # SCREEN.fill((255,255,255))
            setLoop(False)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE]:
                setLoop(False)
        if pygame.key.get_pressed()[K_SPACE]:
            print(time_interval)
        pygame.display.update()
    pygame.quit()

sys.exit()