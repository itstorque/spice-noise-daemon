#!/usr/bin/env python3

import argparse
import sys

import numpy as np

if __name__=="__main__":
    
    parser = argparse.ArgumentParser()
   
    parser.add_argument('-v', '--vsource', action='store_true', 
        help="creates a noise voltage source (default unless -i)")
    parser.add_argument('-i', '--isource', action='store_true', 
        help="creates a noise current source (overwrites -v)")
    
    parser.add_argument(
        '-g',
        '--gaussian',
        nargs=2,
        type=float,
        metavar=('mu', 'sigma'),
        help='noise distribution is a gaussian distribution and specify mu and sigma',
    )
    
    args = parser.parse_args()
    
    if args.isource and args.vsource:
        raise argparse.ArgumentError(None, "Choose one of vsource (-v) or isource (-i) for noise")
    
    if not args.isource:
         # vsource
         pass
    else:
        # isource
        pass
    
    noise = None
    
    if args.gaussian:
        
        mu, sigma = args.gaussian
        
        noise = np.random.normal(mu, sigma, 1000)
        
    

    