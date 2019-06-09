from cryptic import MicroService, get_config, Config
from scheme import *

config: Config = get_config("debug")  # this sets config to debug mode
ms: MicroService = MicroService(name="echo")
db_wrapper = ms.get_wrapper()

user_device: dict = {  # is just an example does not have to make sense
    'user_uuid': Text(nonempty=True),
    'device_uuid': Email(nonempty=True),
    'active': Boolean(required=True, default=True),
    'somedata': Integer(minimum=0, default=0),
}


@ms.microservice_endpoint(path=["microservice"])
def handle(data: dict, microservice: str):
    return {"name": data["yourname"]}


@ms.user_endpoint(path=["user"], requires=user_device)
def handle(data: dict, user: str):
    # Input is now already validated
    print(data["username"])
    return {"ok": True}


if __name__ == '__main__':
    ms.run()
