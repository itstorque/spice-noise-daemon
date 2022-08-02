#!/usr/bin/env python3

import argparse
import os
from sys import platform

import yaml

import numpy as np
import colorednoise as cn

NOISE_FILE_DEST_PREAMBLE = "noise/noise_data_"
DEFAULT_NOISE_DEF_FILE = "noise/noise_sources.yaml"
LIB_FILE = "noise/pynoise.lib"

def write_yaml(noise_source_dict, dest):

    with open(dest, 'w') as file:
        yaml.dump(noise_source_dict, file)
        
def load_yaml(src):
    
    with open(src, 'r') as file:
        return yaml.load(file, Loader=yaml.FullLoader)
    
def lib_generator(NOISE_FILE_DEST_PREAMBLE, name, source_symbol="V"):
    
    return f""".subckt {name} in out

** NOISE SOURCE **
{source_symbol} out in PWL file={NOISE_FILE_DEST_PREAMBLE}{name}.csv

.ends {name}

"""

def write_lib(LIB_FILE, content):
    
    with open(LIB_FILE, "w") as f:
        
        f.write(content)
        f.close()
    

def generate_asy_content(LIB_FILE, name, type="voltage"):
    
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

def create_asy(filepath, LIB_FILE, name, type="voltage"):
    
    content = generate_asy_content(LIB_FILE, name, type)
    
    with open(filepath + name+".asy", "w") as f:
        
        f.write(content)
        f.close()
    

def save_noise(NOISE_FILE_DEST_PREAMBLE, source_name, noise, t):

    with open(NOISE_FILE_DEST_PREAMBLE + source_name + ".csv", "w") as f:
        
        for i in range(0,len(t)):
            f.write("{:E}\t{:E}\n".format( t[i], noise[i] ))
            
        f.close()
    
def update_noise(NOISE_FILE_DEST_PREAMBLE, t):
    
    for source in source_data["sources"].keys():
            
            noise_data = source_data["sources"][source]["noise"]
            
            if noise_data["type"] == "gaussian":
                
                noise = np.random.normal(noise_data["mean"], noise_data["std"], len(t))
                
                save_noise(NOISE_FILE_DEST_PREAMBLE, source, noise, t)
                
            elif noise_data["type"] == "poisson":
                
                noise = noise_data["scale"] * np.random.poisson(noise_data["lambda"], len(t))
                
                save_noise(NOISE_FILE_DEST_PREAMBLE, source, noise, t)
                
            elif noise_data["type"] == "one_over_f":
                
                noise = noise_data["scale"] * cn.powerlaw_psd_gaussian(noise_data["power"], len(t), fmin=noise_data["fmin"])
                
                save_noise(NOISE_FILE_DEST_PREAMBLE, source, noise, t)

def file_path(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return os.path.dirname(os.path.abspath(arg)) + "/", \
               ''.join(os.path.basename(arg).split(".")[:-1]),\
               os.path.basename(arg).split(".")[-1]

if __name__=="__main__":
    
    # TODO: add path
    
    parser = argparse.ArgumentParser()
   
    parser.add_argument('-g', '--generate', action='store_true', 
        help="generate noise components to use in circuit design")
   
    parser.add_argument('-n', '--noise', action='store_true', 
        help="launch noise daemon that reloads noise")
    
    parser.add_argument('-s', '--setup', action='store_true', 
        help="setup directory for SPICE noise simulations")
    
    parser.add_argument("file", type=lambda x: file_path(parser, x), help="LTSpice circuit to launch this script for.")
    
    args = parser.parse_args()
    
    filepath, filename, file_extension = args.file
    
    NOISE_FILE_DEST_PREAMBLE = filepath + NOISE_FILE_DEST_PREAMBLE
    DEFAULT_NOISE_DEF_FILE   = filepath + DEFAULT_NOISE_DEF_FILE
    LIB_FILE                 = filepath + LIB_FILE
    
    if args.setup:
        print("Setting up directory " + filepath)
        
        os.makedirs(filepath + "/noise", exist_ok=True)
        
        new_file_loc = filepath + "/noise/noise_sources.yaml"
        
        overwrite = True
        
        if os.path.exists(new_file_loc):
            exists_string = "noise_sources.yaml already exists, type [overwrite] to overwrite otherwise hit enter.\n    > "
            if input(exists_string) == "overwrite":
                overwrite = True
            else:
                overwrite = False
        
        if overwrite:
            with open(new_file_loc, "w") as f:
                f.write("""entropy:
  T: 1
  STEPS: 1000
sources:
  noise_source_1:
    source_type: current
    noise:
      type: gaussian
      mean: 0
      std: 0.0000001
""")
                f.close()
    
    if args.generate == False and args.noise == False and args.setup == False:
        args.generate, args.noise = True, True
    
    if args.generate:
        
        source_data = load_yaml(DEFAULT_NOISE_DEF_FILE)
        
        lib_content = "** NOISE_Library **\n\n"
        
        STEPS = source_data["entropy"]["STEPS"]
        T = source_data["entropy"]["T"]
        
        t = np.linspace(0, T, STEPS)
        
        print("Generating new noise component sources...")
        
        for source in source_data["sources"].keys():
        
            lib_content += lib_generator(NOISE_FILE_DEST_PREAMBLE, source, source_symbol="v" if source_data["sources"][source]["source_type"]=="voltage" else "i")
            
            create_asy(filepath, LIB_FILE, source, type=source_data["sources"][source]["source_type"])
        
        write_lib(LIB_FILE, lib_content)
        
        update_noise(NOISE_FILE_DEST_PREAMBLE, t)

    if args.noise:
        
        import time, os.path
        
        try:
            seed_time = os.path.getmtime(filepath + filename + ".log")
            
        except FileNotFoundError as e:
            
            if platform == "darwin":
                os.system(f"/Applications/LTspice.app/Contents/MacOS/LTspice -b {filepath}{filename}.{file_extension} & open " + f"{filepath}{filename}.{file_extension}")
                
            else:
                
                print("Could not find log file.")
                print("Make sure that the supplied file exists and make sure it is launched.")
                
                raise FileNotFoundError
            
        seed_time = os.path.getmtime(filepath + filename + ".log")
        yaml_sources_time = os.path.getmtime(DEFAULT_NOISE_DEF_FILE)
        
        print("Launched noise daemon... Use LTSpice normally now :)")
        
        while True:
        
            source_data = load_yaml(DEFAULT_NOISE_DEF_FILE)
            
            STEPS = source_data["entropy"]["STEPS"]
            T = source_data["entropy"]["T"]
            
            t = np.linspace(0, T, STEPS)
            
            time.sleep(1)
            
            try:
            
                if os.path.getmtime(filepath + filename + ".log") > seed_time or os.path.getmtime(DEFAULT_NOISE_DEF_FILE) > yaml_sources_time:
                    
                    seed_time = os.path.getmtime(filepath + filename + ".log")
                    yaml_sources_time = os.path.getmtime(DEFAULT_NOISE_DEF_FILE)
                    
                    update_noise(NOISE_FILE_DEST_PREAMBLE, t)
                    
            except FileNotFoundError as e:
                
                if seed_time != None:
                    print("LTSpice closed, killing daemon")
                
                break
    