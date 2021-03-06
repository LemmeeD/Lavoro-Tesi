class GeckoDriverExecutableNotFoundError(Exception):
    def __init__(self):
        temp = f"No geckodriver executable found."
        self.message = f"No geckodriver executable found."
        BaseException.__init__(self, temp)

    def __str__(self):
        return f'{self.message}'

