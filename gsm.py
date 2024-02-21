"""
    Copyright (c) Philippe Romano, 2021, 2022, 2023
"""

import time
import json
import logging

from gsm_io         import gsm_io
from authentication import authentication
from threading      import Thread, Lock
from queue          import Queue

#                 0-----------------------------------2f
sms_alpha     = ("@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ"
                 " !\"#¤%&'()*+,-./0123456789:;<=>?"
                 "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§"
                 "¿abcdefghijklmnopqrstuvwxyzäöñüà")
sms_ext_alpha = ("````````````````````^```````````````````{}`````\\````````````[~]`"
                 "|````````````````````````````````````€``````````````````````````")

class gsm(gsm_io, authentication):

    ATZ = "ATZ"  # reset modem
    ATE0 = "ATE0"  # set echo off
    ATE1 = "ATE1"  # set echo on
    ATCLIP = "AT+CLIP?"  # get calling line identification presentation
    ATCMEE = "AT+CMEE=1"  # set extended error
    #ATCPIN = "AT+CPIN=\"5061\""  # set pin code
    #ATCLCK0 = "AT+CLCK=\"SC\",0,\"5061\""  # disable code pin check, pin=5061
    #ATCLCK1 = "AT+CLCK=\"SC\",1,\"5061\""  # enable code pin check, pin=5061
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

    def __init__(self, name: str, mode: str, device: str, pin: str, mqtt_client):
        self.GsmReaderThread = None
        self.GsmMode = mode
        self.MQTTClient = mqtt_client
        self.ATCPIN = "AT+CPIN=\""+pin+"\""  # set pin code
        self.ATCLCK0 = "AT+CLCK=\"SC\",0,\""+pin+"\""  # disable code pin check, pin=5061
        self.ATCLCK1 = "AT+CLCK=\"SC\",1,\""+pin+"\""  # enable code pin check, pin=5061
        self.GsmIoOKReceived = None
        self.GsmIoCMSSReceived = None
        self.GsmPIN = pin
        self.Ready = False
        self.Name = name
        self.GsmLogLevel = 0
        self.GsmApiSem = Lock()
        self.GsmMutex = Lock()
        self.SMSQueue = Queue()
        self.GsmIoPrompt = False
        self.GsmIoSmsIdReceived = False
        self.Opened = False
        self.NameServerURI = ''
        self.SmsList = []
        self.GsmIoCMGLReceived = False
        self.GsmIoCMGRReceived = False
        # set logger
        # logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
        logging.basicConfig(level=logging.INFO)
        gsm_io.__init__(self, device)  # since inherited, needs to be called explicitly
        authentication.__init__(self)  # since inherited, needs to be called explicitly

    def __del__(self):
        authentication.__del__(self)  # since inherited, needs to be called explicitly
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
            self.GsmApiSem.acquire()
            frame = bytes(gsm.ATZ, 'ascii')
            self.writeCommandAndWaitOK(frame)
            frame = bytes(gsm.ATE0, 'ascii')
            self.writeCommandAndWaitOK(frame)
            frame = bytes(self.ATCPIN, 'ascii')
            self.writeCommandAndWaitOK(frame)
            frame = bytes(self.ATCLCK0, 'ascii')
            self.writeCommandAndWaitOK(frame)
            frame = bytes(gsm.ATCMGF, 'ascii')
            self.writeCommandAndWaitOK(frame)
            frame = bytes(gsm.ATCNMI, 'ascii')
            self.writeCommandAndWaitOK(frame)
            frame = bytes(gsm.ATCSCS, 'ascii')
            self.writeCommandAndWaitOK(frame)
            frame = bytes(gsm.ATCPMS, 'ascii')
            self.writeCommandAndWaitOK(frame)
            frame = bytes(gsm.ATCLIP, 'ascii')
            self.writeCommandAndWaitOK(frame)
            frame = bytes(gsm.ATCSDH, 'ascii')
            self.writeCommandAndWaitOK(frame)
            frame = bytes(gsm.ATCMGD+"0,4", 'ascii')
            self.writeCommandAndWaitOK(frame)
            self.GsmApiSem.release()

    def sendSmsToNumber(self, number, message):
        if self.Opened:
            # message is string utf-8
            # has to be converted to bytes to be send on modem
            logging.info(f"... Send SMS")
            #logging.info(f"... %s", message)
            self.GsmApiSem.acquire()
            self.GsmMutex.acquire()
            self.GsmIoSmsIdReceived = False
            self.GsmIoCMSSReceived = False
            self.GsmIoPrompt = False
            self.GsmMutex.release()
            data = gsm.ATCMGW+"\""+number+"\""
            frame = bytes(data, 'utf-8')
            self.writeCommandAndWaitOK(frame)           # writes bytes on modem
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
            # Id received is bytes
            data = gsm.ATCMSS+self.GsmIoMessageId.decode('ascii')
            frame = bytes(data, 'utf-8')               # writes bytes on modem
            self.writeCommandAndWaitOK(frame)
            # cmss will arrive before 'ok'
            # logging.info(f'... Id received: '+self.GsmIoCMSSId.decode('ascii'))
            self.GsmApiSem.release()
            logging.info(f"...... SMS sent")
            logging.info("")

    # Start activity thread
    def startGsmReader(self):
        if self.Opened:
            self.GsmReaderThread            = Thread(target=self.runGsmReaderThread)
            self.GsmReaderThread.daemon     = True
            self.GsmReaderThread.isRunning  = True
            self.GsmReaderThread.start()

    # Stop activity thread
    def stopGsmReader(self):
        if self.Opened:
            self.GsmReaderThread.isRunning = False
            self.GsmReaderThread.join()

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
                # print("    ", json.dumps(json_message))
                self.MQTTClient.publish("sms_received", json.dumps(json_message))
            time.sleep(1)

    def encodeUTF8toJSON(self, bytes_message):
        # Be sure to escape " characters with \"
        logging.info('... Encode UTF-8 to JSON')
        logging.info(list(bytes_message))
        result = []
        for b in bytes_message:
            if b == '"':
                result.append('\\')
            result.append(b)
        return ''.join(result)

    def decodeGSM7toUTF8(self, bytes_message):
        logging.info('... Decoding GSM-7 to UTF-8')
        logging.info(list(bytes_message))
        # logging.info(b'..... '+bytes_message)
        result = []
        for b in bytes_message:         # b is code value of character
            '''
            if b == 10:
                result.append('\\')
                result.append('n')
            elif b == 34:
                result.append('\\')
                result.append('"')
            else:
                result.append(sms_alpha[b])
            '''
            result.append(sms_alpha[b])
        return ''.join(result)

    def encodeUTF8toGSM7(self, message):
        # UTF-8 double byte character will be replace by specific
        # GSM alphabet code
        message_list = list(bytes(message, 'utf-8'))
        #logging.info(message_list)
        logging.info('...... Encoding UTF-8 to GSM-7')
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
        logging.info(result)
        sms = result + b'\x1A'
        #sms = result
        return sms

    def readNewSms(self):
        # Read for MQTT in JSON
        result = None
        if self.Opened:
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
                        # logging.info(f"... Sms received: %s", message['Msg'])
                        result = message
                except (Exception,):
                    result = None
            except (Exception,):
                result = None
        return result
