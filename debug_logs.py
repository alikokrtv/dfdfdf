from flask import Flask, request, session
import logging
import sys

# Debug logları için
logger = logging.getLogger('dof_app')
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

def log_debug(message):
    """Debug log yazma yardımcı fonksiyonu"""
    logger.debug(message)
