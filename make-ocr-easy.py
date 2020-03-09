#! /usr/bin/env python
from gimpfu import *
import os

def is_over_limit(val,axis,limit):
    return val < limit[axis][0] or val > limit[axis][1]

def get_adjacent(region,pos,direction,limit):
    x,y = pos
    offsetX,offsetY = direction
    if offsetX == 0:
        if is_over_limit(y+offsetY,'y',limit):
            a1,a2,a3 = '\x00','\x00','\x00'
        else:
            if is_over_limit(x+offsetY,'x',limit):
                a1 = '\x00'
            else:
                a1 = region[x+offsetY,y+offsetY]
            if is_over_limit(x+offsetY*-1,'x',limit):
                a3 = '\x00'
            else:
                a3 = region[x+offsetY*-1,y+offsetY]
            a2 = region[x,y+offsetY]
    elif offsetY == 0:
        if is_over_limit(x+offsetX,'x',limit):
            a1,a2,a3 = '\x00','\x00','\x00'
        else:
            if is_over_limit(y+offsetX*-1,'y',limit):
                a1 = '\x00'
            else:
                a1 = region[x+offsetX,y+offsetX*-1]
            if is_over_limit(y+offsetX,'y',limit):
                a3 = '\x00'
            else:
                a3 = region[x+offsetX,y+offsetX]
            a2 = region[x+offsetX,y]
    return a1,a2,a3

def turn(direction,rotate):     # rotate meaning: -1 left, 1 right
    if direction[0] == 0:
        return direction[1]*rotate*-1, 0
    elif direction[1] == 0:
        return 0, direction[0]*rotate

def move(pos,direction):
    return pos[0]+direction[0],pos[1]+direction[1]

def contour_add(contour,pos):
    contour['poses'].add(pos)
    x,y = pos
    if contour['x1'] >= x: contour['x1'] = x
    if contour['x2'] <= x: contour['x2'] = x
    if contour['y1'] >= y: contour['y1'] = y
    if contour['y2'] <= y: contour['y2'] = y
    return contour

# Theo Pavlidis' Algorithm
# http://www.imageprocessingplace.com/downloads_V3/root_downloads/tutorials/contour_tracing_Abeer_George_Ghuneim/theo.html
def Theo_Pavlidis_algorithm(region,start):
    debug = False
    limit = {'x': [region.x, region.x+region.w-1], 'y': [region.y, region.y+region.h-1]}
    contour = {'poses': set(), 'x1': limit['x'][1], 'x2': limit['x'][0], 'y1': limit['y'][1], 'y2': limit['y'][0]}
    pos = start
    initDirection = 0,-1    # meaning upward
    direction = initDirection

    contour = contour_add(contour,pos)
    step = 1
    while True:
        if step == 1:
            a1,a2,a3 = get_adjacent(region,pos,direction,limit)
        if debug: pdb.gimp_message((pos,direction,(a1,a2,a3)))

        if a1 != '\x00':
            if step == 1:   # To check break condition efficiently, take only 1 step for each iteration
                pos = move(pos,direction)
            elif step == 2:
                direction = turn(direction,-1)  
            elif step == 3:
                pos = move(pos,direction)
                contour = contour_add(contour,pos)
                step = 0
            step+=1
        elif a2 != '\x00':
            pos = move(pos,direction)
            contour = contour_add(contour,pos)
        elif a3 != '\x00':
            if step == 1:
                direction = turn(direction,1)
            elif step == 2:
                pos = move(pos,direction)
            elif step == 3:
                direction = turn(direction,-1)
            elif step == 4:
                pos = move(pos,direction)
                contour = contour_add(contour,pos)
                step = 0
            step+=1
        else:
            direction = turn(direction,1)

        if pos == start and direction == initDirection:
            break
    return contour

def search(region):
    debug = False
    contourList = []
    checkList = set()
    for i in range(region.x, region.x+region.w, 70):    # Lower the steps, more small areas can be catched. But increases execution time.
        for j in range(region.y, region.y+region.h, 100):
            if region[i,j] != '\x00':
                leftNearest = i
                while leftNearest > region.x and region[leftNearest-1,j] != '\x00':
                    leftNearest-=1
                if (leftNearest,j) in checkList:
                    continue
                if debug: pdb.gimp_message((leftNearest,j))
                
                contour = Theo_Pavlidis_algorithm(region,(leftNearest,j))
                contourList.append(contour)
                checkList |= contour['poses']
    return contourList

def make_ocr_easy(*args):
    for image in gimp.image_list():
        path,name = os.path.split(image.filename.decode("utf-8"))
        name = "text_"+os.path.splitext(name)[0]+".png"

        drawable = image.layers[-1]
        pdb.gimp_selection_flood(image)
        pdb.gimp_edit_copy(drawable)
        pdb.gimp_floating_sel_to_layer(pdb.gimp_edit_paste(drawable, True))

        pdb.gimp_selection_grow(image, 1)
        selection = pdb.gimp_image_get_selection(image)
        non_empty, x1, y1, x2, y2 = pdb.gimp_selection_bounds(image)
        region = selection.get_pixel_rgn(x1,y1,x2-x1+1,y2-y1+1)
        contourList = search(region)

        for contour in contourList:
            pdb.gimp_image_select_rectangle(image, 0, contour['x1'], contour['y1'], contour['x2']-contour['x1'], contour['y2']-contour['y1'])
        pdb.gimp_drawable_edit_fill(drawable, 2)
        pdb.gimp_selection_none(image)
        pdb.gimp_drawable_update(drawable, x1, y1, x2-x1, y2-y1)
        pdb.file_png_save_defaults(image, pdb.gimp_image_merge_visible_layers(image, 1), os.path.join(path,name), os.path.join(path,name))

register(
	"python_fu_make-ocr-easy", "", "", "", "", "",
	"<Image>/Tools/Make OCR easy", "RGB*, GRAY*",
	[],
	[],
	make_ocr_easy
)

main()
