# Annotator of ribbon slices
# Takes processed ribbons and reference images (Nissl and annotated Myelin)
# (Did not end up using this)

import cv2
from tkinter import *
import os
import numpy as np

img_points = []
img_complete = False
count = 0
prev_count = 0
ribbon_name = 0

def on_mouse(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        #print('Mouse Position: '+str(x)+', '+str(y))
        img_points.append(x)

def on_mouse_labelled(event, x, y, flags, params):
    global traverses
    if event == cv2.EVENT_LBUTTONDOWN:
        blank_img = np.zeros(labelled_img.shape[:2], dtype=np.uint8)
        for i, trav in enumerate(traverses):
            # Mask contour
            result = cv2.drawContours(blank_img, traverses, i, 255, thickness=-1)
            if result[y,x]:
                img_points.append(i)
                return None

def undo(x):
    if x == 1:
        global img_points, img, prev_count, labelled_img
        if len(img_points) > 0: 
            img_points.pop()
            img = img_backup.copy()
            labelled_img = labelled_backup.copy()
            for i in img_points:
                cv2.line(img, (i, 0), (i,50), (0, 0, 255), 2)
                cv2.drawContours(labelled_img, traverses, i, (0,0,255), thickness=-1)

        prev_count = len(img_points)

def reset(x):
    if x == 1:
        global img, img_points, prev_count, labelled_img
        img = img_backup.copy()
        labelled_img = labelled_backup.copy()
        img_points = []
        prev_count = 0

def skip(x):
    if x == 1:
        global img_points, img_complete, prev_count
        img_points = []
        img_complete = True
        prev_count = 0

def save(x):
    global img_points, img
    if x == 1 and len(img_points)>1:
        #Easier to save as a JSON list file by appending string
        with open("Annotations.csv", 'a') as f:
            for k in img_points:
                #Ribbon number, hemisphere number, and x position of annotation
                f.write(ribbon_name+","+file[-5:-4]+","+str(k)+"\n")

        print("Saved")
        skip(1)

dir = "RibbonImages/"
print("Reading images from:", dir)

#Create windows
cv2.namedWindow('Annotator image', cv2.WINDOW_AUTOSIZE)
cv2.namedWindow('Reference', cv2.WINDOW_AUTOSIZE)
cv2.setMouseCallback('Annotator image', on_mouse, 0)
cv2.setMouseCallback('Reference', on_mouse_labelled, 0)

#Track if window closed
stop = False
button_pad = 150

for idx, file in enumerate(os.listdir(dir)):
    print(file)
    if stop:
        break
    
    ribbon_name = file[:3]
    
    img = cv2.imread(dir + file)
    annotated = cv2.imread("AnnotatedMyelin/"+ str((int(ribbon_name)-1)//3) + "_" + str(int(ribbon_name)-1)+"_regions.tif")
    nissl = cv2.imread("NisslImages/" + ribbon_name+".tif")

    img_backup = img.copy()
    img_complete = False

    # Create a reference image by horizontally stacking labelled myelin and nissl
    annotated = cv2.resize(annotated, (nissl.shape[1], nissl.shape[0]))
    labelled_img = np.hstack((annotated, nissl))
    labelled_img = cv2.resize(labelled_img, (labelled_img.shape[1]//3, labelled_img.shape[0]//3))
    labelled_backup = labelled_img.copy()

    # Load precomputed traverses
    traverses = np.load("PrecomputedTraverses/"+ribbon_name+"_"+file[-5:-4]+".npy", allow_pickle=True)
    for trav in traverses:
        trav[:,:] = trav[:,:]//3
        trav[:,0] += annotated.shape[1]//3
    print("Loading traverses")

    while not img_complete:
        for i in img_points:
            cv2.line(img, (i, 0), (i,50), (0, 0, 255), 2)
            cv2.drawContours(labelled_img, traverses, i, (0,0,255), thickness=-1)
        
        cv2.imshow('Annotator image', img)
        cv2.imshow('Reference', labelled_img)

        key = cv2.waitKey(1)
        if key == ord('R'): #Reset: shift-R
            reset(1)
        if key == ord('S'): #Save: shift-S
            save(1)
            break
        if key == ord('N'): #Skip: shift-N
            skip(1)
            break
        if key == ord('Z'): #undo: shift-Z
            undo(1)

        if cv2.getWindowProperty('Annotator image', cv2.WND_PROP_VISIBLE) < 1: #if window closed
            stop = True
            break
        if cv2.getWindowProperty('Reference', cv2.WND_PROP_VISIBLE) < 1: #if window closed
            stop = True
            break

cv2.destroyAllWindows()