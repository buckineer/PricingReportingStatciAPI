import random
import string


def random_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=6))
