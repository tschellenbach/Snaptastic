from argh import command, ArghParser
from snaptastic import get_snapshotter


@command
def make_snapshots(snapshotter_name, verbosity=2):
    snapshotter = get_snapshotter(snapshotter_name)
    snapshotter.make_snapshots()


@command
def mount_snapshots(snapshotter_name, verbosity=2):
    snapshotter = get_snapshotter(snapshotter_name)
    snapshotter.mount_snapshots()

    
p = ArghParser()
p.add_commands([make_snapshots, mount_snapshots])
p.dispatch()

