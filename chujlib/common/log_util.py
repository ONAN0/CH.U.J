"""Utility for a custom log management 
"""

import json
import logging.config
from pathlib import Path

def setup_logging(logger_name: str, 
                  config_path: str, 
                  log_path: str,
                  print: bool) -> logging.Logger:
   """Sets up a basic logger

   Parameters
   ----------
   logger_name : str
      name of the logger
   config_path : str
      path to the logger config file
   log_path : str
      path of the logs
   print : bool
      True print the log
      False don't print the log

   Returns
   -------
   logging.Logger
      setup logger
   """

   Path(log_path).parent.mkdir(exist_ok=True)

   logger = logging.getLogger(logger_name)

   config_file = Path(config_path)
   
   with open(config_file) as file_in:
      config = json.load(file_in)
   
   config["handlers"]["file"]["filename"] = f"{log_path}"
   
   if print:
      config["loggers"]["root"]["handlers"].append("stderr")
   
   logging.config.dictConfig(config)

   return logger
