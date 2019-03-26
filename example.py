from cryptic import MicroService


def handle(endpoint, data, user):
    print(endpoint, data, user)
    return data


def handle_ms(data):
    print(data)
    return data

if __name__ == '__main__':
    m = MicroService('echo', handle, handle_ms)
    m.run()
