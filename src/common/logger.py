import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """
    Returns a centrally configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Prevent adding handlers multiple times if instantiated multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # CRITICAL: MCP stdio protocol uses stdout for JSON-RPC — logs MUST go to stderr
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(logging.INFO)
        
        # Create formatter and add it to the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        
        # Add the handler to the logger
        logger.addHandler(ch)
        
        # Prevent propagation to the root logger to avoid double printing
        logger.propagate = False
        
    return logger
