import base64
import aiohttp
from multiversx_sdk_core import Address
import json
from config import PROXY_URL, SIZE_PER_TYPE
from TypeParser import ABITypeParser


def int_to_hex(number):
    hex_value = format(int(number), 'x')
    return '0' + hex_value if len(hex_value) % 2 else hex_value


def convert_args(args):
    args_output = []
    for arg in args:
        print(arg)
        if arg["type"].startswith("variadic<"):
            arg["type"] = arg["type"].replace("variadic<", "")[:-1]
        if "<" in arg["type"]:
            arg["type"] = arg["type"].split("<")[1].replace(">", "")
        if ',' in arg["value"]:
            for piece in arg["value"].split(','):
                if arg["type"] in list(SIZE_PER_TYPE.keys()):
                    args_output.append(int_to_hex(piece))
                elif arg["type"] == "Address":
                    args_output.append(Address.from_bech32(piece).hex())
                else:
                    args_output.append(piece.encode('ascii').hex())
        else:
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
            if response_json["data"]["data"]["returnCode"] != "ok":
                return None, response_json["data"]["data"]["returnMessage"]
            return response_json["data"]["data"]["returnData"]


async def parse_abi(sc_address, func, endpoints, abi_json, args=None):
    if args is None:
        args = []
    endpoint_data = next((d for d in endpoints if d['name'] == func), None)
    if endpoint_data is None:
        return None
    answer = await query_sc(func, sc_address, args=args)
    if isinstance(answer, tuple):
        return 400, answer[1]
    decoded_answer = decode_return_data(answer)
    abi_type_parser = ABITypeParser(abi_json)
    response_type = endpoint_data["outputs"][0]["type"]
    parsed_data = abi_type_parser.parse_hex_response(decoded_answer, response_type)
    return 200, parsed_data
