# SPDX-FileCopyrightText: 2022 Renaissance Computing Institute. All rights reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-License-Identifier: LicenseRef-RENCI
# SPDX-License-Identifier: MIT

"""
    entrypoint for the configuration message queue handler

    Authors: Lisa Stillwell, Phil Owen @RENCI.org
"""
import os
import pika

from src.common.logger import LoggingUtil
from src.common.asgs_queue_callback import AsgsQueueCallback

###################################
# main entry point
###################################
def run():
    """
    fires up the message handler to process run properties data

    :return:
    """
    # get the log level and directory from the environment.
    log_level, log_path = LoggingUtil.prep_for_logging()

    # create a logger
    logger = LoggingUtil.init_logging("APSVIZ.APSViz-Msg-Handler.receive_cfg_msg_service", level=log_level, line_format='medium',
                                      log_file_path=log_path)

    try:
        logger.info("Initializing receive_cfg_msg_queue handler.")

        # set up AMQP credentials and connect to asgs queue
        credentials = pika.PlainCredentials(os.environ.get("RABBITMQ_USER"), os.environ.get("RABBITMQ_PW"))

        parameters = pika.ConnectionParameters(os.environ.get("RABBITMQ_HOST"), 5672, '/', credentials, socket_timeout=2)

        connection = pika.BlockingConnection(parameters)

        channel = connection.channel()

        channel.queue_declare(queue='asgs_props')

        logger.info("receive_cfg_msg_queue channel and queue declared.")

        # get an instance to the callback handler
        queue_callback_inst = AsgsQueueCallback(_logger=logger)

        channel.basic_consume('asgs_props', queue_callback_inst.cfg_callback, auto_ack=True)

        logger.info('receive_cfg_msg_queue configured and waiting for messages...')

        channel.start_consuming()
    except Exception:
        logger.exception("FAILURE - Problems initiating receive_cfg_msg_queue")


if __name__ == "__main__":
    run()
