import typing
from abc import ABC

import numpy as np
import pytest


class ResourceUser:
    def __init__(self):
        self.resource = None

    def request_resource(self, resource_collection, resource_id) -> bool:
        self.resource = resource_collection.get_resource_of_id(resource_id)
        if self.resource:
            self.resource.lock(self)
            return True
        return False

    def get_resource_content(self) -> typing.Any:
        if not self.resource:
            raise PermissionError
        return self.resource.get_content(self)

    def update_resource(self, new_content) -> None:
        if self.resource:
            self.resource.change_content(self, new_content)

    def unlock_resource(self) -> None:
        if not self.resource:
            raise PermissionError
        self.resource.unlock(self)
        self.resource = None


class Resource(ABC):
    def __init__(self, id: typing.Any, content: typing.Any):
        self.id = id
        self._content = content
        self._user: ResourceUser | None = None

    def change_content(self, user: ResourceUser, new_content: typing.Any) -> None:
        if self._user != user:
            raise ValueError

        self._content = new_content

    def get_content_type(self) -> typing.Type:
        return type(self._content)

    def lock(self, user: ResourceUser):
        if self._user is not None:
            raise PermissionError
        self._user = user

    def unlock(self, user: ResourceUser) -> None:
        if self._user != user:
            raise ValueError
        self._user = None

    def get_content(self, user: ResourceUser) -> typing.Any:
        if self._user != user:
            raise ValueError

        return self._content

    def is_available(self):
        return self._user is None


class SpecialResource(Resource):
    def __init__(self, id: typing.Any, content: typing.Any):
        super().__init__(id, content)


class SpecialResource2(Resource):
    def __init__(self, id: typing.Any, content: typing.Any):
        super().__init__(id, content)


class SpecialResource3(SpecialResource):
    def __init__(self, id: typing.Any, content: typing.Any):
        super().__init__(id, content)


class ResourceCollection:
    def __init__(self, resource_type: typing.Type):
        self.resource_type = resource_type
        self.resources: list[typing.Type] = []

    def add_resource(self, resource: Resource) -> None:
        self.add_resources([resource])

    def add_resources(self, resources) -> None:
        for resource in resources:
            if resource.get_content_type() != self.resource_type:
                raise TypeError

            self.resources.append(resource)

    def get_resource_of_id(self, id: typing.Any) -> Resource | None:
        for resource in self.resources:
            if resource.id == id and resource.is_available():
                return resource

        return None


def test_main():
    ids = ["a", 12, [], None, False, {"b": -3}, "b", 0.1, True, type(Resource)]
    contents1 = [10, "c", type(str), [8.4, -5, {}], -4, False, type(int), "d", "e", [1, 2, 3]]
    contents2 = [4, "abcd", type(float), [-5, "4"], 3, True, type(list), "", "15", [None, [], "a"]]
    resources = []

    users = [ResourceUser(), ResourceUser(), ResourceUser()]
    for i in range(len(ids)):
        if i < 4:
            resources.append(SpecialResource(ids[i], contents1[i]))
        elif i < 7:
            resources.append(SpecialResource2(ids[i], contents1[i]))
        else:
            resources.append(SpecialResource3(ids[i], contents1[i]))

    collections = []
    for resource in resources:
        is_collection_found = False
        for collection in collections:
            if collection.resource_type == resource.get_content_type():
                collection.add_resource(resource)
                is_collection_found = True
        if not is_collection_found:
            collection = ResourceCollection(resource.get_content_type())
            collection.add_resource(resource)
            collections.append(collection)

    assert len(collections) == 5

    # Summary of loop: Updates all resources with the new content.
    for i in range(len(contents2)):
        id = ids[i]
        new_content = contents2[i]
        user_index = i % len(users)
        selected_user = users[user_index]

        for collection in collections:
            is_successful = selected_user.request_resource(collection, id)
            if is_successful:
                break

        for j in range(len(users)):
            user = users[j]
            if j == user_index:
                user.get_resource_content()
                user.update_resource(new_content)
                user.unlock_resource()
            else:
                with pytest.raises(PermissionError):
                    user.get_resource_content()
                    user.update_resource(new_content)
                    user.unlock_resource()

    for i, id in enumerate(ids):
        new_content = contents2[i]
        resource_with_id = None
        for collection in collections:
            resource_with_id = collection.get_resource_of_id(id)
            if resource_with_id:
                break

        assert new_content == resource_with_id._content


def test_main2():
    resources = [
        SpecialResource("a", 1),
        SpecialResource2("b", 15),
        SpecialResource3(15, -4),
        SpecialResource3(None, -8),
    ]

    collection = ResourceCollection(resources[0].get_content_type())
    collection.add_resources(resources)
    collection.add_resources(np.array(resources))
    collection.add_resources(set(resources))
