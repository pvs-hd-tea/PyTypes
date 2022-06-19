import typing
from abc import ABC, abstractmethod


class ContentRequest:
    def __init__(self, requested_type: typing.Type):
        self.requested_type = requested_type


class ContentPackage:
    def __init__(self, content: typing.Any):
        self.content = content


class Task:
    def __init__(self, requests):
        self.requests = requests
        self.packages = []

    def next_request(self) -> ContentRequest | None:
        if not self.is_done():
            return self.requests[len(self.packages)]
        return None

    def add_package(self, content_package: ContentPackage) -> None:
        self.packages.append(content_package)

    def is_done(self):
        return len(self.packages) == len(self.requests)


class ContentUser(ABC):
    @abstractmethod
    def get_next_request(self) -> ContentRequest | None:
        pass

    @abstractmethod
    def on_get_content_package(self, content_package: ContentPackage) -> None:
        pass


class TaskUser(ContentUser):
    def __init__(self, task: Task):
        self.task = task

    def get_next_request(self) -> ContentRequest | None:
        return self.task.next_request()

    def on_get_content_package(self, content_package: ContentPackage) -> None:
        self.task.add_package(content_package)

    def is_task_done(self):
        return self.task.is_done()


class StorageCluster:
    def __init__(self, storages: list[ContentPackage]):
        self._storages = storages

    def give_content_package_and_remove(self, content_user: ContentUser,
                                        content_request: ContentRequest) -> None:
        for storage in self._storages:
            if storage.give_content_package_and_remove(content_user, content_request):
                return

        raise RuntimeError

    def is_empty(self):
        for storage in self._storages:
            if not storage.is_empty():
                return False
        return True


class Storage:
    def __init__(self, contents: list[typing.Any]):
        self._contents: list[typing.Any] = contents

    def give_content_package_and_remove(self, content_user: ContentUser, content_request: ContentRequest) -> bool:
        for content in self._contents:
            if type(content) == content_request.requested_type:
                self._contents.remove(content)

                package = ContentPackage(content)
                content_user.on_get_content_package(package)
                return True
        return False

    def is_empty(self):
        return len(self._contents) == 0


def test_main():
    requests = [
        ContentRequest(str),
        ContentRequest(str),
        ContentRequest(int),
        ContentRequest(int),
        ContentRequest(int),
        ContentRequest(float),
        ContentRequest(float),
        ContentRequest(str)
    ]

    task1 = Task(requests[:4])
    task2 = Task(requests[4:])

    user1 = TaskUser(task1)
    user2 = TaskUser(task2)

    responses = ["a", "b", "c", -5, 2, 10, 0.4, 12.5]

    storage1 = Storage(responses[:2])
    storage2 = Storage(responses[2:5])
    storage3 = Storage(responses[5:])

    cluster = StorageCluster([storage1, storage2, storage3])
    while not user1.task.is_done() or not user2.task.is_done():
        next_request = user1.get_next_request()
        if next_request:
            cluster.give_content_package_and_remove(user1, next_request)

        next_request = user2.get_next_request()
        if next_request:
            cluster.give_content_package_and_remove(user2, next_request)

    assert user1.is_task_done() and user2.is_task_done() and cluster.is_empty()
