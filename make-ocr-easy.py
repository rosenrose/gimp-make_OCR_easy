#! /usr/bin/env python
from gimpfu import *
import os

def get_adjacent(region,pos,direction):
    x,y = pos
    offsetX,offsetY = direction
    if offsetX == 0:
        return region[x+offsetY,y+offsetY], region[x,y+offsetY], region[x+offsetY*-1,y+offsetY]
    elif offsetY == 0:
        return region[x+offsetX,y+offsetX*-1], region[x+offsetX,y], region[x+offsetX,y+offsetX]

def turn(direction,rotate):     # rotate meaning: -1 left, 1 right
    if direction[0] == 0:
        return direction[1]*rotate*-1, 0
    elif direction[1] == 0:
        return 0, direction[0]*rotate

def move(pos,direction):
    return pos[0]+direction[0],pos[1]+direction[1]

# Theo Pavlidis' Algorithm
# http://www.imageprocessingplace.com/downloads_V3/root_downloads/tutorials/contour_tracing_Abeer_George_Ghuneim/theo.html
def Theo_Pavlidis_algorithm(region,start):
    debug = False
    contour = set()
    pos = start
    initDirection = 0,-1    # meaning upward
    direction = initDirection

    contour.add(pos)
    step = 1
    while True:
        if step == 1:
            a1,a2,a3 = get_adjacent(region,pos,direction)
        if debug: pdb.gimp_message((pos,direction,(a1,a2,a3)))

        if a1 != '\x00':
            if step == 1:   # To check break condition efficiently, take only 1 step for each iteration
                pos = move(pos,direction)
            elif step == 2:
                direction = turn(direction,-1)  
            elif step == 3:
                pos = move(pos,direction)
                contour.add(pos)
                step = 0
            step+=1
        elif a2 != '\x00':
            pos = move(pos,direction)
            contour.add(pos)
        elif a3 != '\x00':
            if step == 1:
                direction = turn(direction,1)
            elif step == 2:
                pos = move(pos,direction)
            elif step == 3:
                direction = turn(direction,-1)
            elif step == 4:
                pos = move(pos,direction)
                contour.add(pos)
                step = 0
            step+=1
        else:
            direction = turn(direction,1)
        if pos == start and direction == initDirection:
            break
    return contour

def search(region):
    debug = False
    contourBounds = []
    checkList = []
    for i in range(region.x, region.x+region.w, 70):    # Lower the steps, more small areas can be catched. But increases execution time.
        for j in range(region.y, region.y+region.h, 100):
            if region[i,j] != '\x00':
                leftNearest = i
                while region[leftNearest-1,j] != '\x00':
                    leftNearest-=1
                if (leftNearest,j) in checkList:
                    continue
                if debug: pdb.gimp_message((leftNearest,j))
                contour = Theo_Pavlidis_algorithm(region,(leftNearest,j))                
                bound = {'x1': min([x for x,y in contour]), 'x2': max([x for x,y in contour]),
                        'y1': min([y for x,y in contour]), 'y2': max([y for x,y in contour])}
                contourBounds.append(bound)
                checkList += list(contour)
    return contourBounds

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
        region = selection.get_pixel_rgn(x1-1,y1-1,x2-x1+2,y2-y1+2)     # Additional zero-filled edges needed for algorithm
        contourBounds = search(region)

        for bound in contourBounds:
            pdb.gimp_image_select_rectangle(image, 0, bound['x1'], bound['y1'], bound['x2']-bound['x1'], bound['y2']-bound['y1'])
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
