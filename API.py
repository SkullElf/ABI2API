from flask import Flask, request, Response
from flask_restful import Api, Resource, reqparse
from flasgger import Swagger, swag_from
import re
import asyncio
import json
from gevent.pywsgi import WSGIServer

from ParseABI import parse_abi
from config import SCADDRESS, ABI_PATH

app = Flask(__name__)
api = Api(app)

# Load ABI JSON from file
with open(ABI_PATH) as f:
    abi_json = json.load(f)
endpoints = abi_json["endpoints"]
types = abi_json["types"]

swagger = Swagger(app)


def create_endpoint_resource_class(endpoint_data):
    input_parser = reqparse.RequestParser()
    for input_data in endpoint_data['inputs']:
        input_name = input_data['name']
        input_type = input_data['type']
        multi_arg = input_data.get('multi_arg', False)

        if multi_arg:
            input_parser.add_argument(input_name, action='append', type=str, location='form')
        else:
            input_parser.add_argument(input_name, type=str, location='form')

        if input_type.startswith("optional<"):
            input_parser.add_argument(f"opt_{input_name}", type=str, location='form')

    class_name = f"EndpointResource_{endpoint_data['name']}"

    class EndpointResource(Resource):
        @swag_from({
            'parameters': [
                {
                    'name': input_data['name'],
                    'in': 'query',
                    'type': resolve_input_type(input_data['type']),
                    'required': True if not input_data['type'].startswith("optional<") else False
                } for input_data in endpoint_data['inputs']
            ],
            'responses': {
                200: {
                    'description': 'Success',
                    'schema': {
                        'type': 'object',
                        'properties': {
                            output_data.get('name', 'output'): {
                                'type': output_data.get('type', 'output')
                            } for output_data in endpoint_data.get('outputs', [])
                        }
                    }
                }
            },
            'summary': endpoint_data['name'],
            'description': '\n'.join(endpoint_data.get('docs', []))
        })
        def get(self):
            result = asyncio.run(self.get_async())
            return result

        async def get_async(self):
            # Parse the input data from the request
            inputs = {}
            args = []
            for input_data in endpoint_data['inputs']:
                input_name = input_data['name']
                input_value = str(request.args.get(input_name))
                is_optional = input_data['type'].startswith("optional<")

                if is_optional:
                    if input_value is None:
                        opt_input_value = request.args.get(f"opt_{input_name}")
                        if opt_input_value is None:
                            inputs[input_name] = None
                        else:
                            inputs[input_name] = [opt_input_value]
                    else:
                        inputs[input_name] = [input_value]
                else:
                    inputs[input_name] = input_value

                if is_optional:
                    args.append({
                        "value": inputs[input_name][0] if inputs[input_name] else None,
                        "type": input_data["type"]
                    })
                else:
                    args.append({
                        "value": input_value,
                        "type": input_data["type"]
                    })

            # Process the input and call the smart contract based on the endpoint name
            output = await parse_abi(
                SCADDRESS,
                endpoint_data["name"],
                endpoints,
                types,
                args=args
            )

            if output is None:
                return Response(f"Data returned empty", 500)
            if len([d for d in endpoint_data['outputs'] if 'multi_result' in d and d['multi_result']]) == len(
                    endpoint_data['outputs']):
                return Response(json.dumps(output), mimetype='application/json')  # Return the output as JSON
            return Response(json.dumps(output[0]), mimetype='application/json')  # Return the first element as JSON

    EndpointResource.__name__ = class_name
    return EndpointResource


def resolve_input_type(input_type):
    cleaned_type = re.sub(r"<.*?>", "", input_type)
    cleaned_type = re.sub(r"optional|variadic", "", cleaned_type)
    datatypes = {
        "BigUint": "integer",
        "u64": "integer",
        "Address": "string",
        "bool": "boolean",
        "TokenIdentifier": "string",
        "EgldOrEsdtTokenIdentifier": "string",
        "u32": "integer",
        "u8": "integer"
    }
    return datatypes.get(cleaned_type, "string")


# Add the endpoint resources dynamically based on the ABI JSON
for endpoint in abi_json['endpoints']:
    if endpoint["mutability"] == "readonly":
        resource_class = create_endpoint_resource_class(endpoint)
        api.add_resource(resource_class, f"/{endpoint['name']}")


if __name__ == '__main__':
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    http_server.serve_forever()
