"""
Client and server using classes
"""
import json

import logging
import socket

import const_cs
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)  # init loging channels for the lab

# pylint: disable=logging-not-lazy, line-too-long

DELIMITER = "\n" #Trennzeichen zur Signalisierung des Endes einer Nachricht.

class Server:
    """ The server """
    _logger = logging.getLogger("vs2lab.lab1.clientserver.Server")
    _serving = True

    def __init__(self):
        # In-Memory-Datenbank als Python Dictionary (2-Tier: Datenebene)
        self.phonebook = {
            "Alec": "0721-12345",
            "Artemis": "0721-67890",
            "Charlie": "0176-11223344",
            "Dana": "0151-99887766",
            "An Tim": "0176-12345678"
        }

        #Socket anlegen
        #                                IPv4, TCP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                             
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Freigabe der Adresse nach Beendigung des Servers
        self.sock.bind((const_cs.HOST, const_cs.PORT))
        self.sock.settimeout(3)  # time out in order not to block forever
        self._logger.info("Server bound to socket " + str(self.sock))

    def serve(self):
        """ Serve directory requests """
        # Socket-Lebenszyklus: listen
        self.sock.listen(1)
        self._logger.info("Server is listening on %s:%s...", const_cs.HOST, const_cs.PORT)

        while self._serving:
            try:
                # Socket-Lebenszyklus: accept (blockiert bis ein Client anklopft)
                (connection, address) = self.sock.accept()
                self._logger.info("Connection accepted from %s", address)

                # Nachricht empfangen (bis DELIMITER gefunden wird)
                buffer = ""
                while DELIMITER not in buffer:
                    chunk = connection.recv(1024).decode('utf-8')
                    if not chunk:
                        break
                    buffer += chunk

                if buffer:
                    request = buffer.strip()
                    self._logger.info("Received request: '%s'", request)

                    # Protokoll-Auswertung
                    response = self._handle_request(request)

                    # Socket-Lebenszyklus: send
                    connection.sendall((response + DELIMITER).encode('utf-8'))
                    self._logger.info("Sent response to %s", address)

                # Socket-Lebenszyklus: close (Client-Verbindung schließen)
                connection.close()
                self._logger.info("Connection to %s closed.", address)

            except socket.timeout:
                pass  # Timeout ignorieren und prüfen, ob _serving noch True ist
            except Exception as e:
                self._logger.error("Error during serve: %s", e)

        self.sock.close()
        self._logger.info("Server socket closed. Server down.")

    def _handle_request(self, request: str) -> str:
        """ Protokoll-Logik: Verarbeitet Anfragen und generiert Antworten """
        parts = request.split(maxsplit=1)
        command = parts[0].upper()

        if command == "GETALL":
            # Liefert das gesamte Telefonbuch als JSON-String
            return json.dumps(self.phonebook)

        elif command == "GET":
            if len(parts) < 2:
                return "ERROR: Missing name for GET"
            name = parts[1]
            number = self.phonebook.get(name)
            if number:
                return number
            return f"ERROR: '{name}' not found"

        else:
            return f"ERROR: Unknown command '{command}'"


class Client:
    """ The directory service client (bietet die Auskunft-API) """
    logger = logging.getLogger("vs2lab.lab1.clientserver.Client")

    def __init__(self):
        self.sock = None

    def _send_request(self, message: str) -> str:
        """ Baut Verbindung auf, sendet Request und liest vollständige Response """
        # Socket-Lebenszyklus: socket, connect
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((const_cs.HOST, const_cs.PORT))
        self.logger.info("Client connected to socket: %s", self.sock)

        # Socket-Lebenszyklus: send
        full_message = message + DELIMITER
        self.sock.sendall(full_message.encode('utf-8'))
        self.logger.info("Sent request: '%s'", message)

        # Socket-Lebenszyklus: recv in Schleife (für große Payloads wie GETALL)
        buffer = ""
        while DELIMITER not in buffer:
            chunk = self.sock.recv(1024).decode('utf-8')
            if not chunk:
                break
            buffer += chunk

        # Socket-Lebenszyklus: close
        self.sock.close()
        self.logger.info("Client socket closed.")

        return buffer.strip()

    # --- Auskunft-API-Schnittstelle gemäß Aufgabenstellung ---

    def get(self, name: str) -> str:
        """ Operation 1: GET <name> """
        return self._send_request(f"GET {name}")

    def get_all(self) -> dict:
        """ Operation 2: GETALL """
        response = self._send_request("GETALL")
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": response}