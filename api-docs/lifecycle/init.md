```json
{
  "id": "init",
  "name": "init",
  "summary": "Initialize the SDK with configuration.",
  "description": "Creates a singleton SDK instance. Must be called exactly once per process before any other API. Infrastructure config only; per-transaction identifiers go on the TransactionRequest.",
  "category": "lifecycle",
  "stability": "stable",
  "since": "0.1.0",
  "parameters": [
    {
      "name": "config",
      "type": "SdkConfig",
      "required": true,
      "description": "SDK infrastructure configuration (transports, logging, cloud mode).",
      "example": {
        "transportPreference": ["TCP", "BLUETOOTH"],
        "logLevel": "INFO",
        "cloudResultMode": "MANUAL_POLL"
      }
    }
  ],
  "returns": {
    "type": "PinelabsSdk",
    "description": "The singleton SDK handle.",
    "example": "<PinelabsSdk instance>"
  },
  "errors": [
    { "variant": "AlreadyInitialized", "when": "init() called more than once in the same process.", "recoverable": false },
    { "variant": "InvalidConfig", "when": "Any config field fails validation.", "recoverable": false }
  ],
  "examples": [
    { "language": "kotlin", "code": "val sdk = PinelabsSdk.init(SdkConfig(transportPreference = listOf(TransportKind.TCP)))" },
    { "language": "python", "code": "sdk = PinelabsSdk.init(SdkConfig(transport_preference=[TransportKind.TCP]))" },
    { "language": "swift", "code": "let sdk = try PinelabsSdk.init(config: SdkConfig(transportPreference: [.tcp]))" }
  ],
  "see_also": ["do-transaction", "check-status"]
}
```
