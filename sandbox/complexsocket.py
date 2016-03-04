'''
Created on 13 May 2015

@author: up45
'''
from __future__ import print_function

from percival.log import log
from percival.carrier.txrx import TxRx, TxRxContext
from percival.carrier.encoding import (encode_message, encode_multi_message, decode_message)

#board_ip_address = "percival2.diamond.ac.uk"
board_ip_address = "percival3.diamond.ac.uk"

def main():
    log.debug("complexsocket...")
    
    with TxRxContext(board_ip_address) as trx:
        
        #msg = encode_message(0x0144, 0x00000000)
        #msg = encode_message(0x0144, 0x00000000) # Header Info Readback
        #msg = encode_message(0x0102, 0x00000001) # Device Command: control, device_no-op, device index 1
        msg = encode_message(0x00EC, 0x00000005) # Device Command: control, device_set_and_get, device index 1

        log.debug("as string: %s",str([msg]))
        #trx.tx_msg(msg)
        #trx.tx_msg(msg)
        #resp = trx.rx_msg()
        resp = trx.send_recv(msg)
        log.debug("Device Command: %d bytes: %s", len(resp), [resp])
        resp = decode_message(resp)
        log.debug("Got %d words", len(resp))
        log.debug(resp)
        
        msg = encode_message(0x0144, 0x00000000) # ECHO WORD (times out)
        resp = trx.send_recv(msg)
        log.debug("ECHO WORD: %d bytes: %s", len(resp), [resp])
        resp = decode_message(resp)
        log.debug("Got %d words", len(resp))
        log.debug(resp)
    
if __name__ == '__main__':
    main()
    