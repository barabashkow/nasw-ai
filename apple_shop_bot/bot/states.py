from enum import IntEnum


class CheckoutState(IntEnum):
    ASK_NAME = 1
    ASK_PHONE = 2
    ASK_DELIVERY = 3
    ASK_ADDRESS = 4
    CONFIRM = 5