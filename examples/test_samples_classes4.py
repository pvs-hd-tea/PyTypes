import enum
import typing

import numpy as np
import pandas as pd
import pytest


class PERMISSION_LEVEL(enum.IntEnum):
    INVALID = 0
    ONE = 1
    TWO = 2
    THREE = 3


class DataTable:
    def __init__(self, id: str, minimum_permissions: PERMISSION_LEVEL, content: typing.Any = None):
        self.id = id
        self.minimum_permissions = minimum_permissions
        self.content = content


class DataBaseUser:
    def __init__(self, permission_level: PERMISSION_LEVEL):
        self.permission_level = permission_level


class Database:
    def __init__(self):
        self.data_tables = {}

    def create_data_table(self, user: DataBaseUser, id: str, content=None) -> None:
        if not id or not user:
            raise TypeError

        data_table = DataTable(id, user.permission_level, content)
        self.data_tables[id] = data_table

    def get_content_of(self, user: DataBaseUser, id: str) -> pd.DataFrame:
        if not id or not user:
            raise TypeError

        data_table = self.data_tables[id]
        if int(user.permission_level) < int(data_table.minimum_permissions):
            raise PermissionError

        return data_table.content

    def update_content_of(self, user: DataBaseUser, id: str, new_content=None) -> None:
        if not id or not user:
            raise TypeError

        data_table = self.data_tables[id]
        if int(user.permission_level) < int(data_table.minimum_permissions):
            raise PermissionError

        data_table.content = new_content


def test_main():
    database = Database()

    user1 = DataBaseUser(PERMISSION_LEVEL.ONE)
    user2 = DataBaseUser(PERMISSION_LEVEL.TWO)
    user3 = DataBaseUser(PERMISSION_LEVEL.THREE)

    content1 = None
    content2 = pd.DataFrame(np.array([[-1, False], [2, False], [5, True]]), columns=['a', 'b'])
    content3 = pd.DataFrame(np.array([[-1, type(int), "string"]]), columns=['c', 'd', 'e'])
    new_content1 = pd.DataFrame(np.array([[10, 3.15, 1, False], [27, -5.9, 0, False], [50, 1.4, 0, True]]),
                                columns=['f', 'g', 'h', 'i'])
    new_content2 = pd.DataFrame(np.array([[-1, False, None], [2, False, None], [5, True, type(str)]]),
                                columns=['a', 'b', 'c'])
    new_content3 = None
    database.create_data_table(user1, "a", content1)
    database.create_data_table(user2, "b", content2)
    database.create_data_table(user3, "c", content3)

    with pytest.raises(TypeError):
        database.get_content_of(None, "a")
        database.get_content_of(user1, None)
        database.update_content_of(None, "a", new_content1)
        database.update_content_of(user1, None, new_content1)

    with pytest.raises(PermissionError):
        database.get_content_of(user1, "b")
        database.get_content_of(user1, "c")
        database.get_content_of(user2, "c")

        database.update_content_of(user1, "b", new_content2)
        database.update_content_of(user1, "c", new_content3)
        database.update_content_of(user2, "c", new_content3)

    assert database.get_content_of(user1, "a") == content1
    assert database.get_content_of(user2, "b").equals(content2)
    assert database.get_content_of(user3, "c").equals(content3)

    database.update_content_of(user1, "a", new_content1)
    database.update_content_of(user2, "b", new_content2)
    database.update_content_of(user3, "c", new_content3)

    database.update_content_of(user3, "a", content1)
    database.get_content_of(user3, "a")
