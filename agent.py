import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from tools import load_data, get_sales_summary, get_revenue_by_region, get_top_products, get_category_performance

# Load environment variables and create Gemini client
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Load the dataset once so every tool can use it
df = load_data()

# Map each tool name to a lambda that calls the real function with the dataframe
TOOL_FUNCTIONS = {
    "get_sales_summary": lambda: get_sales_summary(df),
    "get_revenue_by_region": lambda: get_revenue_by_region(df),
    "get_top_products": lambda n=5: get_top_products(df, n=int(n)),
    "get_category_performance": lambda: get_category_performance(df),
}

# Tell Gemini what role it plays and what data it has access to
SYSTEM_PROMPT = (
    "You are an AI business intelligence agent for an e-commerce company. "
    "You have access to tools that analyze real sales data with 3,500 orders "
    "across multiple products, categories, and regions from 2022-2024. "
    "When a user asks a business question, use the appropriate tool to get "
    "real data, then provide a clear, actionable answer based on the results. "
    "Always cite specific numbers from the data. If the question cannot be "
    "answered with the available tools, say so honestly."
)
# Each declaration tells Gemini a tool's name, purpose, and parameters
tool_declarations = [
    {
        "name": "get_sales_summary",
        "description": "Get an overall summary of sales performance including total orders, revenue, profit, average order value, and profit margin.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_revenue_by_region",
        "description": "Get revenue, profit, and order count broken down by geographic region (North, South, East, West).",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_top_products",
        "description": "Get the top N best-selling products ranked by total revenue.",
        "parameters": {
            "type": "object",
            "properties": {
                "n": {
                    "type": "integer",
                    "description": "Number of top products to return. Defaults to 5.",
                },
            },
        },
    },
    {
        "name": "get_category_performance",
        "description": "Get performance metrics for each product category (Electronics, Accessories, Office) including revenue, profit, margin, and average quantity per order.",
        "parameters": {"type": "object", "properties": {}},
    },
]
def ask_agent(question):
    """Send a question to the agent and return the response with tool call info."""
    # Package the tool declarations and system prompt into a config
    tools = types.Tool(function_declarations=tool_declarations)
    config = types.GenerateContentConfig(
        tools=[tools],
        system_instruction=SYSTEM_PROMPT,
    )

    # Send the user's question to Gemini
    contents = [question]
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=contents,
        config=config,
    )

    # Extract the first part of the response
    part = response.candidates[0].content.parts[0]
    tool_info = None

    # If Gemini wants to call a tool, execute it and send the result back
    if part.function_call:
        fc = part.function_call
        func_name = fc.name
        func_args = dict(fc.args) if fc.args else {}

        tool_info = {"name": func_name, "args": func_args}
        print(f"  [Agent chose tool: {func_name}({func_args})]")

        # Look up and execute the matching Python function
        if func_name in TOOL_FUNCTIONS:
            result = TOOL_FUNCTIONS[func_name](**func_args)
        else:
            result = f"Error: Unknown tool '{func_name}'"

        # Send the tool result back to Gemini for a final natural language answer
        contents.append(response.candidates[0].content)
                # NEW CODE (Use this):
        fn_response_part = types.Part(
            function_response=types.FunctionResponse(
                id=fc.id,
                name=fc.name,
                response={"result": result},
            )
        )
        contents.append(types.Content(role="user", parts=[fn_response_part]))

        final_response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents,
            config=config,
        )
        answer = final_response.text
    else:
        answer = part.text

    return answer, tool_info
if __name__ == "__main__":
    print("E-Commerce Business Intelligence Agent")
    print("Type 'quit' to exit.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue

        answer, tool_info = ask_agent(question)
        print(f"\nAgent: {answer}\n")    