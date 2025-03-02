import coloredlogs
import logging


from mats.test import Test
from mats.test_sequence import TestSequence
from mats.tkwidgets import MatsFrame
from mats.version import __version__

__all__ = ["Test", "TestSequence",
           "ArchiveManager", "MatsFrame", "__version__"]

coloredlogs.install(level="DEBUG")

logger = logging.getLogger(__name__)
