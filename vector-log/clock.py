
from copy import copy
import enum
import inspect
import itertools
import operator

class VectorClock(object):
  __slots__ = ["clock"]

  def __init__(self, content=None):
    if content is None:
      content = dict()
    self.clock = content

  # Going to mutate clock, copy & send new one.
  def increment(self, key):
    cpy = copy(self.clock)
    if key not in cpy:
      cpy[key] = 1
    else:
      cpy[key] += 1
    return VectorClock(cpy)

  def join(self, other):
    """
    Join two clocks by taking the max of all their values.

    IMPORTANT NOTE: do not use the raw clock value from this function.
    Increment your participant key before sharing it!
    """
    our_keys = set(self.clock.keys())
    other_keys = set(other.content.keys())
    all_keys = our_keys.union(other_keys)

    values = {}
    for key in all_keys:
      values[key] = max(self[key] or 0, other[key] or 0)

    return VectorClock(values)

  def participants(self):
    return self.clock.keys()

  def __getitem__(self, key):
    if key in self.clock:
      return self.clock[key]
    return None

  def __same_keys(self, other):
    keys = set(self.clock.keys())
    other_keys = set(other.content.keys())
    return len(keys.symmetric_difference(other_keys)) == 0

  def __op(self, other, op):
    if not self.__same_keys(other):
      return False
    for key in self.clock:
      if not op(self.clock[key], other.content[key]):
        return False
    return True

  # None of the operators can be defined in terms of each other because
  # they all have to return false when the keys mismatch.
  def __le__(self, other):
    return self.__op(other, operator.le)

  def __lt__(self, other):
    return self.__op(other, operator.lt)

  def __ge__(self, other):
    return self.__op(other, operator.ge)

  def __gt__(self, other):
    return self.__op(other, operator.gt)

  def __eq__(self, other):
    return self.__op(other, operator.eq)

  def compare(self, other):
    # Reimplement comparison logic. It's faster.
    if not self.__same_keys(other):
      return ClockOrder.Unordered

    valid_ops = {
      operator.le: True,
      operator.eq: True,
      operator.ge: True,
    }

    for key in self.clock:
      for v in valid_ops:
        valid_ops[v] &= v(self.clock[key], other.content[key])

    if valid_ops[operator.eq]:
      return ClockOrder.Equal
    elif valid_ops[operator.le]:
      return ClockOrder.Before
    elif valid_ops[operator.ge]:
      return ClockOrder.After

    # Keys have funny pattern.
    return ClockOrder.Unordered


class ClockOrder(enum.Enum):
  Before = -1
  Equal = 0
  After = 1
  Unordered = 2


