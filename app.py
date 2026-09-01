
import os
import json
import time  
import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
from google.genai.errors import APIError  
from tools import load_data, get_sales_summary, get_revenue_by_region, get_top_products, get_category_performance, generate_chart

# Configure the Streamlit page
st.set_page_config(page_title="E-Commerce BI Agent", page_icon="📊", layout="wide")

# --- MULTI-KEY ROTATION SYSTEM (QUOTE-PROOFED) ---
keys_string = os.environ.get("GOOGLE_API_KEYS") or st.secrets.get("GOOGLE_API_KEYS") or ""

API_KEYS = []
if keys_string:
    raw_keys = keys_string.split(",")
    for k in raw_keys:
        clean_k = k.strip().replace('"', '').replace("'", "")
        if clean_k:
            API_KEYS.append(clean_k)

# Fallback to single key if multi-key string isn't found
fallback_used = False
if not API_KEYS:
    single_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if single_key:
        clean_single = single_key.strip().replace('"', '').replace("'", "")
        if clean_single:
            API_KEYS = [clean_single]
            fallback_used = True

if not API_KEYS:
    st.error("Please configure GOOGLE_API_KEYS in your secrets or .env file.")
    st.stop()

if "current_key_index" not in st.session_state:
    st.session_state.current_key_index = 0

def get_active_client():
    """Instantiate a client using the currently active rotated key index."""
    active_key = API_KEYS[st.session_state.current_key_index]
    return genai.Client(api_key=active_key)

# Execution wrapper with automatic key rotation and 503 backoff
def generate_content_with_rotation(contents, config, model="gemini-3.6-flash", max_503_retries=3, delay_503=5):
    attempts = len(API_KEYS)
    
    for _ in range(attempts):
        try:
            client = get_active_client()
            
            # Inner loop to handle temporary 503 server overloads
            for attempt_503 in range(max_503_retries):
                try:
                    return client.models.generate_content(
                        model=model,
                        contents=contents,
                        config=config,
                    )
                except APIError as e:
                    if e.code == 503 and attempt_503 < max_503_retries - 1:
                        st.warning(f"⚠️ Google API servers are busy (503). Retrying in {delay_503} seconds... (Attempt {attempt_503+1}/{max_503_retries})")
                        time.sleep(delay_503)
                        continue
                    raise e
                    
        except APIError as e:
            err_str = str(e).lower()
            is_auth_error = "credential" in err_str or "auth" in err_str or "key" in err_str or e.code in [400, 401, 403]
            
            if e.code == 429 or is_auth_error:
                current_bad_index = st.session_state.current_key_index
                next_index = (current_bad_index + 1) % len(API_KEYS)
                st.session_state.current_key_index = next_index
                
                if is_auth_error:
                    st.warning(f"⚠️ Key #{current_bad_index + 1} has invalid credentials. Skipping and trying Key #{next_index + 1}...")
                else:
                    st.warning(f"⚠️ Key #{current_bad_index + 1} quota exceeded. Automatically rotating to Key #{next_index + 1}...")
                continue
            raise e
        except Exception as e:
            raise e
            
    st.error("❌ All configured API keys are either exhausted, invalid, or blocked. Please check your credentials!")
    st.stop()
# ---------------------------------

# Cache data so it only loads once per session
@st.cache_data
def get_data():
    return load_data()

df = get_data()

# Protect lambdas from hallucinated arguments using catch-all **kwargs
TOOL_FUNCTIONS = {
    "get_sales_summary": lambda *args, **kwargs: get_sales_summary(df),
    "get_revenue_by_region": lambda *args, **kwargs: get_revenue_by_region(df),
    "get_top_products": lambda *args, **kwargs: get_top_products(df, n=int(kwargs.get("n", 5))),
    "get_category_performance": lambda *args, **kwargs: get_category_performance(df),
    "generate_chart": lambda *args, **kwargs: generate_chart(
        df, 
        chart_type=kwargs.get("chart_type", "bar"), 
        data_source=kwargs.get("data_source", "region")
    ),
}

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
    {
        "name": "generate_chart",
        "description": "Generate a chart visualization from the sales data. Use this when the user asks to see a chart, graph, or visualization.",
        "parameters": {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "line"],
                    "description": "Type of chart. Use 'bar' for comparisons, 'line' for trends over time.",
                },
                "data_source": {
                    "type": "string",
                    "enum": ["region", "category", "monthly"],
                    "description": "What data to visualize. 'region' for regional breakdown, 'category' for category comparison, 'monthly' for sales over time.",
                },
            },
            "required": ["chart_type", "data_source"],
        },
    },
]

SYSTEM_PROMPT = (
    "You are an AI business intelligence agent for an e-commerce company. "
    "You have access to tools that analyze real sales data with 3,500 orders "
    "across multiple products, categories, and regions from 2022-2024. "
    "When a user asks a business question, use the appropriate tool to get "
    "real data, then provide a clear, actionable answer based on the results. "
    "Always cite specific numbers from the data. If the question cannot be "
    "answered with the available tools, say so honestly. "
    "When the user asks for a chart, graph, or visualization, use the generate_chart tool."
)

# Display the app title and description
st.title("📊 E-Commerce Business Intelligence Agent")
st.markdown(
    "Ask any business question about the e-commerce dataset. "
    "The AI agent will autonomously choose the right analysis tool and return data-backed insights."
)

# Show dataset stats and SECURE DIAGNOSTICS in the sidebar
with st.sidebar:
    st.header("About the Dataset")
    st.metric("Total Orders", f"{len(df):,}")
    st.metric("Total Revenue", f"${df['Sales'].sum():,.0f}")
    st.metric("Total Profit", f"${df['Profit'].sum():,.0f}")
    
    st.markdown("---")
    st.subheader("🔑 Secure API Key Diagnostic")
    st.write(f"**Keys Detected:** {len(API_KEYS)}")
    st.write(f"**Using Fallback Single Key?** {'Yes' if fallback_used else 'No'}")
    st.write(f"**Active Key Index:** #{st.session_state.current_key_index + 1}")
    
    for idx, key in enumerate(API_KEYS):
        if len(key) > 12:
            masked = f"{key[:8]}...{key[-4:]}"
        else:
            masked = "INVALID_LENGTH"
        st.write(f"Key #{idx+1}: `{masked}` (Chars: {len(key)})")
        
    st.markdown("---")
    st.markdown("**Categories:** Electronics, Accessories, Office")
    st.markdown("**Regions:** North, South, East, West")

# Initialize chat history pipelines in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_history" not in st.session_state:
    st.session_state.api_history = []

# Replay previous messages on page rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "chart_path" in message and message["chart_path"]:
            st.image(message["chart_path"])

# Helper function to extract text securely from any GenerateContentResponse
def extract_text_safely(response, fallback_text="Could not extract textual content from response."):
    if not response or not response.candidates:
        return fallback_text
    
    candidate = response.candidates[0]
    if not candidate.content or not candidate.content.parts:
        return fallback_text
        
    # Attempt to concatenate all text parts
    text_parts = [p.text for p in candidate.content.parts if p.text]
    if text_parts:
        return "".join(text_parts)
        
    return fallback_text

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
            
            # Re-verify and clean API history to prevent empty entries
            st.session_state.api_history = [
                item for item in st.session_state.api_history 
                if item.parts and (item.parts[0].text or item.parts[0].function_call or item.parts[0].function_response)
            ]
            
            # 1. Append the new user prompt directly to high-fidelity api_history
            user_content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )
            st.session_state.api_history.append(user_content)
            
            # Execute first call
            try:
                response = generate_content_with_rotation(
                    contents=st.session_state.api_history,
                    config=config,
                    model="gemini-3.6-flash"
                )
            except APIError as e:
                st.error(f"❌ Google API error: {e.message}. Please try again later!")
                st.stop()
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
                st.stop()
                
            part = response.candidates[0].content.parts[0]
            chart_path = None
            answer = None

            # Check if Gemini wants to call a tool
            if part.function_call:
                fc = part.function_call
                func_name = fc.name
                func_args = dict(fc.args) if fc.args else {}
                st.caption(f"🔧 Agent called: `{func_name}({func_args})`")
                
                # Execute the tool safely inside a try-except block
                try:
                    if func_name in TOOL_FUNCTIONS:
                        result = TOOL_FUNCTIONS[func_name](**func_args)
                    else:
                        result = f"Error: Unknown tool '{func_name}'"
                except Exception as tool_err:
                    st.error(f"❌ Failed to run tool '{func_name}': {str(tool_err)}")
                    st.stop()
                    
                # Detect chart results and prepare display
                if func_name == "generate_chart" and os.path.exists(str(result)):
                    chart_path = result
                    tool_result_text = f"Chart generated and saved to {result}"
                else:
                    if isinstance(result, pd.DataFrame):
                        tool_result_text = json.loads(result.to_json(orient="records", date_format="iso"))
                    elif isinstance(result, pd.Series):
                        tool_result_text = json.loads(result.to_json(date_format="iso"))
                    else:
                        tool_result_text = result
                    
                # Append the model's function call content to api_history
                model_fc_content = types.Content(
                    role="model",
                    parts=[part]
                )
                st.session_state.api_history.append(model_fc_content)
                
                # Append the tool's response content to api_history (using 'user' role for schema compatibility)
                fn_response_part = types.Part(
                    function_response=types.FunctionResponse(
                        id=fc.id,
                        name=fc.name,
                        response={"result": tool_result_text},
                    )
                )
                tool_content = types.Content(role="user", parts=[fn_response_part])
                st.session_state.api_history.append(tool_content)
                
                # Execute follow-up call
                try:
                    final_response = generate_content_with_rotation(
                        contents=st.session_state.api_history,
                        config=config,
                        model="gemini-3.6-flash"
                    )
                    # Use our secure text extractor!
                    extracted_text = extract_text_safely(final_response, fallback_text=None)
                    
                    if extracted_text is not None:
                        answer = extracted_text
                    else:
                        # ZERO-HISTORY FALLBACK: If the accumulated history call returns None,
                        # attempt a stateless execution using only the current prompt and the tool response
                        stateless_contents = [
                            types.Content(role="user", parts=[types.Part.from_text(text=f"Process this tool output: {tool_result_text}. User prompt was: {prompt}")]),
                        ]
                        fallback_response = generate_content_with_rotation(
                            contents=stateless_contents,
                            config=config,
                            model="gemini-3.6-flash"
                        )
                        answer = extract_text_safely(fallback_response, fallback_text="Could not summarize tool data due to temporary API limits.")
                except APIError as e:
                    st.error(f"❌ Google API error during summary: {e.message}. Please try again!")
                    st.stop()
                    
                # Append the final response content to api_history if successful
                if answer:
                    model_final_content = types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=answer)]
                    )
                    st.session_state.api_history.append(model_final_content)
            else:
                answer = extract_text_safely(response, fallback_text="No text response generated.")
                model_text_content = types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=answer)]
                )
                st.session_state.api_history.append(model_text_content)
                
            # If all else fails, do not allow None to render
            if answer is None:
                answer = "The API was unable to construct a summary response. Please try submitting your query again!"
                
            st.markdown(answer)
            if chart_path:
                st.image(chart_path)

    # Save details to session state messages for UI rendering
    st.session_state.messages.append({"role": "assistant", "content": answer, "chart_path": chart_path})