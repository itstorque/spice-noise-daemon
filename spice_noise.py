#!/usr/bin/env python3

import argparse
from turtle import update
import yaml

import numpy as np

NOISE_FILE_DEST_PREAMBLE = "noise/noise_data_"

DEFAULT_NOISE_DEF_FILE = "noise/noise_sources.yaml"
LIB_FILE = "noise/pynoise.lib"

def write_yaml(noise_source_dict, dest=DEFAULT_NOISE_DEF_FILE):

    with open(dest, 'w') as file:
        yaml.dump(noise_source_dict, file)
        
def load_yaml(src=DEFAULT_NOISE_DEF_FILE):
    
    with open(src, 'r') as file:
        return yaml.load(file, Loader=yaml.FullLoader)
    
def lib_generator(name, source_symbol="V"):
    
    return f""".subckt {name} in out

** NOISE SOURCE **
{source_symbol} out in PWL file={NOISE_FILE_DEST_PREAMBLE}{name}.csv

.ends {name}

"""

def write_lib(content):
    
    with open(LIB_FILE, "w") as f:
        
        f.write(content)
        f.close()
    

def generate_asy_content(name, type="voltage"):
    
    return f"""Version 4
SymbolType CELL
LINE Normal 0 80 0 72
LINE Normal 0 0 0 8
CIRCLE Normal -32 8 32 72
TEXT 0 40 Center 0 {name}
SYMATTR Prefix X
SYMATTR Description {type.lower()} noise source
SYMATTR SpiceModel {name}
SYMATTR ModelFile {LIB_FILE}
PIN 0 0 NONE 8
PINATTR PinName in
PINATTR SpiceOrder 1
PIN 0 80 NONE 8
PINATTR PinName out
PINATTR SpiceOrder 2
"""

def create_asy(name, type="voltage"):
    
    content = generate_asy_content(name, type)
    
    with open(name+".asy", "w") as f:
        
        f.write(content)
        f.close()
    

def save_noise(source_name, noise, t):

    with open(NOISE_FILE_DEST_PREAMBLE + source_name + ".csv", "w") as f:
        
        for i in range(0,len(t)):
            f.write("{:E}\t{:E}\n".format( t[i], noise[i] ))
            
        f.close()
    
def update_noise(t):
    
    for source in source_data["sources"].keys():
            
            noise_data = source_data["sources"][source]["noise"]
            
            if noise_data["type"] == "gaussian":
                
                noise = np.random.normal(noise_data["mean"], noise_data["std"], len(t))
                
                save_noise(source, noise, t)
                
            elif noise_data["type"] == "poisson":
                
                noise = np.random.poisson(noise_data["lambda"], len(t))
                
                save_noise(source, noise, t)
    
if __name__=="__main__":
    
    # TODO: add path
    
    parser = argparse.ArgumentParser()
   
    parser.add_argument('-g', '--generate', action='store_true', 
        help="generate noise components to use in circuit design")
   
    parser.add_argument('-n', '--noise', action='store_true', 
        help="launch noise daemon that reloads noise")
    
    args = parser.parse_args()
    
    if args.generate:
        
        source_data = load_yaml()
        
        lib_content = "** NOISE_Library **\n\n"
        
        STEPS = source_data["entropy"]["STEPS"]
        T = source_data["entropy"]["T"]
        
        t = np.linspace(0, T, STEPS)
        
        for source in source_data["sources"].keys():
        
            lib_content += lib_generator(source, source_symbol="v" if source_data["sources"][source]["source_type"] else "i")
            
            create_asy(source, type=source_data["sources"][source]["source_type"])
        
        write_lib(lib_content)
        
        update_noise(t)

    if args.noise:
        
        import time, os.path
        
        seed_time = os.path.getmtime("test.log")
        
        source_data = load_yaml()
        
        STEPS = source_data["entropy"]["STEPS"]
        T = source_data["entropy"]["T"]
        
        t = np.linspace(0, T, STEPS)
        
        while True:
            
            time.sleep(1)
            
            if os.path.getmtime("test.log") > seed_time:
                
                seed_time = os.path.getmtime("test.log")
                
                update_noise(t)
    