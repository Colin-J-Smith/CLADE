#!/usr/bin/env python





# Python 2/3 compatibility
from __future__ import print_function

import cv2
import numpy as np
from difflib import SequenceMatcher
import sys

import RPi.GPIO as GPIO


def similar(a, b):
	return SequenceMatcher(None, a, b).ratio()

def nothing(*arg):
	pass

def limit(inputVal,limits):
	output=inputVal
	for i,val in enumerate(inputVal,0):
		if val>limits[i][1]:
			val=limits[i][1]
		elif val<limits[i][0]:
			val=limits[i][0]
		output[i]=val

	return output





try:
	fn = sys.argv[1]
except:
	fn = 0



cap = cv2.VideoCapture(fn)


cv2.namedWindow('image')
thrs=50
cv2.createTrackbar('Hue', 'image', 61, 179, nothing)
cv2.createTrackbar('Sat', 'image', 235, 255, nothing)
cv2.createTrackbar('Val', 'image', 255, 255, nothing)
cv2.createTrackbar('filterThresh', 'image', 0, 100, nothing) 

 #sets how much to blur
filt=39
exitNow=0
pause=0

# set up the GPIO pin
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
trigger_pin = 13
GPIO.setup(trigger_pin, GPIO.OUT)
GPIO.output(trigger_pin, GPIO.LOW)

while True:
	try:
		
		flag, imgInit = cap.read()

		
		imgBGR = cv2.resize(imgInit,(300, 300),cv2.INTER_AREA)
		img=cv2.cvtColor(imgBGR, cv2.COLOR_BGR2HSV) 
		
		while True:	
			if exitNow==1:
				break


			hue = cv2.getTrackbarPos('Hue', 'image')
			sat = cv2.getTrackbarPos('Sat', 'image')
			val = cv2.getTrackbarPos('Val', 'image')

			#GPIO.output(trigger_pin, GPIO.LOW)
			
			

			lower=[hue,sat,val]
			lower=np.array(lower, dtype="uint8")
			lower2=[[[hue,sat,val]]]
			lower2=np.array(lower2, dtype="uint8")
			chosenColor = cv2.cvtColor(lower2, cv2.COLOR_HSV2BGR)##Tr
		

			upperBound=limit(lower+thrs/2,[[0,179],[0,255],[0,255]])
			lowerBound=limit(lower-thrs/2,[[0,179],[0,255],[0,255]])
			mask=np.uint8(cv2.inRange(img,lowerBound,upperBound))


			vis = np.uint8(img.copy())
			vis[mask==0]=(0,0,0)
			
			
			gray2 = img[:,:,2] #only want black and white image
			gray = vis[:,:,2]

			blurred = cv2.GaussianBlur(gray, (filt, filt), 0)

			thresholdValue = cv2.getTrackbarPos('filterThresh', 'image')
			thresh = cv2.threshold(blurred, thresholdValue, 255, cv2.THRESH_BINARY)[1]
			testArray=[(lower-thrs/2).tolist(),(lower+thrs/2).tolist(),lowerBound.tolist(),upperBound.tolist(),thresholdValue]


			[cnts, trash] = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		

			areas=int(len(cnts))
			splotch = np.zeros((1,areas),dtype=np.uint8)
			
			# loop over the contours
			try:	
				for i,c in enumerate(cnts,0):
				
					M = cv2.moments(c)
					splotch[0][i] = int(M["m00"])
				try:
					max1=np.argmax(splotch)
				except:
					max1=-1
				
				original=vis.copy()
				if max1>-1:
					M = cv2.moments(cnts[max1])
					cX = int(M["m10"] / M["m00"])
					cY = int(M["m01"] / M["m00"])


					
					# cv2.drawContours(vis, [cnts[max1]], -1, (0, 255, 0), 2)
					# cv2.circle(vis, (cX, cY), 7, (255, 255, 255), -1)
					# cv2.putText(vis, "Green Light", (cX - 20, cY - 20),
					# 	cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

					# Trigger the button
					GPIO.output(trigger_pin, GPIO.HIGH)

			except:
				pass
			
			# cc=(int(chosenColor[0][0][0]),int(chosenColor[0][0][1]),int(chosenColor[0][0][2]))
			# cv2.circle(imgBGR, (50, 50), 50, cc, -1)

			# visBGR=cv2.cvtColor(vis, cv2.COLOR_HSV2BGR) 
			# thresh = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
			
			# cv2.imshow('image',np.hstack([imgBGR,thresh, visBGR])) #np.hstack([original, vis]))#np.hstack([thresh, gray2]))
			
			# ch=cv2.waitKey(1)
			# print(ch)

			# if ch == 27:
			# 	exitNow=True
			# 	break
			
			# elif ch==112 and pause==0:
				
			# 	pause=1
			# 	print("paused")
		
			# elif ch==112 and pause ==1:
			# 	pause=0
			# 	print("unPaused")

			# 	break
			# elif pause==1:
			# 	pass
			# else:
			# 	break
	except KeyboardInterrupt:
		raise
	except cv2.error as e:

		print("Here it is \n",str(e), "\n")
		if similar(str(e), " /home/pi/opencv-3.3.0/modules/imgproc/src/imgwarp.cpp:3483: error: (-215) ssize.width > 0 && ssize.height > 0 in function resize")>.8:
			print("\n\n\n\n Your video appears to have ended\n\n\n")
		break
							
cv2.destroyAllWindows()
















		
	
