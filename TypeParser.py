from typing import Any, List, Dict, Optional, Tuple
from multiversx_sdk_core import Address
import base64
import json


class ABITypeParser:
    def __init__(self, abi_json: Dict[str, Any]) -> None:
        self.types: Dict[str, Any] = {}
        if "types" in abi_json:
            types = abi_json["types"]
            for type_name, type_value in types.items():
                self.types[type_name] = type_value

    def parse_hex_response(self, hex_responses: list, response_type: str) -> Any:
        result = []
        for hex_response in hex_responses:
            parsed_data, _ = self.read_hex(hex_response, response_type)
            result.append(parsed_data)
        print(result)
        if len(result) == 1:
            return result[0]
        return result

    def isBase64(self, sb):
        try:
            if isinstance(sb, str):
                # If there's any unicode here, an exception will be thrown and the function will return false
                sb_bytes = bytes(sb, 'ascii')
            elif isinstance(sb, bytes):
                sb_bytes = sb
            else:
                raise ValueError("Argument must be string or bytes")
            return base64.b64encode(base64.b64decode(sb_bytes)) == sb_bytes
        except Exception:
            return False

    def read_hex(self, data: bytes, object_type: str) -> Tuple[Any, int]:
        if object_type in ["u8", "i8", "u16", "i16", "u32", "i32", "u64", "i64", "bool", "TokenIdentifier",
                           "EgldOrEsdtTokenIdentifier", "BigUint", "bytes"]:
            return self.read_primitive_type(data, object_type)
        elif object_type == "Address":
            return self.read_address_type(data)
        elif object_type.startswith("List<"):
            subtype = object_type.replace("List<", "")[:-1]
            return self.read_list_type(data, subtype)
        elif object_type.startswith("optional<"):
            subtype = object_type.replace("optional<", "")[:-1]
            return self.read_hex(data, subtype)
        elif object_type.startswith("variadic<"):
            subtype = object_type.replace("variadic<", "")[:-1]
            return self.read_hex(data, subtype)
        elif object_type.startswith("Option<"):
            subtype = object_type.replace("Option<", "")[:-1]
            return self.read_option_type(data, subtype)
        elif object_type.startswith("multi<"):
            subtypes = object_type.replace("multi<", "")[:-1].split(",")
            return self.read_multi_type(data, subtypes)
        elif object_type in self.types:
            fields = self.types[object_type]
            if isinstance(fields, dict) and fields.get("type") == "enum":
                return self.read_enum_type(data, fields)
            elif isinstance(fields, dict) and fields.get("type") == "struct":
                struct_fields = fields["fields"]
                parsed_object = {}
                offset = 0
                for field in struct_fields:
                    field_name = field["name"]
                    field_type = field["type"]
                    parsed_field, field_length = self.read_hex(data[offset:], field_type)
                    parsed_object[field_name] = parsed_field
                    offset += field_length
                return parsed_object, offset
            elif isinstance(fields, list):
                # Handle tuple type
                parsed_object = []
                offset = 0
                for field_type in fields:
                    parsed_field, field_length = self.read_hex(data[offset:], field_type)
                    parsed_object.append(parsed_field)
                    offset += field_length
                return tuple(parsed_object), offset
        else:
            raise ValueError(f"Unsupported type: {object_type}")

    def read_multi_type(self, data: bytes, subtypes: List[str]) -> Tuple[Tuple[Any, ...], int]:
        parsed_items = []
        offset = 0
        for subtype in subtypes:
            parsed_item, item_length = self.read_hex(data[offset:], subtype)
            parsed_items.append(parsed_item)
            offset += item_length
        return tuple(parsed_items), offset

    def read_enum_type(self, data: bytes, enum_fields: Dict[str, Any]) -> Tuple[Any, int]:
        variants = enum_fields.get("variants", [])
        discriminant_data = data[0]
        discriminant = discriminant_data
        variant = variants[discriminant]
        item_length = 1
        return variant["name"], item_length

    def read_primitive_type(self, data: bytes, object_type: str) -> Tuple[Any, int]:
        if object_type == "bytes":
            obj_len = int.from_bytes(data[:4], byteorder="big")
            item_length = 4
            parsed_item = data[4:obj_len+4].decode('ascii')
            if self.isBase64(parsed_item):
                parsed_item = base64.b64decode(parsed_item).decode()
                if (parsed_item.startswith('{') and parsed_item.endswith('}')) or (parsed_item.startswith('[') and parsed_item.endswith(']')):
                    try:
                        parsed_item = json.loads(parsed_item)
                    except:
                        pass
            return parsed_item, item_length + obj_len
        elif object_type in ["u8", "i8"]:
            parsed_item = int.from_bytes(data[:1], byteorder="big")
            item_length = 1
        elif object_type in ["u16", "i16"]:
            parsed_item = int.from_bytes(data[:2], byteorder="big")
            item_length = 2
        elif object_type in ["u32", "i32"]:
            parsed_item = int.from_bytes(data[:4], byteorder="big")
            item_length = 4
        elif object_type in ["u64", "i64"]:
            parsed_item = int.from_bytes(data[:8], byteorder="big")
            item_length = 8
        elif object_type == "bool":
            parsed_item = bool(int.from_bytes(data[:1], byteorder="big"))
            item_length = 1
        elif object_type == "TokenIdentifier":
            parsed_item, item_length = self.read_token_identifier(data)
        elif object_type == "EgldOrEsdtTokenIdentifier":
            parsed_item, item_length = self.read_egld_or_esdt_token_identifier(data)
        elif object_type == "BigUint":
            obj_len = int.from_bytes(data[:4], byteorder="big")
            item_length = 4
            parsed_item = int.from_bytes(data[item_length:item_length + obj_len], byteorder="big")
            item_length += obj_len
        else:
            raise ValueError(f"Unsupported primitive type: {object_type}")
        return parsed_item, item_length

    def read_token_identifier(self, data: bytes) -> Tuple[str, int]:
        if not data.hex().startswith("0000"):
            return data.decode('ascii'), len(data)
        obj_len = int.from_bytes(data[:4], byteorder="big")
        item_length = 4
        parsed_item = data[item_length:item_length + obj_len].decode("ascii")
        item_length += obj_len
        return parsed_item, item_length

    def read_egld_or_esdt_token_identifier(self, data: bytes) -> Tuple[str, int]:
        if not data.hex().startswith("0000"):
            return data.decode('ascii'), len(data)
        obj_len = int.from_bytes(data[:4], byteorder="big")
        item_length = 4
        parsed_item = data[item_length:item_length + obj_len].decode("ascii")
        item_length += obj_len
        return parsed_item, item_length

    def read_address_type(self, data: bytes) -> Tuple[str, int]:
        hex_address = data[:32].hex()
        parsed_item = Address.from_hex(hex_address, hrp="erd").bech32()
        item_length = 32
        return parsed_item, item_length

    def read_list_type(self, data: bytes, subtype: str) -> Tuple[List[Any], int]:
        parsed_list = []
        offset = 0
        while offset < len(data):
            parsed_item, item_length = self.read_hex(data[offset:], subtype)
            parsed_list.append(parsed_item)
        return parsed_list, offset

    def read_option_type(self, data: bytes, subtype: str) -> Tuple[Optional[Any], int]:
        if len(data) == 0:
            return None, 0
        presence_flag = data[0]
        offset = 1
        if presence_flag == 0:
            return None, offset
        parsed_item, item_length = self.read_hex(data[offset:], subtype)
        offset += item_length
        return parsed_item, offset

