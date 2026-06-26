# Installation

TokenHelm requires **Python 3.11+**. Its only runtime dependency is PyYAML.

```bash
pip install tokenhelm                  # core
pip install "tokenhelm[openai]"        # + OpenAI SDK (for your own client)
pip install "tokenhelm[anthropic]"     # + Anthropic SDK
pip install "tokenhelm[gemini]"        # + google-genai SDK
pip install "tokenhelm[ollama]"        # + ollama SDK
pip install "tokenhelm[all]"           # all provider SDKs
pip install "tokenhelm[dev]"           # pytest, pytest-asyncio, pytest-cov, ruff, build
```

The provider extras pull in the SDKs **you** call to make requests. TokenHelm never imports a
provider SDK to read a response — it observes the response object your client returns — so the
core install stays tiny and you only add the extras you actually use.

## Verify

```python
import tokenhelm
print(tokenhelm.__version__)           # 0.1.0
```
