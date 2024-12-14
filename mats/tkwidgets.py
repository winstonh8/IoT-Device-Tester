import logging
from tkinter import *

from mats.test import Test
from mats.test_sequence import TestSequence

_light_green = "#66ff66"
_light_red = "#ff6666"
_light_yellow = "#ffff99"
_relief = "sunken"
_label_padding = 5


class MatsFrame(Frame):

    """
    The frame that interacts with the test sequence to display the \
    test results as the test is executing.

    :param parent: the tk parent frame
    :param sequence: the instance of `TestSequence` to monitor
    :param vertical: if `True`, will stack tests vertically; \
        otherwise, horizontally; default is vertical, `True`
    :param start_btn: if `True`, will populate a start button; \
        otherwise, will not; default is `True`
    :param abort_btn: if `True`, will populate an abort button; \
        otherwise, will not; default is `True`
    :param wrap: the number above which will start the next row or column
    :param loglevel: the logging level, for instance 'logging.INFO'
    """

    def __init__(
        self,
        parent,
        sequence: TestSequence,
        vertical: bool = True,
        start_btn: bool = True,
        abort_btn: bool = True,
        wrap: int = 6,
        loglevel=logging.INFO,
    ):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(loglevel)

        self._parent = parent
        super().__init__(self._parent)

        self._sequence = sequence

        devPid = self._sequence.getPid()
        devMan = self._sequence.getMan()

        arrow = "\u2b9e"

        row = 0
        col = 0

        #place start and abort buttons

        btn_frame = Frame(self)
        btn_frame.grid(row=0, column=0, sticky="news")
        btn_frame.columnconfigure(0, weight=1)
        r = 0

        Button(btn_frame, text="Start", command=sequence.start).grid(
            row=r, column=0, sticky="news"
        )
        r += 1

        Button(btn_frame, text="ABORT", command=sequence.abort, fg="red").grid(
            row=r, column=0, sticky="news"
        )
        
        Label(self, text = "Device Information:\nPID: " + devPid + "\nManufacturer: " + devMan, anchor = "w").grid(
            row = 0, column = 1)

        #create label frame
        status_frame = Frame(self)
        Label(self, text=arrow, justify="center", anchor="center").grid(
            row=0, column=1, sticky="news"
        )
        status_frame.grid(row=0, column=2)

        col += 1

        # take list of all tests in sequence and create a label, description label and checkbox for each
        self._test_status_frames = []
        self._test_status_checkbox = []
        self._test_status_description = []
        self._test_serial_output = []
        for test in self._sequence.tests:
            self._test_status_frames.append(
                _TestLabel(
                    status_frame, test, loglevel=self._logger.getEffectiveLevel()
                )
            )
            self._test_status_checkbox.append(
                _TestCheck(
                    status_frame, self._sequence, test, loglevel=self._logger.getEffectiveLevel()
                )
            )
            self._test_status_description.append(
                _TestDesc(
                    status_frame, test, loglevel=self._logger.getEffectiveLevel()
                )
            )
            self._test_serial_output.append(
                _TestOutput(
                    status_frame, test, loglevel=self._logger.getEffectiveLevel()
                )
            )

        # take each checkbutton, label and descrption label and place on the grid
        row, col = 0, 0
        max_row = row
        max_col = col
        # for each test
        for tl, tcb, tdl, tso in zip(self._test_status_frames, self._test_status_checkbox, self._test_status_description, self._test_serial_output):
            # put on the grid, then increment row to place next label
            if vertical:
                tcb.grid(row=row, column=col, sticky="news")
                tl.grid(row=row, column=col + 1, sticky="news")
                tdl.grid(row=row, column=col + 2, sticky="news")
                tso.grid(row=row, column=col + 3, sticky="news")

                row += 1
                row %= wrap
                if row == 0:
                    col += 1
            else:
                tl.grid(row=row, column=col, sticky="news")

                col += 1
                col %= wrap
                if col == 0:
                    row += 1

            max_row = max(row, max_row)
            max_col = max(col, max_col)

        col += 1

        #add select/deselect all tests button that will toggle all checkbuttons
        selectButton = Button(btn_frame, text="Select/Deselect All Tests", command=self._updateAllStates).grid(row=row, column=col, sticky="news")

        #add reset button to reset all tests
        resetButton = Button(btn_frame, text="Reset All Tests", command=lambda: [self._resetAllStates(), sequence._reset_sequence()]).grid(
            row=row + 1, column=col, sticky="news")

        connectButton = Button(btn_frame, text = "Connect Device", command = sequence._connect_device).grid(
            row = row + 2, column = col, sticky = "news")

        self._complete_label = Label(
            self, text="-", anchor="center", justify="center")
        if vertical:
            self._complete_label.grid(row=2, column=0, sticky="news")
        else:
            self._complete_label.grid(row=0, column=3, sticky="news")
        self._complete_label.config(
            relief=_relief, padx=_label_padding, pady=_label_padding
        )

        self._update()

    # function to select/deselect all checkboxes
    def _updateAllStates(self):
        #make sure test sequence isn't running
        if ("complete / ready" in self._sequence._state or "aborted / ready" in self._sequence._state):
            # check to see if all the checkboxes are selected or not; default they are
            allRun = True
            # look through all checkbuttons; if one is off, then they are not all on
            for checkbutton in self._test_status_checkbox:
                if checkbutton._value.get() == 0:
                    allRun = False
                    break
            # if they're all on, deselect all
            if allRun == True:
                for checkbutton in self._test_status_checkbox:
                    checkbutton._value.set(0)
                    checkbutton._test.set_run_status(False)
            # otherwise select all
            else:
                for checkbutton in self._test_status_checkbox:
                    checkbutton._value.set(1)
                    checkbutton._test.set_run_status(True)
        
    #will reset checkbuttons if the state of the sequence is completed and read or aborted and ready
    def _resetAllStates(self):
        if (self._sequence._state == "complete / ready" or self._sequence._state == "aborted / ready"):
            for checkbutton in self._test_status_checkbox:
                checkbutton._value.set(1)
                checkbutton._test.set_run_status(True)
                checkbutton.config(state=NORMAL)

    def _update(self):
        if self._sequence.in_progress:
            self._complete_label.config(
                text="in progress", background=_light_yellow)
        elif self._sequence.is_aborted:
            self._complete_label.config(text="aborted", background=_light_red)
        elif self._sequence.is_passing:
            self._complete_label.config(text="pass", background=_light_green)
        else:
            self._complete_label.config(text="fail", background=_light_red)

        self.after(100, self._update)


class _TestCheck(Checkbutton):
    """
    Class for creating checkboxes beside tests; create check boxes, place them on grid in class above, add to another list sequence to be run;
    can check for tests to be run at time of start button (command=). When button pressed, make the check boxes unclickable (state=DISABLED)
    """

    def __init__(self, parent, _sequence, test: Test, loglevel=logging.INFO):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(loglevel)

        self._parent = parent
        super().__init__(self._parent, command=self._updateState)

        self._value = IntVar(parent)
        self.config(variable=self._value)

        self._seq = _sequence
        self._test = test
        self._value.set(1)
        self._update()

    def _updateState(self):
        if self._test.get_run_status == True:
            self._test.set_run_status(False)
            self._value.set(0)
        else:
            self._test.set_run_status(True)
            self._value.set(1)

    def _update(self):
        #receive or check status of program; if waiting, leave checkbox; if tests start, grey out checkbox
        if self._seq.in_progress:
            self.config(state=DISABLED)

        self.after(100, self._update)

class _TestDesc(Label):
    """
    Single label for the description of the tests
    """
    def __init__(self, parent, test: Test, loglevel = logging.INFO):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(loglevel)

        self._parent = parent
        super().__init__(self._parent)

        self._test = test
        
        self._label_text = f"{self._test.description}"

        self.config(
            text=self._label_text,
            relief=_relief,
            padx=_label_padding,
            pady=_label_padding,
        )

class _TestLabel(Label):

    """
    A single instance of a test label frame.
    """

    def __init__(self, parent, test: Test, loglevel=logging.INFO):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(loglevel)

        self._parent = parent
        super().__init__(self._parent)

        self._test = test

        criteria = self._test.criteria
        criteria_list = []
        criteria_string = ""
        if criteria is not None:
            for condition, value in criteria.items():
                if (
                    isinstance(value, bool)
                    or isinstance(value, int)
                    or isinstance(value, str)
                ):
                    cs = f"{condition}={value}"
                else:
                    cs = f"{condition}={value}"
                criteria_list.append(cs)
            criteria_string = ",".join(criteria_list)

        self._label_text = f"{self._test.moniker}"
        if criteria_string:
            self._label_text += f"\n{criteria_string}"

        self.config(
            text=self._label_text,
            relief=_relief,
            padx=_label_padding,
            pady=_label_padding,
        )

        self._label_bg_color = self.cget("background")

        self._update()

    def _update(self):
        """
        Updates the test label display based on the status of the Test

        :return: None
        """
        color = self._label_bg_color

        if self._test.status == "waiting":
            color = self._label_bg_color
        elif self._test.status == "running":
            color = _light_yellow
        elif self._test.status == "aborted":
            color = _light_red
        elif not self._test.is_passing:
            color = _light_red
        elif self._test.is_passing:
            color = _light_green

        self.config(background=color,)

        self.after(100, self._update)


class _TestOutput(Label):
    """
    Single label for the description of the tests
    """
    def __init__(self, parent, test: Test, loglevel = logging.INFO):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(loglevel)

        self._parent = parent
        super().__init__(self._parent)

        self._test = test

        self.config(text = "output")

        self.config(
            relief=_relief,
            padx=_label_padding,
            pady=_label_padding,
        )

        self._update()
    
    def _update(self):
        """
        Updates the label based on the status of the Test
        """

        if (self._test.status == "complete"):
            self.config(text = str(self._test.got_resp))
        
        self.after(100, self._update)