import logging
import json
import tkinter as tk
from py.serial_connection import SerialConnection

import coloredlogs
from mats.test import Test
from mats.test_sequence import TestSequence
from mats.tkwidgets import MatsFrame


def teardown():
    print('some kind of sequence teardown function to occur here, '
          'like turning off power supplies or putting the fixture into a safe state')


def test_complete_callback(data, string):
    print(
        f'this is the data that gets passed to a callback:\n{json.dumps(data, indent=2)}')
    print(f'added some other string: {string}')


class test_setup(Test):
    # contructor; set cmd, resp as local variables
    def __init__(self, ser, cmd, resp, desc, loglevel=logging.INFO):
        self.ser = ser
        self.cmd = cmd
        self.resp = resp
        self.desc = desc
        super().__init__(moniker=cmd, pass_if=self.resp, description=self.desc, loglevel=loglevel)

#get the device information
class device_info():
    def __init__(self, pid, manufacturer):
        self.pid = pid
        self.manufacturer = manufacturer
        
if __name__ == '__main__':

    # instance serial connection
    ser = SerialConnection()
    # print(ser)

    coloredlogs.install(level=logging.DEBUG)
    # instantiate the json file
    config = json.load(open("test_config.json"))

    # create new variable of just a list of lists from the json dictionary
    cli_tests = config['cli_tests']

    device_info = device_info(ser.getPID(), ser.getManufacturer())

    sequence = []
    # loop through cli_tests list and pass commands/responses to test functions, then add that function to the sequence
    for a in cli_tests:
        cmd = a[0]
        resp = a[1]
        desc = a[2]
        test_obj = test_setup(ser, cmd, resp, desc)
        sequence.append(test_obj)

    ts = TestSequence(teardown=lambda: teardown(),
                      device_info=device_info,
                      sequence=sequence,
                      callback=lambda data: test_complete_callback(
                          data, 'my string!'),
                      loglevel=logging.DEBUG)
    # instantiate gui
    window = tk.Tk()

    tkate_frame = MatsFrame(window, ts, vertical=True)
    tkate_frame.grid(sticky='news')

    window.mainloop()
