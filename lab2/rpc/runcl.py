import logging
import time

import rpc

from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)


def print_result(result_list):
    """Callback: wird im Warte-Thread aufgerufen, sobald das Ergebnis da ist."""
    print("Callback: Ergebnis = {}".format(result_list.value))


cl = rpc.Client()
cl.run()

base_list = rpc.DBList({'foo'})
waiter = cl.append('bar', base_list, print_result)  # kehrt nach dem ACK zurück
print("ACK erhalten - Client macht weiter")

seconds = 0
while waiter.is_alive():          # solange der Thread noch aufs Ergebnis wartet
    seconds += 1
    print("Client ist aktiv ... {} s".format(seconds))
    time.sleep(1)

waiter.join()                     # sicherstellen, dass der Thread fertig ist
cl.stop()