"""
Package intended to provide extra, non-core functionality to the SCAMP (Suite for Computer-Assisted Music in Python)
framework for music composition. This package is the place for models of music-theoretical concepts (e.g. scales,
pitch-class sets), conveniences for interacting with various types of input and output, and in general anything that
builds upon SCAMP but is outside of the scope of the main framework.

The package is split into several subpackages according to the nature of the content: The pitch subpackage contains
tools for manipulating pitches, such as scales and intervals; the rhythm subpackage contains tools for creating and
interacting with rhythms and meters; the interaction subpackage contains utilities for human interface devices and
other live interactions; the supercollider subpackage contains utilities for embedding supercollider code within
SCAMP scripts; and the composers subpackage contains composer-specific tools and theoretical devices.
"""