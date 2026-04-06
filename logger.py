import logging
import sys
from colorlog import ColoredFormatter

def setup_logger(name="agents-orchestration"):
    """
    Setup a colored logger with structural information.
    """
    logger = logging.getLogger(name)
    
    # If logger already has handlers, don't add more
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Standard format: [TIME] [LEVEL] [LOGGER_NAME] - MESSAGE
    # Colored format:
    formatter = ColoredFormatter(
        "%(log_color)s[%(levelname)s]%(reset)s %(blue)s[%(name)s]%(reset)s %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to the root logger to avoid duplicate logs
    logger.propagate = False
    
    return logger

# Global instance
logger = setup_logger()

def log_node_start(node_name):
    logger.info(f"🚀 Entering Node: {node_name}")

def log_node_end(node_name, result_summary=None):
    if result_summary:
        logger.info(f"✅ Finished Node: {node_name} | Result: {result_summary}")
    else:
        logger.info(f"✅ Finished Node: {node_name}")

def log_error(node_name, error_msg):
    logger.error(f"❌ Error in Node {node_name}: {error_msg}")

def log_supervisor_decision(next_agent, instruction):
    logger.warning(f"🎯 Supervisor Decision: Next={next_agent}")
    logger.info(f"📝 Instruction: {instruction}")
