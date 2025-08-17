#!/usr/bin/env python3
"""
Simple server runner for antispam beacon
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.p2p_beacon import main
