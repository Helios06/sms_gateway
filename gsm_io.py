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

from    threading   import Thread, Lock
import  serial
import  serial.tools.list_ports
import  time
import  logging

class gsm_io:

    def __init__(self, loglevel, device):
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
        logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=loglevel)

    def __del__(self):
        if self.Opened:
            self.GsmSerial.close()
        del self.GsmSerial
        del self.GsmIoProtocolSem
        del self.CommandSem

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
                logging.error('...... device is still closed, could not open '+self.GsmDevice)
        except (Exception,):
            logging.error('...... device exception while opening '+self.GsmDevice)
        return  self.Opened

    def closeGsmIoDevice(self):
        logging.info('... trying to close GSM device')
        self.GsmSerial.close()
        if self.GsmSerial.is_open:
            logging.error('... Gsm is still opened ')
        else:
            self.Opened = False
            logging.info('... Gsm is closed ')

    def writeCommandAndWaitOK(self, frame: bytes):
        # frame is bytes
        self.GsmIoOKReceived = False
        data = frame + b'\r'
        self.writeData(data)
        while not self.GsmIoOKReceived:
            time.sleep(0.01)
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
                if '> ' in frame.decode("ascii"):
                    self.GsmIoOKReceived = True
                    self.GsmIoPromptReceived = True
                    frame = b''
                if '\r\n' in frame.decode("ascii"):
                    # received response
                    if 'OK\r\n' in frame.decode("ascii"):
                        self.GsmIoOKReceived = True
                        if self.RecordSmsText:
                            self.SmsText = self.SmsText[:-4]    # remove 2 last crlf
                            self.LastSmsText = self.SmsText
                            self.SmsText = b''
                            self.RecordSmsText = False
                    elif '+CMGL:' in frame.decode("ascii"):
                        sms_line = frame[0:len(frame)-1].decode("ascii")
                        message_id = sms_line.split(',')[0].split(': ')[1]
                        number = sms_line.split(',')[2][1:-1]  # remove both "
                        status = sms_line.split(',')[1][1:-1]  # remove both "
                        self.SmsList.append({'Id': message_id, 'Number': number, 'Status': status})
                        self.GsmIoCMGLReceived = True
                        # do not clear Waiting Response at this time
                        # frame = b''
                    elif 'ATZ\r\r\n' in frame.decode("ascii"):
                        pass
                    elif 'ATE0\r\r\n' in frame.decode("ascii"):
                        pass
                    elif '+CME ERROR:' in frame.decode("ascii"):
                        # logging.debug(f"............ %s", frame.decode("ascii"))
                        # logging.debug(f"............ not critical")
                        self.GsmIoOKReceived = True
                    elif '+CMGW:' in frame.decode("ascii"):
                        self.GsmIoMessageId = frame[7:len(frame)-2]
                        self.GsmIoSmsIdReceived = True
                        # do not clear Waiting Response at this time
                    elif '+CMSS:' in frame.decode("ascii"):
                        self.GsmIoCMSSId = frame[7:len(frame)-2]
                        self.GsmIoCMSSReceived = True
                        # do not clear Waiting Response at this time
                    elif '+CPMS:' in frame.decode("ascii"):
                        # do not clear Waiting Response at this time
                        pass
                    elif '+CLIP:' in frame.decode("ascii"):
                        # do not clear Waiting Response at this time
                        pass
                    elif '+CMGR:' in frame.decode("ascii"):
                        # Now sms text will follow
                        self.RecordSmsText = True
                        self.GsmIoCMGRReceived = True
                    elif '\r\n' in frame.decode("ascii"):
                        if self.RecordSmsText:
                            self.SmsText = self.SmsText+frame
                        else:
                            pass
                    else:
                        pass
                    frame = b''
