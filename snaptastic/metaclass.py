

class SnapshotterRegisteringMetaClass(type):
    '''
    Automatically register the classes
    '''
    def __new__(self, classname, bases, classDict):
        from snaptastic import register
        class_definition = type.__new__(self, classname, bases, classDict)
        register(class_definition)
        return class_definition