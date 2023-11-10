# Kafka Security Configuration

# FastStream Kafka Security

This chapter discusses the security options available in FastStream and how to use them.

## Security Objects

FastStream allows you to enhance the security of applications by using security objects when creating brokers. These security objects encapsulate security-related configurations and mechanisms. Security objects supported in FastStream are (More are planned in the future such as SASL OAuth):

### 1. BaseSecurity Object

**Purpose:** The `BaseSecurity` object wraps `ssl.SSLContext` object and is used to enable SSL/TLS encryption for secure communication between FastStream services and external components such as message brokers.

**Usage:**

```python linenums="1"
{!> docs_src/kafka/basic_security/app.py [ln:1-11] !}
```

### 2. SASLPlaintext Object with SSL/TLS

**Purpose:** The `SASLPlaintext` object is used for authentication in SASL (Simple Authentication and Security Layer) plaintext mode. It allows you to provide a username and password for authentication.

**Usage:**

```python linenums="1"
{!> docs_src/kafka/plaintext_security/app.py [ln:1-11] !}
```

**Using any SASL authentication without SSL:**

The following example should raise a **RuntimeException**:

```python linenums="1"
{!> docs_src/kafka/security_without_ssl/example.py [ln:8] !}
```

If the user does not want to use SSL encryption, they must explicitly set the `use_ssl` parameter to `False` when creating a SASL object.

```python linenums="1"
{!> docs_src/kafka/security_without_ssl/example.py [ln:11] !}
```

### 3. SASLScram256/512 Object with SSL/TLS

**Purpose:** The `SASLScram256` and `SASLScram512` objects are used for authentication using the Salted Challenge Response Authentication Mechanism (SCRAM).

**Usage:**

=== "SCRAM256"
    ```python linenums="1"
    {!> docs_src/kafka/sasl_scram256_security/app.py [ln:1-11] !}
    ```

=== "SCRAM512"
    ```python linenums="1"
    {!> docs_src/kafka/sasl_scram512_security/app.py [ln:1-11] !}
    ```
