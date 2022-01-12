# -*- coding: utf-8 -*-
"""
    helpers.py
    @author: Darwinex Labs (www.darwinex.com), 2021-*
    
    Helper methods to parse FIX messages
    
"""

import logging
from datetime import datetime

"""
# Convert string to datetime
"""
def str_to_datetime(date_time_str):
    try:
        # 20200720-07:32:15.114
        return datetime.strptime(date_time_str, '%Y%m%d-%H:%M:%S.%f')
    except:
        return None


def datetime_to_str(date_time):
    try:
        # 20200720-07:32:15.114
        return date_time.strftime('%Y%m%d-%H:%M:%S.%f')
    except:
        return None


"""
# Convert a FIX message to a readable string.
"""
def read_FIX_message(message, delimiter=', '):
    m = message.toString().replace('\x01', delimiter)
    if len(m) >= 2:
        return m[:-2]
    return m


"""
# Extract Message Field Value (not used)
"""
def extract_message_field_value(_FIX_API_Object, message, type=''):

    if type == 'datetime':
        message.getHeader().getField(_FIX_API_Object)
        return str_to_datetime(_FIX_API_Object.getString())
    if message.isSetField(_FIX_API_Object.getField()):
        message.getField(_FIX_API_Object)
        if type == '':
            return _FIX_API_Object.getValue()
        elif type == 'str':
            return str(_FIX_API_Object.getValue())
        elif type == 'int':
            try:
                return int(_FIX_API_Object.getValue())
            except:
                return None
        elif type == 'float':
            try:
                return float(_FIX_API_Object.getValue())
            except:
                return None
    else:
        return None


"""
# Extract Header Field Value (not used)
"""
def extract_header_field_value(_FIX_API_Object, message):
    if message.getHeader().isSetField(_FIX_API_Object.getField()):
        message.getHeader().getField(_FIX_API_Object)
        return _FIX_API_Object.getValue()
    else:
        return None
    
##########################################################################

"""
# setup a logger
"""
def setup_logger(name, log_file, format_str, level=logging.INFO):

    formatter = logging.Formatter(format_str)

    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


"""
# log message
"""
def log(logger, message, _print=False):

    if logger is not None:
        logger.info(message)
    
    if _print:
        print(message)

##########################################################################
