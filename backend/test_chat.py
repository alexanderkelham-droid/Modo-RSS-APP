"""Quick test of chat endpoint."""
import asyncio
import httpx


async def test_chat():
    url = "https://modo-rss-app-production.up.railway.app/chat"
    
    questions = [
        "What is the energy news in Germany?",
        "tell me about hecate energy",
    ]
    
    for question in questions:
        payload = {
            "question": question,
            "k": 8
        }
        
        print(f"\n{'='*60}")
        print(f"Question: {payload['question']}")
        print('='*60)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"\nAnswer: {data.get('answer')[:200]}...")
                    print(f"\nConfidence: {data.get('confidence')}")
                    if data.get('citations'):
                        print(f"Citations: {len(data['citations'])} sources")
                else:
                    print(f"Error: {response.text}")
        except Exception as e:
            print(f"Exception: {e}")


if __name__ == "__main__":
    asyncio.run(test_chat())
