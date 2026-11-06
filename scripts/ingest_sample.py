from pathlib import Path

import httpx


API_URL = "http://localhost:8000/api/v1/documents/text"
POLICY_PATH = Path("data/sample_policy.md")


def main() -> None:
    policy_text = POLICY_PATH.read_text(encoding="utf-8")

    response = httpx.post(
        API_URL,
        json={
            "source": "synthetic-homeowners-policy-v1",
            "title": "Sample Homeowners Policy",
            "text": policy_text,
            "document_type": "insurance_policy",
        },
        timeout=60,
    )
    print("Status code:", response.status_code)
    print("Response body:", response.text)


if __name__ == "__main__":
    main()
