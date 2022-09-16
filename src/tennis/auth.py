from dataclasses import dataclass


@dataclass
class User:
    username: str
    password: str


@dataclass
class Website:
    login_url: str
    search_url: str
