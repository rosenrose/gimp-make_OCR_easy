#! /usr/bin/env python
from gimpfu import *
import os

def BFS(region,i,j,marked,limit):
    convex = {'x1':limit['xMax'], 'x2':limit['xMin'], 'y1':limit['yMax'], 'y2':limit['yMin']}
    queue = []
    queue.append((i,j))
    marked[i-region.x][j-region.y] = True
    while queue:
        i,j = queue.pop()
        if convex['x1'] >= i: convex['x1'] = i
        if convex['x2'] <= i: convex['x2'] = i
        if convex['y1'] >= j: convex['y1'] = j
        if convex['y2'] <= j: convex['y2'] = j

        adjacent = set([(i,max([j-2,limit['yMin']])),(min([i+2,limit['xMax']]),j),
                        (i,min([j+2,limit['yMax']])),(max([i-2,limit['xMin']]),j)])
        if (i,j) in adjacent:
            adjacent.remove((i,j))
        for ad in adjacent:
            if marked[ad[0]-region.x][ad[1]-region.y]:
                continue
            if region[ad] != '\x00':
                queue.insert(0,ad)
            marked[ad[0]-region.x][ad[1]-region.y] = True
    return convex,marked

def search(region):
    marked = [[False for i in range(region.y,region.y+region.h)] for j in range(region.x,region.x+region.w)]
    limit = {'xMin': region.x, 'yMin': region.y, 'xMax': region.x+region.w-1, 'yMax': region.y+region.h-1}
    convexList = []
    temp=[]
    for i in range(region.x,region.x+region.w,100):
        for j in range(region.y,region.y+region.h,100):
            if marked[i-region.x][j-region.y]:
                continue            
            if region[i,j] != '\x00':
                temp.append((i,j))
                convex,marked = BFS(region,i,j,marked,limit)
                convexList.append(convex)
            else:
                marked[i-region.x][j-region.y] = True
    # pdb.gimp_message(temp)
    return convexList

def make_ocr_easy(*args):
    for image in gimp.image_list():
        path,name = os.path.split(image.filename.decode("utf-8"))
        name = "text_%s.png"%(os.path.splitext(name)[0])
        drawable = image.layers[-1]

        pdb.gimp_selection_flood(image)
        pdb.gimp_edit_copy(drawable)
        pdb.gimp_floating_sel_to_layer(pdb.gimp_edit_paste(drawable, True))

        pdb.gimp_selection_grow(image, 1)
        selection = pdb.gimp_image_get_selection(image)
        non_empty, x1, y1, x2, y2 = pdb.gimp_selection_bounds(image)
        region = selection.get_pixel_rgn(x1,y1,x2-x1,y2-y1)
        convexList = search(region)

        for convex in convexList:
            pdb.gimp_image_select_rectangle(image, 0, convex['x1'], convex['y1'],
                            convex['x2']-convex['x1'], convex['y2']-convex['y1'])
        # drawable = image.layers[-1]
        # image.active_layer = drawable
        pdb.gimp_drawable_edit_fill(drawable, 2)
        pdb.gimp_selection_none(image)
        pdb.gimp_message(name)
        pdb.file_png_save_defaults(image, pdb.gimp_image_merge_visible_layers(image, 1), os.path.join(path,name), os.path.join(path,name))

register(
	"python_fu_make-ocr-easy", "", "", "", "", "",
	"<Image>/Tools/Make OCR-easy", "RGB*, GRAY*",
	[],
	[],
	make_ocr_easy
)

main()
