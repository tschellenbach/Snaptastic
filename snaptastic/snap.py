import sys
import os

path = os.path.abspath(__file__)
parent = os.path.join(path, '../', '../')
sys.path.append(parent)

from argh import command, ArghParser
from snaptastic import get_snapshotter


@command
def make_snapshots(snapshotter_name, verbosity=2):
    snapshotter_class = get_snapshotter(snapshotter_name)
    snap = snapshotter_class()
    snap.make_snapshots()


@command
def mount_snapshots(snapshotter_name, verbosity=2):
    snapshotter_class = get_snapshotter(snapshotter_name)
    snap = snapshotter_class()
    snap.mount_snapshots()

    
p = ArghParser()
p.add_commands([make_snapshots, mount_snapshots])
p.dispatch()

