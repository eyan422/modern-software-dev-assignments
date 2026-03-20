import os
from dotenv import load_dotenv
from ollama import chat

load_dotenv()

NUM_RUNS_TIMES = 5

# TODO: Fill this in!
YOUR_SYSTEM_PROMPT = """Reverse the characters of a word by numbering each character, then reading the positions from last to first. Output ONLY the reversed word, nothing else.

User: cat
Positions: 1=c, 2=a, 3=t
Read backwards (3,2,1): t,a,c
Assistant: tac

User: python
Positions: 1=p, 2=y, 3=t, 4=h, 5=o, 6=n
Read backwards (6,5,4,3,2,1): n,o,h,t,y,p
Assistant: nohtyp

User: database
Positions: 1=d, 2=a, 3=t, 4=a, 5=b, 6=a, 7=s, 8=e
Read backwards (8,7,6,5,4,3,2,1): e,s,a,b,a,t,a,d
Assistant: esabatad

# User: httpstatus
# Positions: 1=h, 2=t, 3=t, 4=p, 5=s, 6=t, 7=a, 8=t, 9=u, 10=s
# Read backwards (10,9,8,7,6,5,4,3,2,1): s,u,t,a,t,s,p,t,t,h
# Assistant: sutatsptth

User: strawberry
Positions: 1=s, 2=t, 3=r, 4=a, 5=w, 6=b, 7=e, 8=r, 9=r, 10=y
Read backwards (10,9,8,7,6,5,4,3,2,1): y,r,r,e,b,w,a,r,t,s
Assistant: yrrebwarts
"""



USER_PROMPT = """
Reverse the order of letters in the following word. Only output the reversed word, no other text:

httpstatus
"""


EXPECTED_OUTPUT = "sutatsptth"

def test_your_prompt(system_prompt: str) -> bool:
    """Run the prompt up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT.

    Prints "SUCCESS" when a match is found.
    """
    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = chat(
            model="mistral-nemo:12b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": USER_PROMPT},
            ],
            options={"temperature": 0.5},
        )
        output_text = response.message.content.strip()
        if output_text.strip() == EXPECTED_OUTPUT.strip():
            print("SUCCESS")
            return True
        else:
            print(f"Expected output: {EXPECTED_OUTPUT}")
            print(f"Actual output: {output_text}")
    return False

if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)