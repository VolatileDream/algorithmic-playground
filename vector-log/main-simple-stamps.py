#!/usr/bin/env python3

from clock import VectorClock
from util import takes_args

import base64
import itertools
import json

def to_binary(clk):
  return str(base64.b64encode(bytes(json.dumps(clk.clock), "utf8")), "utf8")


def from_binary(content):
  return VectorClock(json.loads(str(base64.b64decode(content), "utf8")))


class ClockApp(object):

  @takes_args
  def new_clock(self, participant):
    print(to_binary(VectorClock().increment(participant)))

  @takes_args
  def increment(self, participant, clock):
    print(to_binary(clock.increment(participant)))

  @takes_args
  def sync(self, participant, clocks):
    """
    Properly synchronize the clocks (ie, max over all keys), and increment our clock.
    """
    clock = clocks[0]
    for c in clocks[1:]:
      clock = clock.join(c)

    print(to_binary(clock.increment(participant)))

  @takes_args
  def list(self, clock):
    for p in clock.participants():
      print("%s :: %s" % (p, clock[p]))

  @takes_args
  def orderable(self, clocks):
    keys = set()
    for c in clocks:
      keys.update(set(c.participants()))

    ordered_keys = list(keys)

    # Convert clocks into tuples, python can sort those for us. :)
    tuples = []
    for c in clocks:
      args = []
      # It is imperative all the tuples have the same key ordering.
      for p in ordered_keys:
        args.append(c[p] or 0) # need to set default
      tuples.append(tuple(args))

    # Sort!
    tuples = sorted(tuples)

    # Now validate that it's a vector-clock ordering.
    prev = tuples[0]
    for tup in tuples[1:]:
      for p,c in itertools.zip_longest(prev, tup):
        # every item in adjacent tuples must follow this.
        if not p <= c:
          return 1
      prev = tup
    return 0
      

  @takes_args
  def increasing(self, clocks):
    if len(clocks) < 2:
      return 0

    prev = clocks[0]
    for clock in clocks[1:]:
      if not prev <= clock:
        return 1
      prev = clock

    return 0


def parser(commands):
  import argparse
  parser = argparse.ArgumentParser()

  parser.add_argument(
    "command",
    default=None,
    type=str,
    choices=commands,
    help="Command to run.")

  parser.add_argument(
    "--participant", "-p",
    default=None,
    type=str,
    help="Run command for a specific participant.")

  parser.add_argument(
    "clock",
    nargs="*",
    type=from_binary,
    help="Vector Clocks")

  return parser


def main(raw_args):
  # Normalize all of these to accept (participant, clocks)
  commands = {
    "increasing?": ClockApp.increasing,
    "increment": ClockApp.increment,
    "init": ClockApp.new_clock,
    "list": ClockApp.list,
    "orderable?": ClockApp.orderable,
    "sync": ClockApp.sync,
  }

  args = parser(commands.keys()).parse_args(raw_args)

  app = ClockApp()
  rc = commands[args.command](app, args)
  if rc:
    sys.exit(rc)

if __name__ == "__main__":
  import sys
  main(sys.argv[1:])

