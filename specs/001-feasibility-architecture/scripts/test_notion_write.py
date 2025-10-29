#!/usr/bin/env python3
"""
Notion Write Test Script (T007)

Tests programmatic entry creation for CollabIQ database:
1. Create test company entries in Company database
2. Create CollabIQ entries with relations
3. Test fuzzy matching scenarios
4. Measure API rate limits
"""

import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any

from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Notion credentials
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID_COLLABIQ = os.getenv("NOTION_DATABASE_ID_COLLABIQ")
NOTION_DATABASE_ID_CORP = os.getenv("NOTION_DATABASE_ID_CORP")

def check_env_vars():
    """Check if all required environment variables are set."""
    missing = []
    if not NOTION_API_KEY:
        missing.append("NOTION_API_KEY")
    if not NOTION_DATABASE_ID_COLLABIQ:
        missing.append("NOTION_DATABASE_ID_COLLABIQ")
    if not NOTION_DATABASE_ID_CORP:
        missing.append("NOTION_DATABASE_ID_CORP")

    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        sys.exit(1)

def create_test_companies(notion: Client) -> Dict[str, str]:
    """Create test company entries and return their page IDs."""
    print("\n📝 Creating test company entries...")

    # Actual field names from the existing database:
    # - Known Name (Title)
    # - Is Portfolio? (Checkbox)
    # - Shinsegae affiliates? (Checkbox)

    companies = {
        "테스트스타트업": {
            "Is Portfolio?": False,
            "Shinsegae affiliates?": False,
            "간략소개 (국문)": "테스트용 스타트업 회사"
        },
        "테스트포트폴리오": {
            "Is Portfolio?": True,
            "Shinsegae affiliates?": False,
            "간략소개 (국문)": "테스트용 포트폴리오 회사"
        },
        "테스트신세계계열사": {
            "Is Portfolio?": False,
            "Shinsegae affiliates?": True,
            "간략소개 (국문)": "테스트용 신세계 계열사"
        }
    }

    company_page_ids = {}

    for company_name, properties in companies.items():
        try:
            print(f"   Creating: {company_name}...")

            # Use direct HTTP request since notion-client has issues
            import requests
            url = "https://api.notion.com/v1/pages"
            headers = {
                "Authorization": f"Bearer {NOTION_API_KEY}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }

            payload = {
                "parent": {"database_id": NOTION_DATABASE_ID_CORP},
                "properties": {
                    "Known Name": {
                        "title": [{"text": {"content": company_name}}]
                    },
                    "Is Portfolio?": {
                        "checkbox": properties["Is Portfolio?"]
                    },
                    "Shinsegae affiliates?": {
                        "checkbox": properties["Shinsegae affiliates?"]
                    },
                    "간략소개 (국문)": {
                        "rich_text": [{"text": {"content": properties["간략소개 (국문)"]}}]
                    }
                }
            }

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                page = response.json()
                company_page_ids[company_name] = page["id"]
                print(f"   ✅ Created: {company_name} ({page['id'][:8]}...)")
            else:
                print(f"   ❌ Failed to create {company_name}: HTTP {response.status_code} - {response.text}")

        except Exception as e:
            print(f"   ❌ Failed to create {company_name}: {e}")

    return company_page_ids

def test_create_collabiq_entry(notion: Client, company_ids: Dict[str, str]) -> bool:
    """Test creating a CollabIQ entry with all field types."""
    print("\n🧪 Test 1: Create entry with all field types...")

    # Actual field names from CollabIQ database:
    # - 협력주체 (Title)
    # - 스타트업명 (Relation)
    # - 협업기관 (Relation)
    # - 협업내용 (Rich Text)
    # - 협업형태 (Select: [B] Non-PortCo X SSG, etc.)
    # - 협업강도 (Select: 이해, etc.)
    # - 날짜 (Date)
    # - 담당자 (People)

    try:
        import requests
        url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        payload = {
            "parent": {"database_id": NOTION_DATABASE_ID_COLLABIQ},
            "properties": {
                "협력주체": {
                    "title": [{"text": {"content": "테스트포트폴리오-테스트신세계계열사"}}]
                },
                "스타트업명": {
                    "relation": [{"id": company_ids.get("테스트포트폴리오", "")}]
                },
                "협업기관": {
                    "relation": [{"id": company_ids.get("테스트신세계계열사", "")}]
                },
                "협업내용": {
                    "rich_text": [{"text": {"content": "테스트용 협업 내용: API 연동 테스트를 위한 샘플 엔트리"}}]
                },
                "협업형태": {
                    "select": {"name": "[A] PortCo X SSG"}
                },
                "협업강도": {
                    "select": {"name": "협력"}
                },
                "날짜": {
                    "date": {"start": "2025-10-29"}
                }
            }
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            page = response.json()
            print(f"   ✅ Created CollabIQ entry: {page['id'][:8]}...")
            print(f"      URL: {page['url']}")
            return True
        else:
            print(f"   ❌ Failed: HTTP {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Failed to create CollabIQ entry: {e}")
        return False

def test_relation_linking(notion: Client, company_ids: Dict[str, str]) -> bool:
    """Test relation linking to unified company database."""
    print("\n🧪 Test 2: Test relation linking to unified company database...")

    import requests
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    try:
        # Test 2a: Link to startup company
        print("   Testing link to startup company...")
        payload1 = {
            "parent": {"database_id": NOTION_DATABASE_ID_COLLABIQ},
            "properties": {
                "협력주체": {"title": [{"text": {"content": "테스트스타트업-테스트신세계계열사"}}]},
                "스타트업명": {"relation": [{"id": company_ids.get("테스트스타트업", "")}]},
                "협업기관": {"relation": [{"id": company_ids.get("테스트신세계계열사", "")}]},
                "협업내용": {"rich_text": [{"text": {"content": "스타트업과 계열사 간 협업 테스트"}}]},
                "협업형태": {"select": {"name": "[B] Non-PortCo X SSG"}},
                "협업강도": {"select": {"name": "이해"}},
                "날짜": {"date": {"start": "2025-10-29"}}
            }
        }
        response1 = requests.post(url, headers=headers, json=payload1)
        if response1.status_code == 200:
            print(f"   ✅ Created link to startup: {response1.json()['id'][:8]}...")
        else:
            print(f"   ❌ Failed: {response1.text}")
            return False

        # Test 2b: Link to portfolio companies (PortCo x PortCo)
        print("   Testing PortCo x PortCo linking...")
        payload2 = {
            "parent": {"database_id": NOTION_DATABASE_ID_COLLABIQ},
            "properties": {
                "협력주체": {"title": [{"text": {"content": "테스트포트폴리오-테스트포트폴리오"}}]},
                "스타트업명": {"relation": [{"id": company_ids.get("테스트포트폴리오", "")}]},
                "협업기관": {"relation": [{"id": company_ids.get("테스트포트폴리오", "")}]},
                "협업내용": {"rich_text": [{"text": {"content": "포트폴리오 내부 협력 테스트"}}]},
                "협업형태": {"select": {"name": "[C] PortCo X PortCo"}},
                "협업강도": {"select": {"name": "협력"}},
                "날짜": {"date": {"start": "2025-10-29"}}
            }
        }
        response2 = requests.post(url, headers=headers, json=payload2)
        if response2.status_code == 200:
            print(f"   ✅ Created PortCo x PortCo link: {response2.json()['id'][:8]}...")
        else:
            print(f"   ❌ Failed: {response2.text}")
            return False

        return True

    except Exception as e:
        print(f"   ❌ Failed relation linking test: {e}")
        return False

def test_api_rate_limits(notion: Client) -> tuple:
    """Measure API rate limits."""
    print("\n🧪 Test 3: Measure API rate limits...")

    try:
        # Test rapid requests
        start_time = time.time()
        successful_requests = 0
        rate_limit_errors = 0

        for i in range(5):
            try:
                notion.databases.retrieve(database_id=NOTION_DATABASE_ID_COLLABIQ)
                successful_requests += 1
            except Exception as e:
                if "rate_limited" in str(e).lower():
                    rate_limit_errors += 1
                    print(f"   ⚠️  Rate limit hit on request {i+1}")

        elapsed_time = time.time() - start_time
        requests_per_second = successful_requests / elapsed_time if elapsed_time > 0 else 0

        print(f"   Successful requests: {successful_requests}/5")
        print(f"   Rate limit errors: {rate_limit_errors}")
        print(f"   Observed rate: {requests_per_second:.2f} requests/second")
        print(f"   Documented limit: 3 requests/second")

        return (requests_per_second, rate_limit_errors > 0)

    except Exception as e:
        print(f"   ❌ Rate limit test failed: {e}")
        return (0, False)

def main():
    """Main test function."""
    print("=" * 60)
    print("Notion Write Test (T007)")
    print("=" * 60)

    # Check environment variables
    check_env_vars()
    print("\n✅ All environment variables found")

    # Initialize Notion client
    print("\n🔌 Connecting to Notion API...")
    try:
        notion = Client(auth=NOTION_API_KEY)
        print("✅ Connected to Notion API")
    except Exception as e:
        print(f"❌ Failed to connect to Notion API: {e}")
        sys.exit(1)

    # Run tests
    company_ids = create_test_companies(notion)

    if not company_ids:
        print("\n❌ No companies were created. Cannot proceed with tests.")
        sys.exit(1)

    test1_pass = test_create_collabiq_entry(notion, company_ids)
    test2_pass = test_relation_linking(notion, company_ids)
    rate, rate_limit_hit = test_api_rate_limits(notion)

    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print(f"Test 1 (Create entry with all fields): {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"Test 2 (Relation linking): {'✅ PASS' if test2_pass else '❌ FAIL'}")
    print(f"Test 3 (API rate limits): {rate:.2f} req/s, Rate limit hit: {'Yes' if rate_limit_hit else 'No'}")

    if test1_pass and test2_pass:
        print("\n✅ All tests passed!")
        print("\nNext step: Update research-template.md Section 2.4 with test results")
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)

    print("=" * 60)

if __name__ == "__main__":
    main()
