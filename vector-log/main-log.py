#!/usr/bin/env python3

from clock import VectorClock
from util import takes_args

import itertools
import json

class VlEncoder(json.JSONEncoder):
  __slots__ = "decodes"
  def __init__(self, types, **kwargs):
    super().__init__(**kwargs)
    self.decodes = dict()
    for t in types:
      if hasattr(t, "from_dict") and hasattr(t, "to_dict"):
        self.decodes[t.__name__] = t
      else:
        raise Exception(
            "type %s does not implement both from_dict and to_dict" % t.__name__)

  def __supported__(self, obj):
    return type(obj).__name__ in self.decodes

  def default(self, o):
    """Overrides default of JsonEncoder."""
    if self.__supported__(o):
      d = o.to_dict()
      d["__type__"] = type(o).__name__
      return d
    return super().default(o)

  def decoder(self):
    return lambda d: self.__decode(d)

  def __decode(self, d):
    if "__type__" in d and d["__type__"] in self.decodes:
      cls = d["__type__"]
      del d["__type__"]
      return self.decodes[cls].from_dict(d)
    return d


class JsonClock(VectorClock):
  def to_dict(self):
    return sef.clock

  @staticmethod
  def from_dict(obj):
    return JsonClock(obj)


class VectorLogEntry(object):
  __slots__ = ["clock", "content", "writer"]

  def __init__(self, clock, content, writer):
    self.clock = clock
    self.content = content
    self.writer = writer

  def to_dict(self):
    return dict(
        clock=self.clock,
        content=self.content,
        writer=self.writer)

  @staticmethod
  def from_dict(js):
    return VectorLogEntry(js["clock"], js["content"], js["writer"])


class VectorLog(object):

  def __init__(self, entries=None):
    if entries is None:
      entries = []
    self.entries = entries

  def append(self, participant, content):
    # clock is not safe to use
    clock = JsonClock()
    for entry in self.entries:
      clock.join(entry.clock)
    clock.increment(participant)
    # now clock is safe to use

    entry = VectorLogEntry(clock, content, participant)
    self.entries.append(entry)

  def list(self):
    return self.entries


class LogApp(object):

  def __init__(self, io=None):
    self.encdec = VlEncoder([JsonClock, VectorLogEntry])
    self.log = None
    self.io = io

  def _log(self):
    if self.log:
      return self.log
    content = self.io.read()
    content += "]"
    self.log = json.loads(content, object_hook=self.encdec.decoder())
    return self.log

  @takes_args
  def new_log(self):
    log = VectorLog()
    log.append(None, "")
    self.log = log

  @takes_args
  def append(self, participant, content):
    self._log().append(participant, content)

  @takes_args
  def list(self):
    for entry in self._log().list():
      items = ["{}={:d}".format(p, c) for p, c in entry.clock.items()]
      clk = ",".join(items)
      print("<{}> {}:: {}".format(clk, entry.writer, entry.content))

  @takes_args
  def sync(self, other_loader):
    """
    """


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
    type=from_json,
    help="Vector Clocks")

  return parser


def main(raw_args):
  # Normalize all of these to accept (participant, clocks)
  commands = {
    "init": LogApp.new_log,
    "append": LogApp.append,
    "list": LogApp.list,
    "sync": LogApp.sync,
  }

  args = parser(commands.keys()).parse_args(raw_args)

  app = LogApp()
  rc = commands[args.command](app, args)
  if rc:
    sys.exit(rc)

if __name__ == "__main__":
  import sys
  main(sys.argv[1:])

