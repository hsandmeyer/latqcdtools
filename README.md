### Description

This is a collection of tools designed for statistical analysis of data in lattice Quantum Chromo Dynamics.
Most tools are written in python.

You are probably here to use the generalized fitting routine for staggered meson correlators.
Run `bin/corrfitter.py --help` for further details
You might want to [look](https://pub.uni-bielefeld.de/download/2936264/2936265/thesis_sandmeyer.pdf) here as well

If you are looking for the generalized fitting routine for correlated data: See `latqcdtools/fitting.py`

### Installation
To run those programs you need to have python3 somewhere in your $PATH.
Additionally you have to define the environment variable PYTHONPATH containing the path
to the root folder of this project.
e.g. put

export PYTHONPATH="${PYTHONPATH}:/path/to/your/latqcdtools/"

into your .bashrc.

Requires python3.6 and above
  
