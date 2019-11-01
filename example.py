from cryptic import MicroService
from uuid import uuid4
from sqlalchemy import Column, String
from typing import Union
from scheme import Text, UUID

ms: MicroService = MicroService(name="test")
db_wrapper = ms.get_wrapper()

user_scheme = {"your_pets_name": Text(required=True), "wallet": UUID()}


@ms.microservice_endpoint(path=["microservice"])
def handle(data: dict, microservice: str):
    return {"my_name": "microservice"}


@ms.user_endpoint(path=["user"], requires=user_scheme)
def handle(data: dict, user: str):
    can_pay: bool = ms.contact_microservice("currency", ["exists"], {"source_uuid": data["wallet"]})["exists"]
    if can_pay:
        my_pet: Test = Test.create(data["your_pets_name"])

        return {"uuid": my_pet.uuid}
    else:
        return {"error": "valid_wallet_required"}


class Test(db_wrapper.Base):
    __tablename__: str = "test"

    uuid: Union[Column, str] = Column(String(36), primary_key=True, unique=True)
    name: Union[Column, str] = Column(String(255), nullable=False)

    @staticmethod
    def create(name: str) -> "Test":
        my_test: Test = Test(uuid=str(uuid4()), name=name)

        db_wrapper.session.add(my_test)
        db_wrapper.session.commit()

        return my_test


if __name__ == "__main__":
    db_wrapper.Base.metadata.create_all(bind=db_wrapper.engine)
    ms.run()
