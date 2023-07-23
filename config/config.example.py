APIS = [
    {
        "SCADDRESS": "SC_ADDRESS_HERE",
        "ABI_PATH": "ABI_JSON_PATH_OR_URL_HERE",
        "NAME": "APP_NAME_HERE"
    }
]
PORT = 80
ENVIRONMENT = "mainnet"
ENVIRONMENTS = {
    "mainnet": "https://gateway.multiversx.com",
    "devnet": "https://devnet-gateway.multiversx.com",
    "testnet": "https://testnet-gateway.multiversx.com"
}
PROXY_URL = ENVIRONMENTS[ENVIRONMENT]
SIZE_PER_TYPE = {
    "i8": 1,
    "i16": 2,
    "i32": 4,
    "i64": 8,
    "i128": 16,
    "u8": 1,
    "u16": 2,
    "u32": 4,
    "u64": 8,
    "u128": 16,
}
