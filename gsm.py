"""
MIT License

Copyright (c) 2023-2024  Helios  helios14_75@hotmail.fr

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import time
import json
import logging

from gsm_io         import gsm_io
from threading      import Thread, Lock
from queue          import Queue

#                 0-----------------------------------2f
sms_alpha     = ("@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ"
                 " !\"#¤%&'()*+,-./0123456789:;<=>?"
                 "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§"
                 "¿abcdefghijklmnopqrstuvwxyzäöñüà")

class gsm(gsm_io):

    ATZ = "ATZ"  # reset modem
    ATE0 = "ATE0"  # set echo off
    ATE1 = "ATE1"  # set echo on
    ATCLIP = "AT+CLIP?"  # get calling line identification presentation
    ATCMEE = "AT+CMEE=1"  # set extended error
    #ATCPIN = "AT+CPIN=\"0000\""  # set pin code
    #ATCLCK0 = "AT+CLCK=\"SC\",0,\"0000\""  # disable code pin check, pin=0000
    #ATCLCK1 = "AT+CLCK=\"SC\",1,\"0000\""  # enable code pin check, pin=0000
    ATCSCS = "AT+CSCS=\"GSM\""  # force GSM mode for SMS
    ATCMGF = "AT+CMGF=1"  # enable sms in text mode
    ATCSDH = "AT+CSDH=1"  # enable more fields in sms read
    ATCMGS = "AT+CMGS="  # send message with prompt
    ATCMGD = "AT+CMGD="  # delete messages: =0,4 -> 4 means ignore the value 0 of index and delete all SMS messages from the message storage area
    ATCMGL = "AT+CMGL="  # list all messages
    ATCMGR = "AT+CMGR="  # read message by index in storage
    ATCMGW = "AT+CMGW="  # write
    ATCMSS = "AT+CMSS="  # send message by index in storage
    ATCPMS = "AT+CPMS=\"ME\",\"ME\",\"ME\""  # storage is Mobile
    ATCSQ = "AT+CSQ"  # signal strength
    ATCREG = "AT+CREG?"  # registered on network ?
    ATCNMI = "AT+CNMI=2,1,0,0,0"  # when sms arrives CMTI send to pc

    def __init__(self, loglevel, name: str, mode: str, device: str, pin: str, auth: str, recv: str, mqtt_client):
        self.GsmReaderThread = None
        self.GsmMode = mode
        self.MQTTClient = mqtt_client
        self.ATCPIN = "AT+CPIN=\""+pin+"\""  # set pin code
        self.ATCLCK0 = "AT+CLCK=\"SC\",0,\""+pin+"\""  # disable code pin check, pin=0000
        self.ATCLCK1 = "AT+CLCK=\"SC\",1,\""+pin+"\""  # enable code pin check, pin=0000
        self.GsmIoOKReceived = None
        self.GsmIoCMSSReceived = None
        self.GsmPIN = pin
        self.Auth = auth
        self.Recv = recv
        self.Ready = False
        self.Name = name
        self.GsmApiSem = Lock()
        self.GsmMutex = Lock()
        self.SMSQueue = Queue()
        self.GsmIoPrompt = False
        self.GsmIoSmsIdReceived = False
        self.Opened = False
        self.SmsList = []
        self.GsmIoCMGLReceived = False
        self.GsmIoCMGRReceived = False
        # set logger
        # DEBUG INFO WARNING ERROR CRITICAL
        # logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
        logging.basicConfig(level=loglevel)
        gsm_io.__init__(self, loglevel, device)  # since inherited, needs to be called explicitly

    def __del__(self):
        gsm_io.__del__(self)  # since inherited, needs to be called explicitly

    def start(self):
        if self.GsmMode == "modem":
            self.Opened = self.openGsmIoDevice()
            if self.Opened:
                self.startGsmIoActivity()
                self.initGsmDevice()
                self.Ready = True
                self.startGsmReader()
            else:
                self.Ready = False
        else:
            self.Ready = True

    def stop(self):
        if self.Ready:
            self.stopGsmReader()
            self.stopGsmIoActivity()
            if self.GsmMode == "modem":
                self.closeGsmIoDevice()
        self.Ready = False

    def initGsmDevice(self):
        if self.Opened:
            logging.debug("Init GSM device")
            self.GsmApiSem.acquire()
            frame = bytes(gsm.ATZ, 'ascii')
            self.writeCommandAndWaitOK(frame)
            logging.debug("... ATZ sent")
            frame = bytes(gsm.ATE0, 'ascii')
            self.writeCommandAndWaitOK(frame)
            logging.debug("... ATE0 sent")
            frame = bytes(self.ATCPIN, 'ascii')
            self.writeCommandAndWaitOK(frame)
            logging.debug("... ATCPIN sent")
            frame = bytes(gsm.ATCMGF, 'ascii')
            self.writeCommandAndWaitOK(frame)
            logging.debug("... ATCMGF sent")
            frame = bytes(gsm.ATCNMI, 'ascii')
            self.writeCommandAndWaitOK(frame)
            logging.debug("... ATCNMI sent")
            frame = bytes(gsm.ATCSCS, 'ascii')
            self.writeCommandAndWaitOK(frame)
            logging.debug("... ATCSCS sent")
            frame = bytes(gsm.ATCPMS, 'ascii')
            self.writeCommandAndWaitOK(frame)
            logging.debug("... ATCPMS sent")
            frame = bytes(gsm.ATCLIP, 'ascii')
            self.writeCommandAndWaitOK(frame)
            logging.debug("... ATCLIP sent")
            frame = bytes(gsm.ATCSDH, 'ascii')
            self.writeCommandAndWaitOK(frame)
            logging.debug("... ATCSDH sent")
            frame = bytes(gsm.ATCMGD+"0,4", 'ascii')
            self.writeCommandAndWaitOK(frame)
            logging.debug("... ATCMGD sent")
            self.GsmApiSem.release()
            logging.debug("... Init GSM device done")
        else:
            logging.error("Init GSM device, not opened !")

    def sendSmsToNumber(self, number, message):
        if self.Opened:
            # message is string utf-8
            # has to be converted to bytes to be sent on modem
            logging.info(f"... Send SMS")
            self.GsmApiSem.acquire()
            self.GsmMutex.acquire()
            self.GsmIoSmsIdReceived = False
            self.GsmIoCMSSReceived = False
            self.GsmIoPrompt = False
            self.GsmMutex.release()
            data = gsm.ATCMGW+"\""+number+"\""
            frame = bytes(data, 'utf-8')
            self.writeCommandAndWaitOK(frame)           # writes bytes on modem
            logging.debug("... ATCMGW sent")
            while not self.GsmIoPromptReceived:
                time.sleep(0.001)
            # prepare (encode) and send message
            self.GsmIoOKReceived = False
            self.GsmIoSmsIdReceived = False
            frame = self.encodeUTF8toGSM7(message)     # encode utf-8 to gsm-7
            self.GsmIoSmsIdReceived = False
            self.writeData(frame)
            # wait transmission
            while not self.GsmIoOKReceived:
                time.sleep(0.001)
            while not self.GsmIoSmsIdReceived:
                time.sleep(0.001)
            logging.debug("... id received")
            # Id received is bytes
            data = gsm.ATCMSS+self.GsmIoMessageId.decode('ascii')
            frame = bytes(data, 'utf-8')               # writes bytes on modem
            self.writeCommandAndWaitOK(frame)
            logging.debug("... ATCMSS sent")
            # cmss will arrive before 'ok'
            self.GsmApiSem.release()
            logging.info(f"...... SMS sent")
            logging.info("")
        else:
            logging.error("GSM device, not opened !")

    # Start activity thread
    def startGsmReader(self):
        if self.Opened:
            logging.debug("Starting GSM Reader")
            self.GsmReaderThread            = Thread(target=self.runGsmReaderThread)
            self.GsmReaderThread.daemon     = True
            self.GsmReaderThread.isRunning  = True
            self.GsmReaderThread.start()
            logging.debug("... GSM Reader started")

    # Stop activity thread
    def stopGsmReader(self):
        if self.Opened:
            logging.debug("Stopping GSM Reader")
            self.GsmReaderThread.isRunning = False
            self.GsmReaderThread.join()
            logging.debug("... GSM Reader stopped")

    def runGsmReaderThread(self):
        # SMS Reader, will post to MQTT
        while getattr(self.GsmReaderThread, "isRunning", True):
            new_sms = self.readNewSms()
            # {'Id': message_id, 'Number': number, 'Status': status, 'Msg': msg}
            if new_sms is not None:
                logging.info("")
                logging.info("Receiving SMS as GSM-7 bytes string")
                new_sms['Msg'] = self.decodeGSM7toUTF8(new_sms['Msg'])
                logging.info(f"... Decoded to UTF-8 string: %s", new_sms['Msg'])
                new_sms['Msg'] = self.encodeUTF8toJSON(new_sms['Msg'])
                json_message = {"from": new_sms['Number'], "txt": new_sms['Msg']}
                logging.info("...... Publishing it to mqtt as JSON on topic sms_received")
                logging.debug(json_message)
                self.MQTTClient.publish(self.Recv, json.dumps(json_message))
            time.sleep(1)

    @staticmethod
    def encodeUTF8toJSON(bytes_message):
        # Be sure to escape " characters with \"
        logging.debug('... Encode UTF-8 to JSON')
        logging.debug(list(bytes_message))
        result = []
        for b in bytes_message:
            if b == '"':
                result.append('\\')
            result.append(b)
        return ''.join(result)

    @staticmethod
    def decodeGSM7toUTF8(bytes_message):
        logging.debug('... Decoding GSM-7 to UTF-8')
        logging.debug(list(bytes_message))
        result = []
        for b in bytes_message:         # b is code value of character
            result.append(sms_alpha[b])
        return ''.join(result)

    @staticmethod
    def encodeUTF8toGSM7(message):
        # UTF-8 double byte character will be replaced by specific
        # GSM alphabet code
        message_list = list(bytes(message, 'utf-8'))
        logging.debug('...... Encoding UTF-8 to GSM-7')
        waitCode195 = False
        waitCode194 = False
        waitCode206 = False
        result = bytes("", 'utf-8')
        for c in message_list:
            if waitCode195 is True:
                waitCode195 = False
                if c == 132:
                    result += b'\x5b'   # --> Ä
                elif c == 133:
                    result += b'\x0e'   # --> Å
                elif c == 135:
                    result += b'\x09'   # --> Ç
                elif c == 137:
                    result += b'\x1f'   # --> É
                elif c == 145:
                    result += b'\x5d'   # --> Ñ
                elif c == 150:
                    result += b'\x5c'   # --> Ö
                elif c == 152:
                    result += b'\x0b'   # --> Ø
                elif c == 156:
                    result += b'\x5e'   # --> Ü
                elif c == 159:
                    result += b'\x1e'   # --> ß
                elif c == 160:
                    result += b'\x7f'   # --> à
                elif c == 164:
                    result += b'\x7b'   # --> ä
                elif c == 165:
                    result += b'\x0f'   # --> å
                elif c == 166:
                    result += b'\x1d'   # --> æ
                elif c == 167:
                    result += b'\x63'   # --> c pour ç
                elif c == 168:
                    result += b'\x04'   # --> è
                elif c == 169:
                    result += b'\x05'   # --> é
                elif c == 172:
                    result += b'\x07'   # --> ì
                elif c == 177:
                    result += b'\x7d'   # --> ñ
                elif c == 178:
                    result += b'\x08'   # --> ò
                elif c == 182:
                    result += b'\x7c'   # --> ö
                elif c == 184:
                    result += b'\x0c'   # --> ø
                elif c == 185:
                    result += b'\x06'   # --> ù
                else:
                    pass
            elif waitCode194 is True:
                waitCode194 = False
                if c == 161:
                    result += b'\x40'  # --> ¡
                elif c == 163:
                    result += b'\x01'  # --> £
                elif c == 164:
                    result += b'\x24'  # --> ¤
                elif c == 165:
                    result += b'\x03'  # --> §
                elif c == 167:
                    result += b'\x5f'  # --> §
                elif c == 191:
                    result += b'\x60'  # --> ¿
                else:
                    pass
            elif waitCode206 is True:
                waitCode206 = False
                if c == 147:
                    result += b'\x13'  # --> Γ
                elif c == 148:
                    result += b'\x10'  # --> Δ
                elif c == 152:
                    result += b'\x19'  # --> Θ
                elif c == 155:
                    result += b'\x14'  # --> Λ
                elif c == 158:
                    result += b'\x1a'  # --> Ξ
                elif c == 160:
                    result += b'\x16'  # --> Π
                elif c == 163:
                    result += b'\x18'  # --> Σ
                elif c == 166:
                    result += b'\x12'  # --> Φ
                elif c == 168:
                    result += b'\x17'  # --> Ψ
                elif c == 169:
                    result += b'\x15'  # --> Ω
                else:
                    pass
            else:
                if c == 195:
                    waitCode195 = True
                elif c == 194:
                    waitCode194 = True
                elif c == 206:
                    waitCode206 = True
                else:
                    if c == 64:
                        result += b'\x00'   # --> @
                    elif c == 36:
                        result += b'\x02'   # --> $
                    elif c == 95:
                        result += b'\x11'   # --> _
                    else:
                        result += bytes([c])
        logging.debug(result)
        sms = result + b'\x1A'
        return sms

    def isAuthorized(self, number):
        logging.debug(f"... isAuthorized: %s", number)
        if number in self.Auth:
            logging.debug("...... True")
            return True
        logging.debug("...... False")
        return False

    def readNewSms(self):
        # Read for MQTT in JSON
        result = None
        if self.Opened:
            # logging.debug("... readNewSMS")
            self.GsmApiSem.acquire()
            self.SmsList = []
            self.GsmIoCMGLReceived = False
            frame = bytes(gsm.ATCMGL+"\"ALL\"", 'ascii')
            self.writeCommandAndWaitOK(frame)
            for sms in self.SmsList:
                # retrieve sms id
                message_id = sms['Id']
                number = sms['Number']
                status = sms['Status']
                # read sms from id
                self.GsmIoCMGRReceived = False
                frame = bytes(gsm.ATCMGR+message_id, 'ascii')
                self.writeCommandAndWaitOK(frame)
                while not self.GsmIoCMGRReceived:
                    time.sleep(0.001)
                while self.RecordSmsText:
                    time.sleep(0.001)
                # retrieve sms text
                if self.isAuthorized(number):
                    sms = self.LastSmsText
                    self.SMSQueue.put({'Id': message_id, 'Number': number, 'Status': status, 'Msg': sms})
                # delete sms according to id
                frame = bytes(gsm.ATCMGD+message_id+",0", 'ascii')
                self.writeCommandAndWaitOK(frame)
            self.GsmApiSem.release()
            try:
                message = self.SMSQueue.get(False)
                try:
                    if message['Status'] == "STO SENT":
                        result = None
                    elif message['Status'] != "REC UNREAD" and message['Status'] != "REC READ":
                        result = None
                    else:
                        result = message
                except (Exception,):
                    result = None
            except (Exception,):
                result = None
        else:
            logging.error("... readNewSMS, device not opened")
            return result
        return result
