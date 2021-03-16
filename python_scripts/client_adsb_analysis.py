# To be used with python3

#import pyproj
import os, sys, subprocess
os.environ["PROJ_LIB"] = r'C:\Users\bsmig\Anaconda3\envs\env\Library\share (location of epsg)'
import file_writing_main

print("Welcome to the ADS-B processing script. There are 3 options to choose from:")
print("Tabular display of data:\t1")
print("Plot data on a map:\t\t2")
print("Save data to a file:\t\t3")

try:
    user_input =int(input("Please enter your choice: "))

    if (user_input == 1):
        print("You chose tabular data display")
    elif (user_input == 2):
        print("You chose creating plots")
    elif (user_input == 3):
        print("You chose saving data to a file")
        file_writing_main.main()
    else:
        print("Unrecognized option. Choices are {1,2,3}")
        
except ValueError:
    print("ERROR: you did not enter {1,2,3}. Oops-a-doodle...")
