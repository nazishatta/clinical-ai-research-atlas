"""Shared colour palette, chosen for colour-vision deficiency and a dark theme.

Okabe-Ito categorical colours, reordered so the first colours are the ones with
the most contrast on the dark plot background (#1B222C):

* every colour is at least 3:1 against the plot background (WCAG 1.4.11 for
  graphical objects); the first six are at least 4.1:1;
* under simulated protanopia, deuteranopia and tritanopia the closest pair
  among the first six still differs by CIE76 delta-E >= 16.

The previous pastel palette fell to delta-E 4.3 between two of its first four
colours under deuteranopia, which is effectively indistinguishable.

Colour is never the only encoding: charts also use line dash, marker shape,
direct labels, hover text and the accessible data tables.
"""
CATEGORICAL = ['#56B4E9', '#E69F00', '#009E73', '#F0E442', '#CC79A7', '#D55E00', '#BBBBBB', '#0072B2']
NEUTRAL_EDGE = '#8A92B5'
