'''
Created on 13 May 2015

@author: Ulrik Pedersen
'''

from __future__ import print_function
from builtins import range

from percival.log import log
from percival.carrier.txrx import TxRx, TxRxContext
from percival.carrier.encoding import (encode_message, encode_multi_message, decode_message)

#board_ip_address = "percival2.diamond.ac.uk"
board_ip_address = "percival3.diamond.ac.uk"
scanrange = [(0x0144, 6),
             (0x0145, 96),
             (0x0146, None),
             ] # Currently no other "shortcut" addresses return a response

scanrange = range(0x012E, 0x0145, 1)

def main():
    log.info("Scanning shortcuts...")
    
    with TxRxContext(board_ip_address) as trx:
        trx.timeout = 1.0
        
        expected_bytes = None
        #for addr, expected_bytes in scanrange:
        for addr in scanrange:
            msg = encode_message(addr, 0x00000000)
    
            log.debug("Qurying address: %X ...", addr)
            try:
                resp = trx.send_recv(msg, expected_bytes)
            except:
                log.warning("no response (addr: %X", addr)
                continue
            data = decode_message(resp)
            log.info("Got from addr: 0x%04X bytes: %d  words: %d", addr, len(resp), len(data))
            for (a, w) in data:
                log.debug("           (0x%04X) 0x%08X", a, w)
                
if __name__ == '__main__':
    main()
    