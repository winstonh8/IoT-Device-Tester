"""
   Takes data sent over serial port
   parses it out to the console
   allows for commands to be sent to the serial device

  Copyright (c) 2022 Simply Embedded Inc.
  All Rights Reserved.
 """

#!/usr/bin/env python3
import serial
import serial.tools.list_ports


class SerialConnection():
    """
    Initialize a serial connection through searching for specific PID and MID 
    Prompt the user for input and write that input to the serial device
    Take the output from the command and parse it out and display to the user 
    """

    def __init__(self):
        """
        Looks through the list of comports compares all items in the list to the desired PID and Manufacturer ID
        Then if a device match is found it assigns the variable dev to the device path
        It then checks if dev contains no device then it will spit out an error
        If no errors arise then will perform the set up of the serial connection using the dev variable
        """

        dev = ''
        for a in serial.tools.list_ports.comports(True):
            print(a.manufacturer)
            print(a.pid)
            if a.pid == 24577 and a.manufacturer == 'FTDI':
                dev = a.device
                self.devPid = a.pid
                self.devMan = a.manufacturer
                print(dev)
                print("\nSERIAL: Found Sense at " + dev)
                break

        if dev == '':
            print(
                "\n\SERIAL ERROR: Could not locate scanner, is it plugged in? Exiting... \n\n")
            exit()
    
        else:
            self.ser = serial.Serial(
                port=dev, baudrate=115200, timeout=1)
            read = self.ser.readall().decode()
            print(read)

    #getter for the device PID
    def getPID(self):
        return str(self.devPid)

    #getter fromt the device manufacturer
    def getManufacturer(self):
        return self.devMan

    def sendRec(self, userIn):
        """
        takes the user input received in the displayInfo() function and writes that input to the serial device 
        then takes that input and splits it on the provided terminator and will just print the outcome of the command that was provided 

        """
        self.ser.write(bytes(userIn, 'utf-8'))
        # splits the output of the user submitted command on the \x03 terminator
        global read
        read = self.ser.readall().decode()
        print(read)
        return read

    def displayInfo(self):
        """
        Prompts the user for their command to send to the serial device 
        takes that input and sends it to the serial device using the sendRec() function
        then prints the response from the serial device 
        """
        while True:
            userIn = input("enter: ")
            if userIn == "exit":
                print("EXITING PROGRAM\n")
                quit()
            else:
                serialOut = self.sendRec(userIn)
                # used to display everything after command provided by userIn()
                print("response: %s " % read)


if __name__ == "__main__":
    ser = SerialConnection()
    ser.displayInfo()
