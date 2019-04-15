from cryptic import MicroService, setup_database, get_config, Config

# important: set the mode before initializing anything else
config: Config = get_config(mode="debug")
# config.set_mode("debug")  # this is the other possibility to set the mode
ms: MicroService = MicroService(name="echo")
engine, Base, session = setup_database()


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
