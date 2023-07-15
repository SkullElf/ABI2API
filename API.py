from flask import Flask, request, Response, jsonify
from flask_restful import Api, Resource, reqparse
from flask_swagger_ui import get_swaggerui_blueprint
from marshmallow import Schema, fields
import re
from flasgger import Swagger, swag_from
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

# Set up Swagger UI blueprint
swagger_ui_blueprint = get_swaggerui_blueprint(
    '/api/docs',
    '/api/swagger.json',
    config={
        'app_name': "ABI API"
    }
)
app.register_blueprint(swagger_ui_blueprint, url_prefix='/api/docs')

swagger = Swagger(app)


def create_endpoint_resource_class(endpoint_data):
    input_parser = reqparse.RequestParser()
    swagger_parameters = []  # List to hold the Swagger parameters

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

        # Generate Swagger parameter definition for each input
        swagger_parameter = {
            'name': input_name,
            'in': 'query',
            'required': True if not input_type.startswith("optional") else False
        }

        # Determine the data type of the input parameter
        if multi_arg:
            swagger_parameter['type'] = 'array'
            swagger_parameter['items'] = {
                'type': 'string'
            }
        else:
            swagger_parameter['type'] = resolve_input_type(input_type)

        swagger_parameters.append(swagger_parameter)

    class_name = f"EndpointResource_{endpoint_data['name']}"

    class EndpointResource(Resource):
        @swag_from({
            'parameters': swagger_parameters,
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
                is_optional = input_data['type'].startswith("optional")

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
                        "value": str(input_value),
                        "type": input_data["type"]
                    })

            # Process the input and call the smart contract based on the endpoint name
            output = await parse_abi(
                SCADDRESS,
                endpoint_data["name"],
                endpoints,
                abi_json,
                args=args
            )
            code, output = output
            if code == 400:
                return Response(output, 400)

            return jsonify(output)  # Return the output as JSON

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


class ABITypeSchema(Schema):
    class Meta:
        ordered = True

    name = fields.Str(required=True)
    mutability = fields.Str(required=True)
    inputs = fields.List(fields.Dict(), required=True)
    outputs = fields.List(fields.Dict())


# Generate the Swagger JSON specification
swagger_json = {
    'swagger': '2.0',
    'info': {
        'title': 'ABI API',
        'description': 'API documentation for ABI endpoints',
        'version': '1.0'
    },
    'paths': {},
    'definitions': {}
}

for endpoint in abi_json['endpoints']:
    if endpoint["mutability"] == "readonly":
        schema = ABITypeSchema()
        endpoint_data = schema.load(endpoint)
        resource_class = create_endpoint_resource_class(endpoint_data)

        # Add the resource to the API
        api.add_resource(resource_class, f"/{endpoint['name']}")

        # Generate the path for the Swagger JSON specification
        swagger_path = f"/{endpoint['name']}"
        swagger_parameters = swagger_json['paths'].get(swagger_path, {}).get('parameters', [])
        swagger_parameters.extend(endpoint_data['inputs'])
        swagger_json['paths'][swagger_path] = {
            'get': {
                'summary': endpoint['name'],
                'parameters': swagger_parameters,
                'responses': {
                    '200': {
                        'description': 'Success',
                        'schema': {
                            '$ref': f"#/definitions/{endpoint['name']}_response"
                        }
                    }
                }
            }
        }

        # Generate the definition for the Swagger JSON specification
        swagger_definition = {
            'type': 'object',
            'properties': {
                output_data.get('name', 'output'): {
                    'type': output_data.get('type', 'output')
                } for output_data in endpoint.get('outputs', [])
            }
        }
        swagger_json['definitions'][f"{endpoint['name']}_response"] = swagger_definition

# Endpoint to serve the Swagger JSON specification
@app.route('/api/swagger.json')
def serve_swagger_json():
    return jsonify(swagger_json)


if __name__ == '__main__':
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    http_server.serve_forever()