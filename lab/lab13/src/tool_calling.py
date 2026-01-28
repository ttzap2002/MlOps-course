import datetime
import json
import polars as pl
from typing import Callable


from openai import OpenAI


def make_llm_request(prompt: str) -> str:
    client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

    messages = [
        {"role": "developer", "content": "You are a professional data analysis assistant."},
        {"role": "user", "content": prompt},
    ]

    tool_definitions, tool_name_to_func = get_tool_definitions()

    # guard: loop limit, we break as soon as we get an answer
    for _ in range(10):
        response = client.chat.completions.create(
            model="",
            messages=messages,
            tools=tool_definitions,  # always pass all tools in this example
            tool_choice="auto",
            max_completion_tokens=1000,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        resp_message = response.choices[0].message
        messages.append(resp_message.model_dump())

        print(f"Generated message: {resp_message.model_dump()}")
        print()

        # parse possible tool calls (assume only "function" tools)
        if resp_message.tool_calls:
            for tool_call in resp_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                # call tool, serialize result, append to messages
                func = tool_name_to_func[func_name]
                func_result = func(**func_args)

                messages.append(
                    {
                        "role": "tool",
                        "content": json.dumps(func_result),
                        "tool_call_id": tool_call.id,
                    }
                )
        else:
            # no tool calls, we're done
            return resp_message.content

    # we should not get here
    last_response = resp_message.content
    return f"Could not resolve request, last response: {last_response}"


def get_tool_definitions() -> tuple[list[dict], dict[str, Callable]]:
    tool_definitions = [
        {
            "type": "function",
            "function": {
                "name": "read_remote_csv",
                "description": "Reads a CSV file from a generic URL and returns the first few rows as text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The public URL to the CSV file."
                        }
                    },
                    "required": ["url"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_remote_parquet",
                "description": "Reads a Parquet file from a generic URL and returns the first few rows as text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The public URL to the Parquet file."
                        }
                    },
                    "required": ["url"],
                },
            },
        },
    ]

    tool_name_to_callable = {
        "read_remote_csv": read_remote_csv_tool,
        "read_remote_parquet": read_remote_parquet_tool,
    }

    return tool_definitions, tool_name_to_callable


def read_remote_csv_tool(url: str, num_of_rows = 10) -> str:
    try:
        df = pl.read_csv(url)
        return str(df.head(num_of_rows))
    except Exception as e:
        return f"Error with reading csv from {url}: {str(e)}"

def read_remote_parquet_tool(url: str, num_of_rows = 10) -> str:
    try:
        df = pl.read_parquet(url)
        return str(df.head(num_of_rows))
    except Exception as e:
        return f"Error reading parquet from {url}: {str(e)}"


if __name__ == "__main__":
    yellow_taxi_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-02.parquet"
    prompt = f"Please analyze this dataset {yellow_taxi_url}. What can you say about this dataset?"
    response = make_llm_request(prompt)
    print("Response:\n", response)

    apistox_csv = "https://raw.githubusercontent.com/j-adamczyk/ApisTox_dataset/blob/master/outputs/dataset_final.csv"
    prompt = f"Please analyze this dataset {apistox_csv}. What can you say about this dataset?"
    response = make_llm_request(prompt)
    print("Response:\n", response)
