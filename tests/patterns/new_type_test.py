"""
Pattern for distinguishing between different usages of the same type
by using typing.NewType.
"""
from typing import NewType
from tests.types import IFileSystem, InMemoryFileSystem, S3FileSystem
from injectpy import Kernel


# so: we want to have two file systems in our app: local one (on server)
# and some remote place like S3. To distinguish those two we use NewType()
# like this:
NetworkedFileSystem = NewType("NetworkedFileSystem", IFileSystem)


def test_new_type_usage():
    class MyHandler:
        def __init__(self, local: IFileSystem, networked: NetworkedFileSystem) -> None:
            self.local = local
            self.networked = networked

    kernel = Kernel()
    kernel.bind(IFileSystem, to=InMemoryFileSystem)
    kernel.bind(NetworkedFileSystem, to=S3FileSystem)
    inst = kernel.get(MyHandler)

    assert isinstance(inst.local, InMemoryFileSystem)
    assert isinstance(inst.networked, S3FileSystem)
