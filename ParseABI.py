import base64
import aiohttp
from multiversx_sdk_core import Address

from config import PROXY_URL, SIZE_PER_TYPE


def int_to_hex(number):
    hex_value = format(int(number), 'x')
    return '0' + hex_value if len(hex_value) % 2 else hex_value


def convert_args(args):
    args_output = []
    for arg in args:
        if arg["type"] in list(SIZE_PER_TYPE.keys()):
            args_output.append(int_to_hex(arg["value"]))
        elif arg["type"] == "Address":
            args_output.append(Address.from_bech32(arg["value"]).hex())
        else:
            args_output.append(arg["value"].encode('ascii').hex())
    return args_output


def decode_return_data(data):
    if data is None:
        return None
    result = []
    for item in data:
        result.append(bytes.fromhex(base64.b64decode(item).hex()))
    return result


async def query_sc(endpoint, sc_address, args=None):
    if args is None:
        args = []
    else:
        args = convert_args(args)
    url = f"{PROXY_URL}/vm-values/query"
    body = {
        "scAddress": sc_address,
        "funcName": endpoint,
        "value": "0",
        "args": args
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=body) as response:
            response_json = await response.json()
            return response_json["data"]["data"]["returnData"]


def read_hex(data, object_type, types):
    if data.hex() == "":
        return None, 0
    parsed_data = {}
    offset = 0
    if object_type in (["BigUint", "Address", "bool", "TokenIdentifier", "EgldOrEsdtTokenIdentifier"]) + list(SIZE_PER_TYPE.keys()):
        result = None
        if object_type in list(SIZE_PER_TYPE.keys()):
            result = int.from_bytes(data[offset:offset + SIZE_PER_TYPE.get(object_type)], byteorder="big")
            offset += SIZE_PER_TYPE.get(object_type)
        elif object_type == "bool":
            result = data[offset] == 1
            offset += 1
        elif object_type in ["TokenIdentifier", "EgldOrEsdtTokenIdentifier"]:
            result = data.decode()
            offset += 4
        elif object_type in ["BigUint"]:
            obj_len = int.from_bytes(data[offset:offset + 4], byteorder="big")
            offset += 4
            result = str(int.from_bytes(data[offset:offset + obj_len], byteorder="big"))
            offset += obj_len
        elif object_type == "Address":
            hex_address = data[offset:offset + 32].hex()
            result = Address.from_hex(hex_address, hrp="erd").bech32()
            offset += 32
        return result, offset

    if object_type not in types or types[object_type]["type"] == "struct":
        for field in types[object_type]["fields"]:
            field_name = field["name"]
            field_type = field["type"]
            if field_type.startswith("List<"):
                list_length = int.from_bytes(data[offset:offset + 4], byteorder="big")
                offset += 4
                subtype = field_type.replace("List<", "").replace(">", "")
                parsed_data[field_name] = []
                for index in range(list_length):
                    parsed_item, offset1 = read_hex(data[offset:], subtype, types)
                    offset += offset1
                    parsed_data.get(field_name).append(parsed_item)
            if field_type.startswith("Option<"):
                if data[offset] == 0:
                    offset += 1
                    continue
                offset += 1
                field_type = field_type.replace("Option<", '').replace(">", "")
            if field_type in ["BigUint", "Address", "bool", "TokenIdentifier", "EgldOrEsdtTokenIdentifier"] + list(SIZE_PER_TYPE.keys()):
                if field_type == "bool":
                    parsed_data[field_name] = bool(int(data[offset], 16))
                    offset += 1
                elif object_type in list(SIZE_PER_TYPE.keys()):
                    parsed_data[field_name] = int.from_bytes(data[offset:offset + SIZE_PER_TYPE.get(object_type)], byteorder="big")
                    offset += SIZE_PER_TYPE.get(object_type)
                elif field_type in ["TokenIdentifier", "EgldOrEsdtTokenIdentifier"]:
                    obj_len = int.from_bytes(data[offset:offset + 4], byteorder="big")
                    offset += 4
                    parsed_data[field_name] = data[offset:offset + obj_len].decode('ascii')
                    offset += obj_len
                elif field_type in ["BigUint"]:
                    obj_len = int.from_bytes(data[offset:offset + 4], byteorder="big")
                    offset += 4
                    parsed_data[field_name] = str(int.from_bytes(data[offset:offset + obj_len], byteorder="big"))
                    offset += obj_len
                elif field_type == "Address":
                    hex_address = data[offset:offset + 32].hex()
                    parsed_data[field_name] = Address.from_hex(hex_address, hrp="erd").bech32()
                    offset += 32
            elif field_type in types:
                parsed_data[field_name], offset1 = read_hex(data[offset:], field_type, types)
                offset += offset1
    elif types[object_type]["type"] == "enum":
        for item in types[object_type]["variants"]:
            if data[offset] == item["discriminant"]:
                offset += 1
                return item["name"], offset
    return parsed_data, offset


async def parse_abi(sc_address, func, endpoints, types, args=None):
    if args is None:
        args = []
    endpoint_data = next((d for d in endpoints if d['name'] == func), None)
    if endpoint_data is None:
        return None
    answer = await query_sc(func, sc_address, args=args)
    return_data_type = endpoint_data["outputs"][0]["type"]

    if return_data_type.startswith("variadic<"):
        return_data_type = return_data_type.replace("variadic<", "")[:-1]
    if "<" in return_data_type:
        return_data_type = return_data_type.split("<")[1].replace(">", "")
    decoded_answer = decode_return_data(answer)
    if decoded_answer is None:
        return None
    output = []
    for l1 in decoded_answer:
        if ',' in return_data_type:
            tuple_output = []
            for single_type in return_data_type.split(','):
                data_output, _ = read_hex(l1, single_type, types)
                tuple_output.append(data_output)
            data_output = tuple(tuple_output)
        else:
            data_output, _ = read_hex(l1, return_data_type, types)
        output.append(data_output)
    return output
