## API Reference

### Authentication
All endpoints require valid JWT authentication unless otherwise specified.

### Error Responses
All endpoints return standardized error responses:

```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "details": {
    "field": "specific_error_details"
  },
  "timestamp": "2024-12-05T18:00:00Z"
}
```

### Rate Limiting
- Default: 100 requests per minute per user
- Burst: 200 requests per minute
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

