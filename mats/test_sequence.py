import atexit
from datetime import datetime
import logging
from threading import Thread
import traceback
from time import sleep
from typing import List, Optional

from mats.test import Test

from py.serial_connection import SerialConnection

# State Machine - Using strings b/c we can relatively easily look
# for valid substrings to give more information in a concise way.
# For instance, one may be looking for the substring 'ready', but
# another function may look for the substring 'abort'.
# valid states:
#  - ready
#  - starting
#  - setting up
#  - executing tests
#  - tearing down
#  - complete / ready
#  - aborting
#  - aborted / ready
#  - exiting


class TestSequence:

    """
    The sequence or stack of ``Test`` objects to execute.

    The TestSequence will "knit" the sequence together by taking the test \
    objects and appropriately passing them through the automated testing \
    process.

    :param sequence: a list of Tests
    :param archive_manager: an instance of ``ArchiveManager`` which will \
    contain the path and data_format-specific information
    :param auto_run: an integer that determines how many times a test \
    sequence will be executed before stopping
    :param callback: function to call on each test sequence completion; \
    callback will be required to accept one parameter, which is the \
    dictionary of values collected over that test iteration
    :param teardown: function to call after the test sequence is complete, \
    even if there was a problem; common to have safety issues addressed here
    :param on_close: function to call when the functionality is complete; \
    for instance, when a GUI closes, test hardware may need to be de-allocated
    :param loglevel: the logging level
    """

    def __init__(
        self,
        device_info,
        sequence: List[Test],
        auto_run: Optional[int] = None,
        callback: Optional[callable] = None,
        teardown: Optional[callable] = None,
        on_close: Optional[callable] = None,
        loglevel=logging.INFO,
    ):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(loglevel)

        # protection just in case one or more of the instances contained
        # within the sequence were not instantiated properly, this will
        # instantiate them
        for i, test in enumerate(sequence):
            if not isinstance(test, Test):
                sequence[i] = test()

        if not TestSequence.__validate_sequence(sequence):
            raise ValueError("test monikers are not uniquely identified")

        self._sequence = sequence
        self._callback = callback
        self._teardown = teardown
        self._on_close = on_close
        self._auto_run = auto_run
        self._state = "ready" if not auto_run else "starting"

        self._devPid = device_info.pid
        self._devMan = device_info.manufacturer

        self._test_data = {
            "datetime": str(datetime.now()),
            "pass": True,
            "failed": [],
        }

        self.current_test = None
        self._current_test_number = 0

        if self._teardown is not None:
            atexit.register(self._teardown_function)

        self._thread = Thread(target=self._run_sequence, daemon=True)
        self._thread.start()
    
    def getPid(self):
        return self._devPid
    
    def getMan(self):
        return self._devMan

    @property
    def tests(self):
        """
        Returns instances of all tests contained within the ``TestSequence``

        :return: all tests as a list
        """
        return [test for test in self._sequence]

    @property
    def test_names(self):
        """
        Returns the names of the tests contained within the ``TestSequence``

        :return: the names of the tests as a list
        """
        return [test.moniker for test in self._sequence]

    @property
    def ready(self):
        """
        Returns True if the test sequence is ready for another go at it, \
        False if not

        :return: True or False
        """
        return "ready" in self._state

    @property
    def is_passing(self):
        """
        Returns True if the test sequence is currently passing, else False

        :return: True or False
        """
        return self._test_data.get("pass")

    @property
    def is_aborted(self):
        """
        Returns True if the test sequence has been aborted, else False

        :return: True or False
        """
        return "abort" in self._state

    @property
    def failed_tests(self):
        """
        Return a list of the tests which failed.

        :return: list of tests that failed
        """
        return self._test_data.get("failed")

    @property
    def progress(self):
        """
        Returns a tuple containing (current_test_number, total_tests) in \
        order to give an indication of the progress of the test sequence.

        :return: tuple containing (current_test_number, total_tests)
        """
        return (
            self._current_test_number,
            len([test.moniker for test in self._sequence]),
        )

    @property
    def in_progress(self):
        """
        Returns True if the test sequence is currently in progress, else False.

        :return: True if the test sequence is currently in progress, else False
        """
        return "ready" not in self._state

    def close(self):
        """
        Allows higher level code to call the close functionality.
        """
        self._state = "exiting"
        if self._on_close is not None:
            self._on_close()

    @staticmethod
    def __validate_sequence(sequence: List[Test]):
        moniker_set = set([t.moniker for t in sequence])

        if len(moniker_set) != len(sequence):
            return False

        return True

    def abort(self):
        """
        Abort the current test sequence.

        :return: None
        """
        if "ready" not in self._state:
            self._state = "aborting"
            [test.abort() for test in self._sequence]

    def start(self):
        """
        Start a test sequence.  Will only work if a test sequence isn't \
        already in progress.

        :return: None
        """
        if self.in_progress:
            self._logger.warning(
                "cannot begin another test when test is " "currently in progress"
            )
            return

        self._state = "starting"

    def _teardown_function(self):
        self._logger.info(
            "tearing down test sequence by " "executing sequence teardown function"
        )

        try:
            self._teardown()
        except Exception as e:
            self._logger.critical(
                f"critical error during " f"test teardown: {e}")
            self._logger.critical(str(traceback.format_exc()))

    def _reset_sequence(self):
        """
        Initializes the test sequence data, initializes each \
        `Test` in preparation for the next single execution \
        of the sequence.
        """
        if ("complete / ready" in self._state or "aborted / ready" in self._state):
            for test in self._sequence:
                test.reset()

    def _run_sequence(self):
        """
        Runs one instance of the test sequence.

        :return: None
        """
        while self._state != "exiting":
            # wait at the ready (unless in auto-run mode)
            while "ready" in self._state:
                if self._auto_run and "abort" not in self._state:
                    self._logger.info(
                        '"auto_run" flag is set, ' "beginning test sequence"
                    )
                    self.start()
                else:
                    sleep(0.1)

            if self._state == "exiting":
                self._sequence_teardown()
                return

            self._sequence_setup()
            self._sequence_executing_tests()
            self._sequence_teardown()

            if self._auto_run:
                self._auto_run -= 1

            if "abort" in self._state:
                self._state = "aborted / ready"
            else:
                self._state = "complete / ready"

    def _sequence_setup(self):
        if "abort" in self._state:
            return

        self._state = "setting up"
        self._logger.info("-" * 80)
        self._test_data = {
            "datetime": str(datetime.now()),
            "pass": True,
            "failed": [],
        }

        self._current_test_number = 0

        for test in self._sequence:
            test.reset()

    def _sequence_executing_tests(self):
        if "abort" in self._state:
            return

        # begin the test sequence
        for i, test in enumerate(self._sequence):
            self._current_test_number = i

            if test.get_run_status == False:
                self._logger.info(
                    f"test " f"{i} not selected to be run, moving on"
                )
                continue

            if "abort" in self._state:
                self._logger.warning(
                    f"abort detected on test " f"{i}, exiting test sequence"
                )
                break

            self.current_test = test.moniker

            if test.aborted:
                self.abort()
                break

            try:
                test._execute(is_passing=self.is_passing)
            except Exception as e:
                self._logger.critical(
                    f"critical error during " f'execution of "{test}": {e}'
                )
                self._logger.critical(str(traceback.format_exc()))
                self.abort()
                test.fail()

            if test.aborted:
                self.abort()
                test.fail()
                break

            try:
                test._teardown(is_passing=self.is_passing)
            except Exception as e:
                self._logger.critical(
                    f"critical error during " f'teardown of "{test}": {e}'
                )
                self._logger.critical(str(traceback.format_exc()))
                self.abort()
                test.fail()

            if test.aborted:
                self.abort()
                break

            if not test._test_is_passing:
                self._test_data["pass"] = False
                self._test_data["failed"].append(test.moniker)

        if "abort" in self._state:
            self._test_data["pass"] = None

    def _sequence_teardown(self):
        """
        Finishes up a test sequence by saving data, executing teardown \
        sequence, along with user callbacks.
        :return:
        """
        if "abort" not in self._state:
            self._state = "tearing down"

        self._logger.info("test sequence complete")
        self._logger.debug(f"test results: {self._test_data}")

        if self._teardown is not None:
            try:
                self._teardown()
            except Exception as e:
                self._logger.critical(
                    f"an exception has occurred which "
                    f"may result in an unsafe condition "
                    f"during sequence teardown: {e}"
                )

        if self._callback is not None:
            self._logger.info(
                f"executing user-supplied callback function " f'"{self._callback}"'
            )
            try:
                self._callback(self._test_data)
            except Exception as e:
                self._logger.warning(
                    f"an exception occurred during the callback sequence: {e}"
                )

    #method to connect device for connect button
    def _connect_device(self):
        #make sure tests aren't being run right now before running command
        if (self._state == "complete / ready" or self._state == "aborted / ready"):
            self.ser = SerialConnection()

            for test in self._sequence:
                test.ser = self.ser