```json
{
  "id": "check-status",
  "name": "checkStatus",
  "summary": "Poll the status of an in-flight or completed transaction by eventId.",
  "description": "Queries the terminal (or cloud, depending on transport) for the current state of a previously started transaction. Useful after process restarts or network blips to resume tracking an in-flight transaction.",
  "category": "transaction",
  "stability": "stable",
  "since": "0.1.0",
  "parameters": [
    {
      "name": "eventId",
      "type": "String",
      "required": true,
      "description": "The eventId returned by doTransaction().",
      "constraints": { "format": "uuid-v4" },
      "example": "550e8400-e29b-41d4-a716-446655440000"
    }
  ],
  "returns": {
    "type": "TransactionStatus",
    "description": "One of PENDING, IN_PROGRESS, SUCCESS, FAILED, UNKNOWN.",
    "example": "IN_PROGRESS"
  },
  "errors": [
    { "variant": "NotInitialized", "when": "init() was not called.", "recoverable": false },
    { "variant": "InvalidInput", "when": "eventId is not a valid UUIDv4.", "recoverable": false },
    { "variant": "EventNotFound", "when": "The terminal/cloud has no record of this eventId.", "recoverable": false },
    { "variant": "TransportUnavailable", "when": "No transport available to reach the terminal.", "recoverable": true }
  ],
  "examples": [
    { "language": "kotlin", "code": "val status = sdk.checkStatus(\"550e8400-e29b-41d4-a716-446655440000\")" },
    { "language": "python", "code": "status = sdk.check_status(\"550e8400-e29b-41d4-a716-446655440000\")" },
    { "language": "swift", "code": "let status = try sdk.checkStatus(eventId: \"550e8400-e29b-41d4-a716-446655440000\")" }
  ],
  "see_also": ["do-transaction", "cancel-transaction"]
}
```
