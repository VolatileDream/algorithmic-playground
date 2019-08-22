
import inspect

def takes_args(fn):

  def wrapper(self, args):
    invocation = {}
    arg_names = inspect.signature(fn).parameters.keys()
    for name in arg_names:
      if name == "participant":
        if args.participant is None:
          raise Exception("participant unset")
        invocation["participant"] = args.participant
      elif name == "clock":
        invocation["clock"] = args.clock[0]
      elif name == "clocks":
        invocation["clocks"] = args.clock

    return fn(self, **invocation)
        
  return wrapper
