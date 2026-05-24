class Filter:
    def __call__(self, client, message) -> bool:
        return True

    def __and__(self, other: 'Filter') -> 'AndFilter':
        return AndFilter(self, other)

    def __or__(self, other: 'Filter') -> 'OrFilter':
        return OrFilter(self, other)

    def __invert__(self) -> 'NotFilter':
        return NotFilter(self)


class AndFilter(Filter):
    def __init__(self, *filters: Filter):
        self.filters = filters

    def __call__(self, client, message) -> bool:
        return all(f(client, message) for f in self.filters)


class OrFilter(Filter):
    def __init__(self, *filters: Filter):
        self.filters = filters

    def __call__(self, client, message) -> bool:
        return any(f(client, message) for f in self.filters)


class NotFilter(Filter):
    def __init__(self, filter: Filter):
        self.filter = filter

    def __call__(self, client, message) -> bool:
        return not self.filter(client, message)


class text(Filter):
    def __init__(self, text: str):
        self.text = text.lower()

    def __call__(self, client, message) -> bool:
        return message.text.lower() == self.text if message.text else False


class command(Filter):
    def __init__(self, command: str, prefix: str = "/"):
        self.command = (prefix + command).lower()

    def __call__(self, client, message) -> bool:
        return message.text.lower().startswith(self.command) if message.text else False


class user_id(Filter):
    def __init__(self, user_id: str):
        self.user_id = user_id

    def __call__(self, client, message) -> bool:
        return message.sender == self.user_id


class me(Filter):
    def __init__(self):
        pass

    def __call__(self, client, message) -> bool:
        return message.sender == client.me.contact.id if client.me else False


class any(Filter):
    def __init__(self):
        pass

    def __call__(self, client, message) -> bool:
        return True


class filters:
    text = text
    command = command
    user_id = user_id
    me = me
    any = any


def user(user_id: str):
    return user_id(user_id)
