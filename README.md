# IoT Device Tester

## Table of contents

* [General info](#general-info)
* [Technologies](#technologies)
* [Setup](#setup)

### General Info 

This program is built to take long strings of input from a serial device
Parse those strings out to a point where they are clear to read and reuseable
Display the parsed info out to the user over a GUI
Send all important data to a mariaDB docker container
Log any errors encountered both locally and over to the database

### Technologies

#### PySerial

Establish the serial connection and for handling the sending and receiving data over the serial port

#### Logging

Take any errors thrown and log them into an existing log.json file with proper logging format
(If log.json doesn't exit it will create it)

#### json

For creating the the config file to pass the needed data over to the parser and to create the correct file to log errors too

#### PyUSB

To iterate through plugged in USB devices and find the intended device, performed through the hexadecimal USB vendorID

#### Re

Uses ReGex tools to iterate through certain strings to find requested information and print them out into strings and assign them a variable name
