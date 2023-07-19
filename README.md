# ABI2API

ABI2API is a Python library for converting smart contract ABI (Application Binary Interface) on the MultiversX blockchain into a RESTful API. It allows developers to expose the functionality of a smart contract through a simple API interface, making it easier to interact with Smart Contracts.

## Features

- Converts smart contract ABI into a RESTful API
- Supports GET and POST methods for contract functions
- Generates API documentation using Swagger UI
- Handles conversion of data types between ABI and API

## Installation

1. Clone the repository:

```
git clone https://github.com/SkullElf/ABI2API.git
```
Install the required dependencies:
```
pip install -r requirements.txt
```
## Usage

Update the config.py file with your specific configuration settings.

Place the following in the relevant variables:
1. ABI JSON file path.
2. The corresponding Smart Contract address.
3. Specify the port in which you want the API to be available (default=80).
   
Start the API server:

```
python api.py
```

Access the API documentation:
Open your web browser and visit http://localhost:80/apidocs to view the Swagger UI documentation for the generated API.

Make API requests:
You can now make GET requests to interact with your smart contract functions. Refer to the API documentation for the available endpoints and request formats.

## Contributing
Contributions are welcome! If you find any issues or have suggestions for improvements, please feel free to open an issue or submit a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for more information.
