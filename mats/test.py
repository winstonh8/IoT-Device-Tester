import logging
from numbers import Number
from typing import Optional, Union

from sigfig import round


class Test:

    """
    The most basic unit of an executing test sequence.

    Within a test, we may have a setup(), execute(), and \
    teardown() method.  Only the `execute()` method is required \
    to be overridden.

    :param moniker: a shortcut name for this particular test
    :param min_value: the minimum value that is to be considered a pass, \
    if defined
    :param max_value: the maximum value that is to be considered a pass, \
    if defined
    :param pass_if: the value that must be present in order to pass, if defined
    :param significant_figures: the number of significant figures appropriate to the measurement
    :param loglevel: the logging level to apply such as `logging.INFO`
    """

    def __init__(
        self,
        moniker: str,
        description: str,
        min_value: Optional[Number] = None,
        max_value: Optional[Number] = None,
        pass_if: Optional[Union[str, bool, int]] = None,
        significant_figures=4,
        loglevel=logging.INFO,
    ):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(loglevel)

        criteria = {}
        if pass_if is not None:
            criteria["pass_if"] = pass_if
        if min_value is not None:
            criteria["min"] = min_value
        if max_value is not None:
            criteria["max"] = max_value

        self.moniker = moniker
        self.description = description
        self.__criteria = criteria if criteria else None
        self._significant_figures = significant_figures

        self._test_is_passing = None
        self.value = None
        self.aborted = False
        self.status = "waiting"
        self.runStatus = True

        self.saved_data = {}

    @property
    def is_passing(self):
        """
        Returns `True` if test is currently passing, else `False`

        :return: `True` if passing, else `False`
        """
        return self._test_is_passing

    @property
    def criteria(self):
        """
        Returns the test criteria as a `dict`

        :return: test criteria as a `dict`
        """
        return self.__criteria

    @property
    def get_run_status(self):
        return self.runStatus

    def set_run_status(self, runsts):
        self.runStatus = runsts

    def abort(self):
        """
        Causes current test status to abort

        :return: None
        """
        self.aborted = True

    def _execute(self, is_passing):
        """
        Pre-execution method used for logging and housekeeping.

        :param is_passing: True if the test sequence is passing up to this \
        point, else False
        :return:
        """
        self.status = "running" if not self.aborted else "aborted"
        if self.aborted:
            self._logger.warning("aborted, not executing")
            return

        self._logger.info(f'executing test "{self.moniker}"')

        # execute the test and perform appropriate rounding
        value = self.execute(is_passing=is_passing)
        if isinstance(value, Number):
            try:
                value = round(value, self._significant_figures)
            except ValueError:
                self._logger.debug(
                    f'could not apply significant digits to "{value}"')
        self.value = value

        if self.__criteria is not None:
            if self.__criteria.get("pass_if") is not None:
                if self.value != self.__criteria["pass_if"]:
                    self._logger.warning(
                        f'"{self.value}" != pass_if requirement '
                        f'"{self.__criteria["pass_if"]}", failing'
                    )
                    self.fail()
                else:
                    self._logger.info(
                        f'"{self.value}" == pass_if requirement '
                        f'"{self.__criteria["pass_if"]}"'
                    )

            if self.__criteria.get("min") is not None:
                if self.value < self.__criteria["min"]:
                    self._logger.warning(
                        f'"{self.value}" is below the minimum '
                        f'"{self.__criteria["min"]}", failing'
                    )
                    self.fail()
                else:
                    self._logger.info(
                        f'"{self.value}" is above the minimum '
                        f'"{self.__criteria["min"]}"'
                    )

            if self.__criteria.get("max") is not None:
                if self.value > self.__criteria["max"]:
                    self._logger.warning(
                        f'"{self.value}" is above the maximum '
                        f'"{self.__criteria["max"]}"'
                    )
                    self.fail()
                else:
                    self._logger.info(
                        f'"{self.value}" is below the maximum '
                        f'"{self.__criteria["max"]}"'
                    )

        self.status = "running" if not self.aborted else "aborted"

        return self.value

    def _teardown(self, is_passing):
        """
        Pre-execution method used for logging and housekeeping.

        :param is_passing: True if the test sequence is passing up to \
        this point, else False
        :return:
        """
        if self.aborted:
            self.status = "aborted"
            self._logger.warning("aborted, not executing")
            return

        self._logger.info(f'tearing down "{self.moniker}"')

        self.teardown(is_passing)
        self.status = "complete"

    def reset(self):
        """
        Reset the test status
        :return: None
        """
        self.status = "waiting"

    def save_dict(self, data: dict):
        """
        Allows a test to save additional data other than that returned \
        by ``execute()``

        :param data: key: value pairs of the data to be stored
        :return: None
        """
        self.saved_data = data.copy()

    def fail(self):
        """
        When called, will cause the test to fail.

        :return: None
        """
        self._test_is_passing = False

    def execute(self, is_passing):
        """
        :param is_passing: True if the test sequence is passing up to this \
        point, else False
        :return: value to be appended to the sequence dictionary
        """
        # pass commands and expected response to parser.py
        self.got_resp = self.ser.sendRec(self.cmd)
        # should return a (key, value) which are the results of the test
        print("got_resp: " + self.got_resp)

        '''
        NOTICE THAT YOU TAKE GOT_RESP AND TURN INTO STRING!!
        '''

        return str(self.got_resp)

    def teardown(self, is_passing):
        """
        Abstract method intended to be overridden by subclass

        :param is_passing: True if the test sequence is passing up to this \
        point, else False
        :return: None
        """
        pass
