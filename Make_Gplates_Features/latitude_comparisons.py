#!/bin/python
# latitude_comparisons.py
#Project: split up a file by headers
#Date: 15 November 2013
#Authors: Nathan and Kara

'''
give some info here about what the script does

'''

#Import some libraries filled with functions we need
import sys

#Set the filename based on the command line input
filename=sys.argv[1]
name=sys.argv[2]
#block=sys.argv[2]

#Open up the input file for 'r'eading
xyfile=open(filename, 'r')

#Set the output filename 
outFilename = filename[:-2]+'gmt'

#Open up the output file for 'w'riting to.
outputFile=open(outFilename, 'a') #a is append #w is write



while True: 
	line=xyfile.readline() #Read a line at a time
	
	if len(line) == 0: #Check if the line is zero length (i.e. the end of the file)
		break #If it is, break out of the while loop
	
	else: #only print the line if it contains the given string
		if line.find('> name '+str(name))==0:	#set name variable at the top of the script
			print "Found ",name
			foundFlag=1
			outputFile.write(line) # print the line we are on
			while foundFlag==1:
				line=xyfile.readline()
				#print line
				if line=='>\n':			#once we reach a line that contains just ">" then break the loop
					foundFlag=0
				else:
					outputFile.write(line)
				
				
		#while foundFlag==1:
		#if line[0] != '>': #don't print the line if it contains the string
		#	line=xyfile.readline() #Read a line at a time
		#		outputFile.write(line)
			

 #Flush and close the output file, to prevent unessacary memory build up and corruption 
 #(important for complicated programs)
outputFile.flush()
outputFile.close()
		
"""

#Read the input file until the EOF
while True: 
	line=xyfile.readline() #Read a line at a time
	
	if len(line) == 0: #Check if the line is zero length (i.e. the end of the file)
		break #If it is, break out of the while loop
	
	else: #If it is not the end of the file, do some stuff:
		#First check that the line we have read in, contains this string at the 0th index:
		if line.find('> validTime TimePeriod <begin> TimeInstant <timePosition>')==0:
			#If it does, then split that line by the symbols < and >. 
			#We can chop it up like this because we KNOW the shape of the string, 
			#and we know the index of where everything *should* be.
			lineList1=line.split('>')
			lineList2=lineList1[3].split('<')
			time=float(lineList2[0]) #Save the chopped out piece as a floating point number, time
			outputFile.write(line) # print the line we are on
		
		#Check if it is a different header
		elif line[0] == '>': 
			#If it is a header, just print the header to the file
			outputFile.write(line)
		
		#If the line is anything but a header (i.e. our data in this case) do some other stuff
		else:
			#Split the line up, by default spaces
			lineList=line.split()
			#Format the output, 0, 1, 2, is the index, s is a string, g is a floating point number, \n is a newline.
			#Note all this is enclosed in quotes '', this is exactly the style of the output, 
			#so the spaces are important.
			#Finally, say what we actually want to print out, in this case, our data we just read in, and the time.
			ostring='{0:s} {1:s} {2:g}\n'.format(lineList[0],lineList[1],time)
			#Finally, print it out.
			outputFile.write(ostring)

#Flush and close the output file, to prevent unessacary memory build up and corruption 
#(important for complicated programs)
outputFile.flush()
outputFile.close()
"""