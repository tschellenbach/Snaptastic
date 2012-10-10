#dict where all snapshotters get registered
snapshotters = {}


def get_snapshotter(snapshotter_name):
    error_format = 'No Snapshotter %s defined, registered Snapshotters are %s'
    if not snapshotter_name in snapshotters:
        raise ValueError(
            error_format % (snapshotter_name, snapshotters.keys()))
    return snapshotters[snapshotter_name]


class SnapshotterRegisteringMetaClass(type):
    '''
    Automatically register the classes
    '''
    def __new__(self, classname, bases, classDict):
        class_definition = type.__new__(self, classname, bases, classDict)
        if class_definition.name:
            snapshotters[class_definition.name] = class_definition
        return class_definition
