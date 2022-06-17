from abc import ABC


class Data(ABC):
    def __init__(self, integer, string):
        self.integer = integer
        self.string = string

    def get_sum(self):
        return self.integer + int(self.string)


class SubClassData(Data):
    def __init__(self, integer, string, second_integer):
        super().__init__(integer, string)
        self.second_integer = second_integer

    def get_sum(self):
        return super().get_sum() + self.second_integer


class SubClassData2(Data):
    def __init__(self, integer, string, second_string):
        super().__init__(integer, string)
        self.second_string = second_string

    def get_sum(self):
        return super().get_sum() + int(self.second_string)


class DataUser(ABC):
    def __init__(self, data: Data):
        self.data = data

    def get_third_value(self, data: Data):
        if isinstance(data, SubClassData):
            return data.second_integer
        elif isinstance(data, SubClassData2):
            return data.second_string
        else:
            raise TypeError

    def update_data(self, data):
        self.data.string = data.string
        self.data.integer += data.integer


class SubClassDataUser(DataUser):
    def __init__(self, data: SubClassData):
        super().__init__(data)

    def update_data(self, data):
        super().update_data(data)
        third_value = self.get_third_value(data)
        self.data.second_integer = int(third_value)


class SubClassDataUser2(DataUser):
    def __init__(self, data: SubClassData2):
        super().__init__(data)

    def update_data(self, data):
        super().update_data(data)
        third_value = self.get_third_value(data)
        self.data.second_string = str(int(third_value))


def test_1():
    data1 = SubClassData(7, "-6", -2)
    data2 = SubClassData2(-4, "14", "-2")
    user1 = SubClassDataUser(data1)
    user2 = SubClassDataUser2(data2)

    user1.update_data(data2)
    user2.update_data(data1)

    for _ in range(10):
        user1.update_data(user2.data)
        user2.update_data(user1.data)
    assert user1.data.get_sum() == 5790
    assert user2.data.get_sum() == 9361





