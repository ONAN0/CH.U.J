import json

def imp_json(filepath:str) -> dict | list[dict]:
   """Imports JSON file content

   Parameters
   ----------
   filepath : str
      Filepath to read from

   Returns
   -------
   dict | list[dict]
      Data from file
   """
   with open(filepath, "r") as file:
      return json.load(file)

def exp_json(filepath:str, data: dict | list[dict]) -> None:
   """Exports content to JSON file

   Parameters
   ----------
   filepath : str
      Filepath to write to 
   data : dict | list[dict]
      Data to write
   """
   with open(filepath, "w") as file:
      json.dump(data, file)
