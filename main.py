import json
import time
import random
import ast
import warnings
import re

# --- CONFIGURATION ---
# Change these filenames to match whatever file you want to test
CHAT_FILE_NAME = 'sample-chat-conversation-01.json'
CONTEXT_FILE_NAME = 'sample_context_vectors-01.json'

# Suppress warnings to keep output clean
warnings.filterwarnings("ignore")

class MockLLMEvaluator:
    def __init__(self):
        # We simulate using a model to avoid API costs
        self.model = "gpt-4o-mini"

    def calculate_cost(self, prompt_text, response_text):
        """Estimates cost based on character count (Approx 4 chars = 1 token)."""
        input_tokens = len(str(prompt_text)) / 4
        output_tokens = len(str(response_text)) / 4
        # Pricing: $0.15 per 1M input, $0.60 per 1M output
        return ((input_tokens / 1_000_000) * 0.15) + ((output_tokens / 1_000_000) * 0.60)

    def evaluate_response(self, query, context, response):
        """Simulates the evaluation process."""
        start_time = time.time()
        
        # 1. Simulate Latency (Network delay)
        time.sleep(random.uniform(0.1, 0.5)) 
        
        # 2. Mock Logic (In real life, an LLM generates this)
        mock_evaluation = {
            "relevance_score": 0.85, 
            "hallucination_score": 0.95,
            "reasoning": "The response aligns well with the provided context. (Mock Evaluation)"
        }
        
        end_time = time.time()
        latency = end_time - start_time
        
        # 3. Calculate Cost
        dummy_prompt = f"{query} {context}"
        dummy_response = json.dumps(mock_evaluation)
        cost = self.calculate_cost(dummy_prompt, dummy_response)
        
        return {
            "metrics": mock_evaluation,
            "performance": {
                "latency_seconds": round(latency, 4),
                "cost_usd": f"${cost:.8f}"
            }
        }

def load_robust_json(filename):
    """
    Tries to load JSON normally. If it fails (syntax errors),
    it switches to a Regex Scraper to extract raw text.
    """
    print(f"📂 Loading {filename}...")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Strategy 1: Standard JSON (Try to clean comments first)
        try:
            clean_lines = [line for line in content.splitlines() if not line.strip().startswith("//")]
            return json.loads("\n".join(clean_lines))
        except:
            pass

        # Strategy 2: Regex Scraper (The "Nuclear Option" for broken files)
        print(f"   ⚠️ Syntax error detected. Switching to 'Regex Scraper' to extract raw text...")
        
        extracted_data = []
        # Regex patterns to find keys like "message": "..."
        patterns = [
            r'"(user_query|message|query|text|response|bot_response)":\s*"((?:[^"\\]|\\.)*)"',
            r"'(user_query|message|query|text|response|bot_response)':\s*'((?:[^'\\]|\\.)*)'"
        ]
        
        found_items = []
        for p in patterns:
            found_items.extend(re.findall(p, content))

        for key, value in found_items:
            clean_val = value.encode('utf-8').decode('unicode_escape')
            # Ignore short numeric IDs (fixes issues where IDs are mistaken for queries)
            if len(clean_val) < 2 or clean_val.isdigit():
                continue
            extracted_data.append({key: clean_val})
            
        if not extracted_data:
            print(f"   ❌ Regex failed to find any data in {filename}")
            return []
            
        print(f"   ✅ Regex Scraper found {len(extracted_data)} fragments!")
        return extracted_data

    except Exception as e:
        print(f"❌ CRITICAL ERROR reading {filename}: {e}")
        return []

def extract_list_from_data(data):
    """
    Intelligently finds the list of items whether it's a list, 
    a dict with a 'conversation_turns' key, or a dict with 'data'.
    """
    if isinstance(data, list):
        return data
    
    if isinstance(data, dict):
        # Common keys used in these datasets
        possible_keys = ['conversation_turns', 'vector_data', 'data', 'chats', 'context']
        for key in possible_keys:
            if key in data and isinstance(data[key], list):
                return data[key]
        
        # If the dict itself is a single item wrapper
        if 'message' in data or 'text' in data:
            return [data]
            
    return []

# --- Main Execution ---
if __name__ == "__main__":
    print(f"🚀 Starting Evaluation Pipeline...\n")
    
    # Load Data
    chats_data = load_robust_json(CHAT_FILE_NAME)
    contexts_data = load_robust_json(CONTEXT_FILE_NAME)
    
    if chats_data is not None and contexts_data is not None:
        evaluator = MockLLMEvaluator()

        # Unpack lists correctly
        chat_list = extract_list_from_data(chats_data)
        context_list = extract_list_from_data(contexts_data)
        
        # Fallback if regex returned a flat list
        if not chat_list and isinstance(chats_data, list): chat_list = chats_data
        if not context_list and isinstance(contexts_data, list): context_list = contexts_data

        # Process the available pairs
        limit = min(len(chat_list), len(context_list))
        print(f"\nProcessing {limit} valid pairs...")
        
        for i in range(limit):
            chat = chat_list[i]
            ctx = context_list[i]
            
            # --- Smart Key Search ---
            query = None
            response = None
            
            # 1. Find Query/Response in Chat Object
            for k, v in chat.items():
                if k in ['user_query', 'message', 'query', 'text'] and not query: 
                    # Filter out "AI" roles to focus on User Queries
                    if chat.get('role') != 'AI/Chatbot':
                        query = v
                if k in ['bot_response', 'response', 'answer'] and not response: response = v
            
            # Fallback for simple dicts
            if not query and 'message' in chat: query = chat['message']

            # 2. Find Context Text
            context_text = "Context Not Found"
            if isinstance(ctx, dict):
                for k, v in ctx.items():
                     if k in ['text', 'context', 'chunks']: context_text = str(v)
            else:
                context_text = str(ctx)

            # 3. Evaluate (Only if we found a valid query > 5 chars)
            if query and len(str(query)) > 5:
                print(f"--- 📝 Evaluating Conversation {i+1} ---")
                print(f"Query: {str(query)[:100]}...") 
                
                if not response: response = "Generated Response"
                
                result = evaluator.evaluate_response(
                    query=query,
                    context=context_text,
                    response=str(response)
                )
                
                print("Result:")
                print(json.dumps(result, indent=2))
                print("-" * 50 + "\n")
    else:
        print("\n❌ Could not load data.")