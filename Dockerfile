ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install requirements for add-on
RUN apk add --no-cache python3 py3-pip python3-dev
RUN pip3 install --break-system-packages argparse pyserial requests paho-mqtt xmltodict

# Copy data for add-on
COPY CHANGELOG.md /
COPY gsm.py /
COPY gsm_io.py /
COPY LICENSE /
COPY README.md /
COPY run.sh /
COPY sms_manager.py /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
