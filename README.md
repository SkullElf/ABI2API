# ABI2API

ABI2API is a Python library for converting smart contract ABI (Application Binary Interface) on the MultiversX blockchain into a RESTful API. It allows developers to expose the functionality of a smart contract through a simple API interface, making it easier to interact with Smart Contracts.

## Features

- Converts smart contract ABI into a RESTful API
- Supports GET and POST methods for contract functions
- Generates API documentation using Swagger UI
- Handles conversion of data types between ABI and API

# Installation

1. Clone the repository:

```bash
git clone https://github.com/SkullElf/ABI2API.git
```
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

# Configuration

```bash
# Copy the configuration file and make the necessary modifications.
cp config/config.example.py config.py
# Copy the ABI file to the project directory.
cp config/abi.example.json abi.json
```

## Configuration - config.py
### APIS list:
| Key Name                                           | API item                                  |
| -------------------------------------------------- | ----------------------------------------- |
| SCADDRESS # Replace with smart contract address    | SCADDRESS: "erdqqqqqqqqqqqqq..."          |
| ABI_PATH # Replace with ABI path                   | ABI_PATH: "abi.json"                      |
| NAME # Replace with name of the API                | NAME: "xexchange"                         |

### Config variables:
| Variable name                                      | config.py                                 |
| -------------------------------------------------- | ----------------------------------------- |
| PORT # Replace with port for the application       | PORT:  80                                 |
| ENVIRONMENT # Replace with environment name        | ENVIRONMENT:  "mainnet"                   |

## Configuration - abi.json
ABIs are a collection of metatada about the contract.

Replace the path of the abi.json file with the ABI of your smart contract.

# Usage
## Setup
Update the config.py file with your specific configuration settings.
Place the following in the APIS list of instances:
1. ABI JSON file path or URL.
2. The corresponding Smart Contract address.
3. The name for the API (will be used in the URL. See example below).

And the following in the corresponding variables:
1. Specify the port in which you want the API to be available (default=80).
2. Specify the environment in which you'd like to query the smart contracts (default="mainnet")

> TIP: `ABI_PATH` can also be a URL. This way you'll always be up to date with the latest versions!

Start the API server:

```
python api.py
```

Access the API documentation:
Open your web browser and visit http://localhost:80/NAME/ to view the Swagger UI documentation for the generated API (`NAME` being the app name specified in the config).

Make API requests:
You can now make GET requests to interact with your smart contract functions. Refer to the API documentation for the available endpoints and request formats.

> TIP: You can use the URL parameter `smartcontractaddress=X` to override the SC address in the same environment, and query SC X using the same ABI JSON

## Examples
ABI2API allows usage of multiple instances on the same port with different URL paths by entering multiple entries in the APIS list of the config:
```python
APIS = [
    {
        "SCADDRESS": "erd1qqqqqqqqqqqqqpgqc03cjhpykywz03qsavcmsjah65zkjhgxah0ssseq8a",
        "ABI_PATH": "multisig.json",
        "NAME": "multisig"
    },
    {
        "SCADDRESS": "erd1qqqqqqqqqqqqqpgq6wegs2xkypfpync8mn2sa5cmpqjlvrhwz5nqgepyg8",
        "ABI_PATH": "xoxno.json",
        "NAME": "xoxno"
    }

]
PORT = 80
```
In this example, ABI2API will provide the user with 2 different APIs on:
1. http://localhost/multisig/
2. http://localhost/xoxno/

> TIP: The `NAME` variable is a unique identifier, so make sure it's different in each entry.

# Contributing
Contributions are welcome! If you find any issues or have suggestions for improvements, please feel free to open an issue or submit a pull request.

# License
This project is licensed under the MIT License. See the LICENSE file for more information.
