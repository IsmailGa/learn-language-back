import re

PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,32}$")