import os
import streamlit as st
from google import genai
from google.genai import types
from tools import load_data, get_sales_summary, get_revenue_by_region, get_top_products, get_category_performance

# Configure the Streamlit page
st.set_page_config(page_title="E-Commerce BI Agent", page_icon="📊", layout="wide")

# Load API key from environment variable or Streamlit secrets
api_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("Please set your GOOGLE_API_KEY in .env or Streamlit secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# Cache data so it only loads once per session
@st.cache_data
def get_data():
    return load_data()

df = get_data()

# Map tool names to their Python functions
TOOL_FUNCTIONS = {
    "get_sales_summary": lambda: get_sales_summary(df),
    "get_revenue_by_region": lambda: get_revenue_by_region(df),
    "get_top_products": lambda n=5: get_top_products(df, n=int(n)),
    "get_category_performance": lambda: get_category_performance(df),
}
tool_declarations = [  # Declare the tools Gemini can choose from
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
SYSTEM_PROMPT = (
    "You are an AI business intelligence agent for an e-commerce company. "
    "You have access to tools that analyze real sales data with 3,500 orders "
    "across multiple products, categories, and regions from 2022-2024. "
    "When a user asks a business question, use the appropriate tool to get "
    "real data, then provide a clear, actionable answer based on the results. "
    "Always cite specific numbers from the data. If the question cannot be "
    "answered with the available tools, say so honestly."
)

# Display the app title and description
st.title("📊 E-Commerce Business Intelligence Agent")
st.markdown(
    "Ask any business question about the e-commerce dataset. "
    "The AI agent will autonomously choose the right analysis tool and return data-backed insights."
)

# Show dataset stats in the sidebar (Updated 'Sales Amount' to 'Sales' for your dataset)
with st.sidebar:
    st.header("About the Dataset")
    st.metric("Total Orders", f"{len(df):,}")
    st.metric("Total Revenue", f"${df['Sales'].sum():,.0f}")
    st.metric("Total Profit", f"${df['Profit'].sum():,.0f}")
    st.markdown("---")
    st.markdown("**Categories:** Electronics, Accessories, Office")
    st.markdown("**Regions:** North, South, East, West")
    st.markdown("**Period:** 2022-2024")
# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Replay previous messages on page rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle new user input
if prompt := st.chat_input("Ask a business question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            tools = types.Tool(function_declarations=tool_declarations)
            config = types.GenerateContentConfig(
                tools=[tools],
                system_instruction=SYSTEM_PROMPT,
            )
            contents = [prompt]
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=contents,
                config=config,
            )
            part = response.candidates[0].content.parts[0] 
                        # Check if Gemini wants to call a tool
            if part.function_call:
                fc = part.function_call
                func_name = fc.name
                func_args = dict(fc.args) if fc.args else {}
                st.caption(f"🔧 Agent called: `{func_name}({func_args})`")
                # Execute the tool and get results
                if func_name in TOOL_FUNCTIONS:
                    result = TOOL_FUNCTIONS[func_name](**func_args)
                else:
                    result = f"Error: Unknown tool '{func_name}'"
                # Send the tool result back to Gemini for a final answer
                contents.append(response.candidates[0].content)
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
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})   