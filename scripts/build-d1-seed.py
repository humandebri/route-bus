#!/usr/bin/env python3
"""Compatibility entry point: only generate the organized publication seed."""
import runpy
runpy.run_path('scripts/build-publication-seed.py',run_name='__main__')
