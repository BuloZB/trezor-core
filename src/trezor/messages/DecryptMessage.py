# Automatically generated by pb2py
import protobuf as p


class DecryptMessage(p.MessageType):
    FIELDS = {
        1: ('address_n', p.UVarintType, p.FLAG_REPEATED),
        2: ('nonce', p.BytesType, 0),
        3: ('message', p.BytesType, 0),
        4: ('hmac', p.BytesType, 0),
    }
    MESSAGE_WIRE_TYPE = 51
