#!/usr/bin/env python3
"""
Simple script to test LLM API connection
Run this to diagnose if the LLM server itself is the problem
"""

import os
import sys
import time
from dotenv import load_dotenv
from openai import OpenAI
import httpx

# Load environment variables
load_dotenv()

def test_llm_connection():
    """Test if LLM API is accessible and responding"""

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    base_url = os.getenv("LLM_BASE_URL")

    print("=" * 60)
    print("LLM Connection Test")
    print("=" * 60)
    print(f"API Key: {'✓ Set' if api_key else '✗ Not set'}")
    print(f"Model: {model}")
    print(f"Base URL: {base_url if base_url else 'OpenAI default'}")
    print("=" * 60)

    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not set in environment")
        return False

    try:
        print("\n🔄 Creating OpenAI client...")

        # Create client with short timeout for testing
        http_client = httpx.Client(
            timeout=httpx.Timeout(
                connect=10.0,
                read=30.0,
                write=10.0,
                pool=10.0
            )
        )

        if base_url:
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                http_client=http_client,
                max_retries=1  # Only retry once for testing
            )
        else:
            client = OpenAI(
                api_key=api_key,
                http_client=http_client,
                max_retries=1
            )

        print("✓ Client created successfully")

        print("\n🔄 Sending test request to LLM...")
        print("   (This will take a few seconds...)")

        start_time = time.time()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Hello! Please respond with just 'OK'"}
            ],
            max_tokens=10
        )

        elapsed = time.time() - start_time

        print(f"\n✅ SUCCESS! LLM is responding")
        print(f"   Response time: {elapsed:.2f} seconds")
        print(f"   Response: {response.choices[0].message.content}")
        print(f"   Tokens used: {response.usage.total_tokens}")

        return True

    except httpx.ConnectError as e:
        print(f"\n❌ CONNECTION ERROR: Cannot connect to LLM server")
        print(f"   {str(e)}")
        print(f"\n💡 Possible causes:")
        print(f"   - LLM server is down")
        print(f"   - Incorrect base URL: {base_url}")
        print(f"   - Network/firewall blocking connection")
        return False

    except httpx.TimeoutException as e:
        print(f"\n❌ TIMEOUT ERROR: LLM server not responding")
        print(f"   {str(e)}")
        print(f"\n💡 Possible causes:")
        print(f"   - LLM server is overloaded or slow")
        print(f"   - Network latency issues")
        return False

    except Exception as e:
        error_type = type(e).__name__
        print(f"\n❌ ERROR [{error_type}]: {str(e)}")

        # Check for specific error types
        if "401" in str(e) or "Unauthorized" in str(e):
            print(f"\n💡 Authentication failed - check your API key")
        elif "429" in str(e) or "rate" in str(e).lower():
            print(f"\n💡 Rate limit exceeded - LLM server is rejecting requests")
        elif "500" in str(e) or "502" in str(e) or "503" in str(e):
            print(f"\n💡 LLM server error - server is having internal issues")
        else:
            print(f"\n💡 Unknown error - check logs for details")

        return False

if __name__ == "__main__":
    print("\n")
    success = test_llm_connection()
    print("\n" + "=" * 60)

    if success:
        print("✅ LLM connection is working!")
        print("   The problem is likely in the application code.")
        sys.exit(0)
    else:
        print("❌ LLM connection failed!")
        print("   The problem is with the LLM server or configuration.")
        sys.exit(1)
