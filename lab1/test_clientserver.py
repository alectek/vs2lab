"""
Simple client server unit test
"""

import logging
import threading
import unittest

import clientserver
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)


class TestEchoService(unittest.TestCase):
    """The test"""
    _server = clientserver.Server()  # create single server in class variable
    _server_thread = threading.Thread(target=_server.serve)  # define thread for running server

    @classmethod
    def setUpClass(cls):
        cls._server_thread.start()  # start server loop in a thread (called only once)

    def setUp(self):
        super().setUp()
        self.client = clientserver.Client()  # create new client for each test


    def test_01_get_existing(self):
           """Testet das Abrufen eines existierenden Eintrags."""
           number = self.client.get("Alec")
           self.assertEqual(number, "0721-12345")
   
    def test_02_get_non_existing(self):
           """Testet das Verhalten, wenn ein Name nicht im Telefonbuch existiert."""
           response = self.client.get("Peter")
           self.assertTrue(response.startswith("ERROR"))
   
    def test_03_get_all(self):
        """Testet das Abrufen des gesamten Telefonbuchs als Dictionary."""
        phonebook = self.client.get_all()
        self.assertIsInstance(phonebook, dict)
        self.assertIn("Alec", phonebook)
        self.assertIn("Artemis", phonebook)
        self.assertEqual(phonebook["Charlie"], "0176-11223344")
   
   
    @classmethod
    def tearDownClass(cls):
        cls._server._serving = False  # break out of server loop. pylint: disable=protected-access
        cls._server_thread.join()  # wait for server thread to terminate




if __name__ == '__main__':
    unittest.main()
