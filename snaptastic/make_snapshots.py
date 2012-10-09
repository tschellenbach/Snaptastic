#!/usr/bin/env python
""" creates snapshots from volumes attached to this instance.
"""
from tagged_snapshots import get_mounted_volumes, get_volumes, create_snapshot, configure_logging

def main():
    
    configure_logging('make_snapshots.log')
    
    snap = Snapshotter()
    snapshots = snap.make_snapshots()

if __name__ == '__main__':
    main()
