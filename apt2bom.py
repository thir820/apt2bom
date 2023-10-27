#!/usr/bin/python3

if __name__ == '__main__':
    from apt2bom.log import config_logger
    import logging
    config_logger(level=logging.INFO)

    from apt2bom.apt2bom import run
    run()
