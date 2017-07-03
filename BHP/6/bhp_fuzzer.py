#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Burp 模糊测试

from burp import IBurpExtender
from burp import IIntruderPayloadGeneratorFactory
from burp import IIntruderPayloadGenerator

from java.util import List, ArrayList

import random

class BurpExtender(IBurpExtender, IIntruderPayloadGeneratorFactory):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        callbacks.registerIntruderPayloadGeneratorFactory(self)
        return

    def getGeneratorName(self):
        return "BHP Payload Generator"

    def createNewInstance(self, attack):
        return BHPFuzzer(self, attack)

class BHPFuzzer(IIntruderPayloadGenerator):
    def __init__(self, extender, attack):
        self._extender = extender
        self._helpers  = extender._helpers
        self._attack = attack
        print "BHP Fuzzer initialized"
        self.max_payloads = 1000
        self.num_payloads = 0
        return

    def hasMorePayloads(self):
        print "hasMorePayloads called."
        if self.num_payloads == self.max_payloads:
            print "No more payloads."
            return False
        else:
            print "More payloads. Continuing."
            return True

    def getNextPayload(self, current_payload):
        payload = "".join(chr(x) for x in current_payload)    # Convert into a string
        payload = self.mutate_payload(payload)    # Call our simple mutator to fuzz the POST
        self.num_payloads += 1    # Increase the number of fuzzing attempts
        return payload

    def reset(self):
        self.num_payloads = 0
        return

    def mutate_payload(self, original_payload):
        # Pick a simple mutator or even call an external script like Radamsa does
        picker = random.randint(1, 3)
        # Select a random offset in the payload to mutate
        offset  = random.randint(0, len(original_payload)-1)
        payload = original_payload[:offset]

        # Random offset insert a SQL injection attempt
        if picker == 1:
            payload += "'"

        # Jam an XSS attempt in
        if picker == 2:
            payload += "<script>alert('BHP!');</script>";

        # Repeat a chunk of the original payload a random number
        if picker == 3:
            chunk_length = random.randint(len(payload[offset:]), len(payload)-1)
            repeater = random.randint(1, 10)

            for i in range(repeater):
                payload += original_payload[offset:offset+chunk_length]

        payload += original_payload[offset:]    # Add the remaining bits of the payload

        return payload