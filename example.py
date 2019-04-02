from cryptic import MicroService

ms: MicroService = MicroService(name="echo")


@ms.microservice_endpoint(path=["microservice"])
def handle(data: dict, microservice: str):
    print(data, microservice)
    return {}


@ms.user_endpoint(path=["user"])
def handle(data: dict, user: str):
    print(data, user)
    return {}


if __name__ == '__main__':
    ms.run()
