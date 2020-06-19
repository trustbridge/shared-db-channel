import base64


def decrypt_kms_data(encrypted_data, aws_region):
    """Decrypt KMS encoded data."""
    import boto3  # local import so we don't need it installed for demo/local
    if not aws_region:
        import logging  # due to logging complications
        logging.error(
            "Trying to decrypt KMS value but no AWS region set"
        )
        return None

    kms = boto3.client('kms', region_name=aws_region)
    decrypted = kms.decrypt(CiphertextBlob=encrypted_data)

    if decrypted.get('KeyId'):
        # Decryption succeed
        decrypted_value = decrypted.get('Plaintext', '')
        if isinstance(decrypted_value, bytes):
            decrypted_value = decrypted_value.decode('utf-8')
        return decrypted_value


def string_or_b64kms(value, kms_prefix, aws_region):
    """Check if value is base64 encoded - if yes, decode it using KMS."""

    if not value:
        return value

    try:
        # Check if environment value base64 encoded
        if isinstance(value, (str, bytes)):
            encrypted_value = None
            if value.startswith(kms_prefix):
                encrypted_value = value[len(kms_prefix):]
            else:
                # non-encrypted value
                return value
            # If yes, decode it using AWS KMS
            data = base64.b64decode(encrypted_value)
            decrypted_value = decrypt_kms_data(data, aws_region)

            # If decryption succeed, use it
            if decrypted_value:
                value = decrypted_value
    except Exception as e:
        import logging  # due to logging complications
        logging.exception(e)
    return value
