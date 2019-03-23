from cryptic import MicroService


def handle(endpoint, data, user):
    print(endpoint, data, user)
    return data


def handle_ms(ms, data, tag):
    print(ms, data, tag)


if __name__ == '__main__':
    m = MicroService('echo', handle, handle_ms)
    m.run()
