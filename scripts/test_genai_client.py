import os
import pprint

try:
    from google import genai
except Exception as e:
    print('import error:', e)
    raise

key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
print('Using API key present?', bool(key))

client = None
try:
    client = genai.Client(api_key=key)
    print('Created client:', type(client))
except Exception as e:
    print('client creation failed:', e)

prompt = 'Return only a JSON array: [{"title":"TestIt","company":"X","summary":"S","url":"http://x"}]'
resp = None
try:
    resp = client.models.generate_content(model='gemini-2.5-flash-preview-09-2025', contents=prompt)
    print('\n=== resp repr ===')
    print(repr(resp)[:1000])
    print('\n=== Inspect common attrs ===')
    for attr in ('text','message','candidates','content'):
        print(attr, '->', getattr(resp, attr, None))
except Exception as e:
    print('generate_content failed:', e)
    raise

print('\n=== Done ===')
