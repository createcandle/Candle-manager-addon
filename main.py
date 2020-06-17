"""MySensors adapter for Mozilla WebThings Gateway."""

from os import path
import functools
import signal
import sys
import time

sys.path.append(path.join(path.dirname(path.abspath(__file__)), 'lib'))

from pkg.candle_adapter import CandleAdapter  # noqa


_DEBUG = False
_HANDLER = None

print = functools.partial(print, flush=True)


def cleanup(signum, frame):
    """Clean up any resources before exiting."""
    if _HANDLER is not None:
        _HANDLER.close_proxy()

    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    _HANDLER = CandleAdapter(verbose=_DEBUG)

    # Wait until the proxy stops running, indicating that the gateway shut us
    # down.
    while _HANDLER.proxy_running():
        time.sleep(2)
