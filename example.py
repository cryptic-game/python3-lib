from cryptic import MicroService, _config
from uuid import uuid4
from sqlalchemy import Column, Integer, String, Boolean
from typing import Union

_config.set_mode("debug")

ms: MicroService = MicroService(name="echo")

database_wrapper = ms.get_wrapper()


@ms.microservice_endpoint(path=["microservice"])
def handle(data: dict, microservice: str):
    print(data, microservice)
    return {}


@ms.user_endpoint(path=["user"])
def handle(data: dict, user: str):
    print(data, user)
    return {}


class MyDataBase(database_wrapper.Base):
    __tablename__: str = 'test'

    uuid: Union[Column, str] = Column(String(36), primary_key=True, unique=True)
    name: Union[Column, str] = Column(String(255), nullable=False)

    @staticmethod
    def create(name: str) -> 'MyDataBase':
        mydb : MyDataBase = MyDataBase(uuid = str(uuid4()), name=name)

        return mydb


if __name__ == '__main__':
    ms.run()
