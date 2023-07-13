SCADDRESS = "SMART_CONTRACT_ADDRESS"
ABI_PATH = "ABI_JSON_PATH"
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
