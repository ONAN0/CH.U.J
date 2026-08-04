"""Utility for a custom log management 
"""

import json
import logging.config
from pathlib import Path

def setup_logging(logger_name: str, 
                  config_path: str, 
                  log_path: str,
                  console_level: int) -> logging.Logger:
   """Sets up a basic logger

   Parameters
   ----------
   logger_name : str
      name of the logger
   config_path : str
      path to the logger JSON config file
   log_path : str
      destination log file path
   console_level : int
      
      * 0: no console logging
      * 1: INFO and above
      * 2: WARNING and above

   Returns
   -------
   logging.Logger
      configured logger
   """

   Path(log_path).parent.mkdir(exist_ok=True)

   config_file = Path(config_path)
   
   with open(config_file) as file_in:
      config = json.load(file_in)
   
   config["handlers"]["file"]["filename"] = f"{log_path}"

   handlers = config["loggers"]["root"]["handlers"]

   if 1 == console_level and "stdout" not in handlers:
      handlers.append("stdout")
   elif 2 == console_level and "stderr" not in handlers:
      handlers.append("stderr")

   logging.config.dictConfig(config)

   return logging.getLogger(logger_name)
