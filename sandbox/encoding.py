'''
Created on 4 Dec 2014

@author: Ulrik Pedersen
'''

import struct

SINGLE_MSG_FMT='!HI'

msg_packer = struct.Struct(SINGLE_MSG_FMT)

def encode_message(addr, word):
    encoded_msg = msg_packer.pack(addr, word)
    return encoded_msg

def encode_multi_message(start_addr, words):
    addresses = range(start_addr, start_addr + len(words))
    encoded_msg = ""
    assert len(addresses) == len(words)
    for addr, word in zip(*[addresses, words]):
        encoded_msg += encode_message(addr, word)
        
    return encoded_msg

def decode_message(msg):
    extra_bytes = len(msg)%6
    if (extra_bytes > 0):
        msg = msg[:-extra_bytes] # WARNING: we are chopping away some bytes here...
    num_words =  len(msg)/6
    fmt = "!"
    fmt += "HI" * num_words
    
    msg_unpacker = struct.Struct(fmt)
    addr_word_list = msg_unpacker.unpack(msg)
    
    # reshape the linear list of (addr, word, addr, word, addr, word...) into a 
    # neat [(addr,word), (addr, word) ... ] list
    addr_word_sets = zip(*[iter(addr_word_list)]*2)
    
    return addr_word_sets

