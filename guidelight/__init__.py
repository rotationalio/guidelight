"""
A library for developing task-oriented AI systems that integrate with Endeavor.
"""

##########################################################################
## Module Info
##########################################################################

# Import the version number at the top level
from .version import get_version, __version_info__


##########################################################################
## Package Version
##########################################################################

__version__ = get_version(short=True)
