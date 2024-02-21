"""
   Copyright (c) Philippe Romano, 2021, 2022, 2023
"""

from    threading   import Thread, Lock
import  serial
import  serial.tools.list_ports
import  time
import logging

class gsm_io:

    def __init__(self, device):
        self.GsmSerial              = serial.Serial()
        self.GsmDevice              = device
        self.GsmIoProtocolSem       = Lock()
        self.GsmIoReadyToSend       = True
        self.CommandSem             = Lock()
        self.WaitingOk              = False
        self.RecordSmsText          = False
        self.GsmIoCMSSId            = -1
        self.GsmIoCMSSReceived      = False
        self.GsmIoOKReceived        = False
        self.GsmIoPromptReceived    = False
        self.SmsText: bytes         = b''
        self.LastSmsText: bytes     = b''
        self.GsmIoMessageId: bytes  = b''
        self.GsmIoActivityThread    = None
        self.SmsList                = None
        self.GsmIoCMGLReceived      = False
        self.GsmIoSmsIdReceived     = False
        self.GsmIoCMGRReceived      = False
        self.Opened                 = False
        self.Debug                  = False
        # logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
        logging.basicConfig(level=logging.INFO)

    def __del__(self):
        if self.Opened:
            self.GsmSerial.close()
        del self.GsmSerial
        del self.GsmIoProtocolSem
        del self.CommandSem

    @staticmethod
    def debugFrame():
        logging.info('')
        logging.info(f'Evaluating byte frame values')
        frame: bytes = b'\xFF\x00\x21'
        logging.info(frame)
        logging.info(list(frame))  # --> b'\xff\x00!'  and   [255, 0, 33]

    def openGsmIoDevice(self):
        try:
            logging.info('... trying to open device on '+self.GsmDevice)
            self.GsmSerial.baudrate = 115200
            self.GsmSerial.port = self.GsmDevice
            self.GsmSerial.parity = serial.PARITY_NONE
            self.GsmSerial.bytesize = serial.EIGHTBITS
            self.GsmSerial.stopbits = serial.STOPBITS_ONE
            self.GsmSerial.xonxoff = False
            self.GsmSerial.rtscts = False
            self.GsmSerial.dsrdtr = False
            self.GsmSerial.open()
            self.GsmSerial.flush()
            if self.GsmSerial.is_open:
                self.Opened = True
                logging.info('...... device is opened on '+self.GsmDevice)
            else:
                self.Opened = False
                logging.info('...... device is still closed, could not open '+self.GsmDevice)
        except (Exception,) as e:
            logging.info('...... device exception while opening '+self.GsmDevice)
            # logging.info(e)
        return  self.Opened

    def closeGsmIoDevice(self):
        self.GsmSerial.close()
        if self.GsmSerial.is_open:
            logging.info('... Gsm is still opened ')
        else:
            self.Opened = False
            logging.info('... Gsm is closed ')

    def writeCommandAndWaitOK(self, frame: bytes):
        # frame is bytes
        self.GsmIoOKReceived = False
        data = frame + b'\r'
        self.writeData(data)
        while not self.GsmIoOKReceived:
            time.sleep(0.001)
        self.GsmIoOKReceived = False

    def writeData(self, frame: bytes):
        self.GsmSerial.write(frame)

    # Start activity thread
    def startGsmIoActivity(self):
        if self.Opened:
            self.GsmIoActivityThread            = Thread(target=self.runGsmIoActivityThread)
            self.GsmIoActivityThread.daemon     = True
            self.GsmIoActivityThread.isRunning  = True
            self.GsmIoActivityThread.start()

    # Stop activity thread
    def stopGsmIoActivity(self):
        if self.Opened:
            self.GsmIoActivityThread.isRunning = False
            self.GsmIoActivityThread.join()

    def runGsmIoActivityThread(self):
        frame: bytes = b''
        while getattr(self.GsmIoActivityThread, "isRunning", True):
            time.sleep(0.001)
            if self.GsmSerial.in_waiting >= 1:
                # some data available
                data: bytes = self.GsmSerial.read(1)
                frame += data
                if self.Ready and self.Debug:
                    logging.info(frame)
                    logging.info(list(frame))
                if '> ' in frame.decode("ascii"):
                    # self.GsmIoActivityLog.debug(self.GsmIoActivityLogLevel+1, 'Frame with prompt: ', hex_data=frame)
                    # self.GsmIoActivityLog.info(self.GsmIoActivityLogLevel+1, 'Prompt (>)')
                    #if self.Ready and self.Debug:
                    #    logging.info('Prompt (>)')
                    self.GsmIoOKReceived = True
                    self.GsmIoPromptReceived = True
                    frame = b''
                if '\r\n' in frame.decode("ascii"):
                    # received response
                    if 'OK\r\n' in frame.decode("ascii"):
                        #self.GsmIoActivityLog.debug(self.GsmIoActivityLogLevel+1, 'OK<cr><lf> Frame: ', hex_data=frame)
                        #if self.Ready and self.Debug:
                        #    logging.info('OK\r\n')
                        self.GsmIoOKReceived = True
                        if self.RecordSmsText:
                            self.SmsText = self.SmsText[:-4]    # remove 2 last crlf
                            self.LastSmsText = self.SmsText
                            self.SmsText = b''
                            self.RecordSmsText = False
                        # self.clearWaitingOk(self.GsmIoActivityLog, self.GsmIoActivityLogLevel+2)
                        # self.GsmIoActivityLog.info(self.GsmIoActivityLogLevel+1, 'OK Received, WaitingOk cleared')
                    elif '+CMGL:' in frame.decode("ascii"):
                        #self.GsmIoActivityLog.debug(self.GsmIoActivityLogLevel+1, '+CMGL Frame: ', hex_data=frame)
                        #if self.Ready and self.Debug:
                        #    logging.info('+CMGL:')
                        sms_line = frame[0:len(frame)-1].decode("ascii")
                        #self.GsmIoActivityLog.info(self.GsmIoActivityLogLevel+1, sms_line)
                        message_id = sms_line.split(',')[0].split(': ')[1]
                        number = sms_line.split(',')[2][1:-1]  # remove both "
                        status = sms_line.split(',')[1][1:-1]  # remove both "
                        self.SmsList.append({'Id': message_id, 'Number': number, 'Status': status})
                        self.GsmIoCMGLReceived = True
                        # do not clear Waiting Response at this time
                        # frame = b''
                    elif 'ATZ\r\r\n' in frame.decode("ascii"):
                        #self.GsmIoActivityLog.debug(self.GsmIoActivityLogLevel+1, 'ATZ<cr><cr><lf> Frame: ', hex_data=frame)
                        pass
                    elif 'ATE0\r\r\n' in frame.decode("ascii"):
                        #self.GsmIoActivityLog.debug(self.GsmIoActivityLogLevel+1, 'ATE0<cr><cr><lf> Frame: ', hex_data=frame)
                        pass
                    elif '+CME ERROR:' in frame.decode("ascii"):
                        #self.GsmIoActivityLog.debug(self.GsmIoActivityLogLevel+1, '+CME ERROR Frame: ', hex_data=frame)
                        self.GsmIoOKReceived = True
                    elif '+CMGW:' in frame.decode("ascii"):
                        #self.GsmIoActivityLog.debug(self.GsmIoActivityLogLevel+1, '+CMGW Frame: ', hex_data=frame)
                        self.GsmIoMessageId = frame[7:len(frame)-2]
                        self.GsmIoSmsIdReceived = True
                        # self.GsmIoActivityLog.info(self.GsmIoActivityLogLevel+2, 'Message id: '+self.GsmIoMessageId.decode("latin-1"))
                        # do not clear Waiting Response at this time
                    elif '+CMSS:' in frame.decode("ascii"):
                        #self.GsmIoActivityLog.debug(self.GsmIoActivityLogLevel+1, '+CMSS Frame: ', hex_data=frame)
                        self.GsmIoCMSSId = frame[7:len(frame)-2]
                        self.GsmIoCMSSReceived = True
                        # self.GsmIoActivityLog.info(self.GsmIoActivityLogLevel+2, 'Message id: '+self.GsmIoCMSSId.decode("latin-1"))
                        # do not clear Waiting Response at this time
                    elif '+CPMS:' in frame.decode("ascii"):
                        #self.GsmIoActivityLog.debug(self.GsmIoActivityLogLevel+1, '+CPMS Frame: ', hex_data=frame)
                        # do not clear Waiting Response at this time
                        pass
                    elif '+CLIP:' in frame.decode("ascii"):
                        #self.GsmIoActivityLog.debug(self.GsmIoActivityLogLevel+1, '+CLIP Frame: ', hex_data=frame)
                        # do not clear Waiting Response at this time
                        pass
                    elif '+CMGR:' in frame.decode("ascii"):
                        # Now sms text will follow
                        # self.GsmIoActivityLog.debug( self.GsmIoActivityLogLevel + 1, '+CMGR Frame: ', hex_data=frame )
                        if self.Ready and self.Debug:
                            logging.info('+CMGR:')
                        self.RecordSmsText = True
                        self.GsmIoCMGRReceived = True
                    elif '\r\n' in frame.decode("ascii"):
                        if self.RecordSmsText:
                            #self.SmsText = self.SmsText+str(frame, encoding="ascii")
                            self.SmsText = self.SmsText+frame
                            #self.GsmIoActivityLog.info(self.GsmIoActivityLogLevel+1, 'adding line to sms text: '+frame[0:len(frame)].decode("latin-1"))
                        # if len(frame) > 2:
                        #    self.GsmIoActivityLog.info(self.GsmIoActivityLogLevel+1, frame[0:len(frame)-2].decode("latin-1")+' received')
                        else:
                            #self.GsmIoActivityLog.info(self.GsmIoActivityLogLevel+1, '<cr><lf> received')
                            pass
                    else:
                        #self.GsmIoActivityLog.debug(self.GsmIoActivityLogLevel+1, 'Frame (?): ', hex_data=frame)
                        #self.GsmIoActivityLog.info(self.GsmIoActivityLogLevel+1, ''+frame.decode("latin-1"))
                        pass
                    frame = b''
