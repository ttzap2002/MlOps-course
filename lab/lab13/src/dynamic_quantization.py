from openai import OpenAI
import time


def get_llm_response(client: OpenAI, prompt: str) -> str:
    chat_response = client.chat.completions.create(
        model="",  # use the default server model
        messages=[
            {"role": "developer", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_completion_tokens=150,
        # turn off thinking for Qwen with /no_think
        extra_body={"chat_template_kwargs": {"enable_thinking": False}}
    )
    content = chat_response.choices[0].message.content.strip()
    return content

if __name__ == "__main__":
    print("XD")
    client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

    prompts = [
        "How many legs does a dog have?",
        "1+1=?",
        "What is a capital of Poland",
        "What is DevOps?",
        "Who are you?",
        "Explain the concept of 'quantization' in 50 words.",
        "List top 5 popular programming languages.",
        "List 5 advantages of using Docker for LLM deployment",
        "Solve this: If I have 3 apples and you give me 5 more, how many do I have?",
        "12 + 4 + 7 =?"
    ]

    start_time = time.perf_counter()

    for prompt in prompts:
        print("Question:", prompt)
        print(f"Answer: {get_llm_response(client, prompt)}")

    end_time = time.perf_counter()

    total_serving_time = end_time - start_time
    print(f"Total serving time: {total_serving_time}")

