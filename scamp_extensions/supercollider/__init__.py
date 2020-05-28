"""
Subpackage containing tools for interfacing with SuperCollider. These tools are enabled by calling
:func:`~sc_playback_implementation.add_sc_extensions`, which adds several functions to SCAMP's
:class:`~scamp.instruments.Ensemble` and :class:`~scamp.session.Session` classes. NB: All of this functionality
assumes that you have SuperCollider installed in such a way that it can be run from the command line
(via the command "sclang").
"""

from .sc_playback_implementation import SCPlaybackImplementation, add_sc_extensions
from .sc_lang import SCLangInstance
