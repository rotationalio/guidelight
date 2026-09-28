from dotenv import load_dotenv

load_dotenv()

import guidelight as gdl

client = gdl.client(timeout=(10, 300))

# List all agents
print("Existing agents:")
print(client.get("agents", query={"page_size": 10}))


# execute a deployed task
context = """Which is best for kids with glasses?"""

result = client.execute("health-plan-decision-support", "input-guardrail", context=context)

print(result)