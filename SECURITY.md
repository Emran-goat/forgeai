# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability within ForgeAI, please send an email to [INSERT SECURITY EMAIL]. All security vulnerabilities will be promptly addressed.

**Please do not report security vulnerabilities through public GitHub issues.**

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Best Practices

When deploying ForgeAI, please follow these security guidelines:

### Environment Variables

- Never commit `.env` files to version control
- Use strong, unique API keys
- Rotate API keys regularly

### Network Security

- Use HTTPS in production
- Configure CORS appropriately
- Enable rate limiting

### Data Security

- Encrypt sensitive data at rest
- Use secure file upload validation
- Implement proper access controls

### Dependencies

- Keep dependencies updated
- Run `pip audit` regularly
- Monitor for security advisories
