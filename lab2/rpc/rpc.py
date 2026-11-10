import constRPC

import time 
import threading

from context import lab_channel


class DBList:
    def __init__(self, basic_list):
        self.value = list(basic_list)

    def append(self, data):
        self.value = self.value + [data]
        return self

class ResultWaiter(threading.Thread):
    def __init__(self, channel, server, callback):
        threading.Thread.__init__(self)
        self.chan = channel          # derselbe Channel wie im Hauptthread
        self.server = server      # von wem das Ergebnis kommt
        self.callback = callback  # Funktion des Anwenders

    def run(self):
        msgrcv = self.chan.receive_from(self.server)  # blockiert - aber nur diesen Thread
        self.callback(msgrcv[1])                      # Ergebnis an Callback übergeben

class Client:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.client = self.chan.join('client')
        self.server = None

    def run(self):
        self.chan.bind(self.client)
        self.server = self.chan.subgroup('server')

    def stop(self):
        self.chan.leave('client')

    def append(self, data, db_list, callback):
        assert isinstance(db_list, DBList)
        msglst = (constRPC.APPEND, data, db_list)  # Request bauen
        self.chan.send_to(self.server, msglst)     # Request senden

        ack = self.chan.receive_from(self.server)  # nur auf das ACK warten
        assert ack[1] == constRPC.OK               # prüfen, dass es wirklich ein ACK ist

        waiter = ResultWaiter(self.chan, self.server, callback)
        waiter.start()                             # Thread wartet ab jetzt aufs Ergebnis
        return waiter                              # damit der Aufrufer später join() kann


class Server:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.server = self.chan.join('server')
        self.timeout = 3

    @staticmethod
    def append(data, db_list):
        assert isinstance(db_list, DBList)  # - Make sure we have a list
        return db_list.append(data)

    def run(self):
        self.chan.bind(self.server)
        while True:
            msgreq = self.chan.receive_from_any(self.timeout)  # wait for any request
            if msgreq is not None:
                client = msgreq[0]  # see who is the caller
                msgrpc = msgreq[1]  # fetch call & parameters
                if constRPC.APPEND == msgrpc[0]:  # check what is being requested
                    self.chan.send_to({client}, constRPC.OK)    # 1. sofort ACK senden
                    print("ACK gesendet, bearbeite Request ...")
                    time.sleep(10)                              # 2. lange Arbeit simulieren
                    result = self.append(msgrpc[1], msgrpc[2])  # 3. lokaler Aufruf
                    self.chan.send_to({client}, result)         # 4. Ergebnis senden
                    print("Ergebnis gesendet")
                else:
                    pass  # unsupported request, simply ignore
