# -*- coding: utf-8 -*-
"""
Created on Thu Jul  2 02:52:04 2020
this is all proof-of-concept stuff, so im not too fussed about global variable bad practices
"""
import pygame
from pygame.math import Vector2
import math
import time
import sys
import random

pygame.init()

N = 200 #number of agents

FPS = 30
bgcolor = (0,0,0)

global wolf_list, sheep_list, Nx, Ny
wolf_list, sheep_list = [],[]
Nx, Ny = 1280,720 #screen resolution

global screen, field, debugsurf #set up the three drawable surfaces
screen = pygame.display.set_mode((Nx,Ny)) #display
field = pygame.Surface( (Nx,Ny), pygame.SRCALPHA ) #game field
debugsurf = pygame.Surface( (Nx,Ny), pygame.SRCALPHA ) #debug layer (for drawing trails, grids, etc on)


screen.fill(bgcolor)
field.fill( (255,255,255) )
debugsurf.fill( (0,0,0,0)) #transparent at first

screen.blit(field, (0,0))
screen.blit(debugsurf,(0,0))
pygame.display.update()
pygame.display.set_caption("Wolfpack")
clock = pygame.time.Clock()


grid_size = 50 #this determines the boid vision range, each boid can see in a circle with radius "grid_size"
bar_width = 1

#DRAW GRID on overlay
Gx = -2
Gy = -2 #note there will be Gy + 1 actual squares to correspont to Gy gridlines
for i in range(0,Nx+grid_size,grid_size):
    pygame.draw.rect(debugsurf, (0,0,255,10), (i, 0, bar_width, Ny) )
    Gx += 1
for j in range(0,Ny+grid_size,grid_size):
    pygame.draw.rect(debugsurf, (0,0,255,10), (0, j, Nx, bar_width) )
    Gy += 1
    
boid_list = []
target_list = []

""" -------- UTILITY FUNCTIONS -------- """

def norm(vec):
    return sum([i**2 for i in vec])
    
def measure_distance(vec1, vec2,normal=False):
    #normal points FROM vec1 TO vec2
    #toroidal world so this is a little subtle
    #we keep vec1 fixed, but have to consider 9 different options (reflections) of vec2
    best_norm = math.inf
    for i in range(-1,2):
        for j in range(-1,2):
            reflection = (vec2 + Vector2(Nx*i,Ny*j)) - vec1
            reflection_norm = norm(reflection)
            if reflection_norm < best_norm:
                best = reflection
                best_norm = reflection_norm
    if normal:
        return math.sqrt(best_norm), best.normalize() #is this needed?
    else:
        return math.sqrt(best_norm)
def debug_search(targ,rg=5):
    neighbours = []
    for i in range(-rg,rg+1):
        for j in range(-rg,rg+1):
            tx, ty = (targ.gx + i)%Gx, (targ.gy + j)%Gy
            print(tx,ty)
            neighbours += grid_table[(tx,ty)]
    return [i for i in neighbours if i != targ] 

def place_agents():
    for n in range(1,N):   
        pos = Vector2(random.random()*Nx, random.random()*Ny)
        boid_list.append(Wolf(n,pos))
    target = Sheep(N)
    boid_list.append(target)
    target_list.append(target)
    return

def gen_table(boid_list):
    grid_table = {(i,j):[] for i in range(Gx+1) for j in range(Gy+1)}
    for b in boid_list:
        grid_table[(b.gx,b.gy)].append(b)
    return grid_table
    
""" -------- CLASSES -------- """
class Boid:
    def __init__(self,idnum=None,startpos=Vector2(random.random()*Nx, random.random()*Ny) ):
        self.id = idnum
        self.col = (0,255,0)
        self.size = 2
        
        self.max_force = 0.6
        self.max_speed = 100*(0.75 + 0.5*random.random())
        self.max_turnspeed = 1 #about 0.5 rev/s
        
        self.repulse_strength = 80*FPS
        equil_dist = 4
        self.cohesion_strength = self.repulse_strength/equil_dist
        self.alignment_strength = 5
        
        self.vision = grid_size
        self.focus = 0.8
        
        self.pos = Vector2(startpos) #redundant casting for safety
        self.vel = Vector2( random.uniform(0,1), random.uniform(0,1)) * self.max_speed
        self.accel = Vector2(0,0)
        
        self.heading = math.atan2(self.vel[1],self.vel[0])
        self.heading_target = self.heading
        
        self.gx,self.gy = self.pos//grid_size #current grid cell (goes from -1 to 8)
        if self.gx < 0:
            self.gx = Gx
        elif self.gx > Gx:
            self.gx = 0
        if self.gy < 0:
            self.gy = Gy
        elif self.gy > Gy:
            self.gy = 0
        
    def update(self,dt=1/FPS):
        # if self.id == 0:
        #     pygame.draw.line(debugsurf, self.col,self.pos, self.pos+self.vel*dt,1)
        self.pos += self.vel*dt
        self.vel += self.accel*dt
        if norm(self.vel) > (self.max_speed/FPS)**2:
            self.vel.scale_to_length(self.max_speed)    
        self.accel = Vector2(0,0)
        #clamp position
        self.pos[0] = self.pos[0] % Nx
        self.pos[1] = self.pos[1] % Ny
        
        #rotate by UP TO MAX TURNSPEED*deltatime
        rotate = self.alignment_strength*min(self.heading_target - self.heading, self.max_turnspeed*dt)
        
        self.vel = self.vel.rotate(rotate*180/math.pi)
        
        self.heading = math.atan2(self.vel[1],self.vel[0])
        self.heading_target = self.heading
        self.gx, self.gy = self.pos//grid_size #current grid cell (goes from -1 to 8)
            
    def draw(self):
        pygame.draw.circle(field,self.col, [int(i) for i in self.pos],self.size)

    def find_neighbours(self,rg=1):
        neighbours = []
        for i in range(-rg,rg+1):
            for j in range(-rg,rg+1):
                tx, ty = (self.gx + i)%(Gx+1), (self.gy + j)%(Gy+1)
                neighbours += [a for a in grid_table[(tx,ty)]]
        return [i for i in neighbours if i != self and self.vision > measure_distance(self.pos,i.pos)]         
    
    def aim_for_goal(self):
        #placeholder goalless situation
        goal = self.align_target
        self.heading_target = ((1-self.focus)*self.align_target + self.focus*goal)
    
    def calculate_movement(self):
        neighbours = self.find_neighbours()
        avgpos = Vector2(0,0)
        avgheading = 0
        for neighbour in neighbours:
            #draw line to neighbour in blue
            if self.id == 0:
                pygame.draw.line(field, (0,0,255), self.pos, neighbour.pos)
            #apply repulsive affect
            mag,normal = measure_distance(neighbour.pos,self.pos,True)
            self.accel += self.repulse_strength*normal/mag
            #cohesion
            avgpos += neighbour.pos
            #align
            avgheading += neighbour.heading
            
        if neighbours:
            cohesion_target = avgpos/len(neighbours)
            mag, normal = measure_distance(self.pos, cohesion_target,True)
            self.accel += self.cohesion_strength*normal
            self.align_target = avgheading/len(neighbours)
            self.aim_for_goal()
        return
    
class Sheep(Boid):
    def __init__(self,idnum=None,startpos=Vector2(random.random()*Nx, random.random()*Ny)):
        Boid.__init__(self,idnum,startpos)
        self.col = (0,0,255)
        self.max_speed = self.max_speed*1.1
        self.focus =1
        self.size = 4
        self.vision *= 4
        self.repulse_strength *= 100
    
    def calculate_movement(self):
        neighbours = self.find_neighbours(4)
        avgpos = Vector2(0,0)
        avgheading = 0
        for neighbour in neighbours:
            #draw line to neighbour in blue
            # if self.id == 0:
            #   pygame.draw.line(field, (0,0,255), self.pos, neighbour.pos)
            #apply repulsive affect
            mag,normal = measure_distance(neighbour.pos,self.pos,True)
            self.accel += self.repulse_strength*normal/mag
        return
class Wolf(Boid):
    def __init__(self,idnum=None,startpos=Vector2(random.random()*Nx, random.random()*Ny)):
        Boid.__init__(self,idnum,startpos)
        self.col = (255,0,0)
        self.focus = 0.8
        self.size = 2
    
    def aim_for_goal(self):
        #placeholder goalless situation
        mag, norm = measure_distance(target_list[0].pos,self.pos,True)
        if random.random() > 0:
            goal = math.atan2(-norm[1],-norm[0])
            #self.col = (255,0,0)
        else:
            goal = self.align_target
            #self.col = (0,255,0)
        self.heading_target = ((1-self.focus)*self.align_target + self.focus*goal)
        
""" -------- MAIN LOOP -------- """"
grid_table = {}
place_agents()
grid_table = gen_table(boid_list)
#sample = boid_list[0] #for debugging purposes only

t0 = time.time()
#MAINLOOP HERE
while True:
    for event in pygame.event.get(): #detect events            
            if event.type == pygame.QUIT or pygame.key.get_pressed()[27]: #detect attempted exit
                pygame.quit()
                sys.exit() 
    clock.tick(FPS)
    deltatime = time.time()-t0
    t0 = time.time()
  
    screen.fill(bgcolor)
    field.fill((255,255,255))
    
    grid_table = gen_table(boid_list)
    
    for a in boid_list:      
        a.calculate_movement()
        a.update(deltatime)
        a.draw()
    screen.blit(field, (0,0))
    screen.blit(debugsurf,(0,0))

    pygame.display.update()

