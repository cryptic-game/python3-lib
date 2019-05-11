from cryptic import MicroService, get_config, Config
from uuid import uuid4
from sqlalchemy import Column, String
from typing import Union

config: Config = get_config("debug")  # this sets config to debug mode
ms: MicroService = MicroService(name="echo")
db_wrapper = ms.get_wrapper()


@ms.microservice_endpoint(path=["microservice"])
def handle(data: dict, microservice: str):
    print(data, microservice)
    return {}


@ms.user_endpoint(path=["user"])
def handle(data: dict, user: str):
    print(data, user)
    return {}


class Test(db_wrapper.Base):
    __tablename__: str = 'test'

    uuid: Union[Column, str] = Column(String(36), primary_key=True, unique=True)
    name: Union[Column, str] = Column(String(255), nullable=False)

    @staticmethod
    def create(name: str) -> 'Test':
        my_test: Test = Test(uuid=str(uuid4()), name=name)

        return my_test


if __name__ == '__main__':
    ms.run()
