import json
import time
import os
from datetime import datetime
from groq import Groq
import config

class LLMService:
    @classmethod
    def ask(cls, system_prompt: str, user_input: str, context: dict = None, system_prompt_name: str = "unknown") -> str:
        """
        Sends a query to the Groq API and logs the interaction.
        Retries up to config.MAX_RETRIES on failure.
        """
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set. Please define it in the .env file.")

        client = Groq(api_key=config.GROQ_API_KEY)
        
        # Build messages list
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        user_content = user_input
        if context:
            user_content += f"\n\nContext:\n{json.dumps(context, indent=2)}"
            
        messages.append({"role": "user", "content": user_content})
        
        # Prepare log directory
        os.makedirs("logs", exist_ok=True)
        log_path = os.path.join("logs", "llm_calls.log")
        
        # Perform request with retries
        last_error = None
        for attempt in range(1, config.MAX_RETRIES + 1):
            start_time = time.time()
            timestamp = datetime.utcnow().isoformat() + "Z"
            
            try:
                chat_completion = client.chat.completions.create(
                    messages=messages,
                    model=config.MODEL_NAME,
                    temperature=config.TEMPERATURE,
                )
                latency = time.time() - start_time
                response_text = chat_completion.choices[0].message.content
                
                # Log success
                log_entry = {
                    "timestamp": timestamp,
                    "system_prompt_name": system_prompt_name,
                    "input": {
                        "system_prompt": system_prompt,
                        "user_input": user_input,
                        "context": context
                    },
                    "output": response_text,
                    "model_used": config.MODEL_NAME,
                    "latency_seconds": latency,
                    "status": "success",
                    "attempt": attempt
                }
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
                
                return response_text
                
            except Exception as e:
                latency = time.time() - start_time
                last_error = e
                # Log attempt failure
                log_entry = {
                    "timestamp": timestamp,
                    "system_prompt_name": system_prompt_name,
                    "input": {
                        "system_prompt": system_prompt,
                        "user_input": user_input,
                        "context": context
                    },
                    "output": None,
                    "model_used": config.MODEL_NAME,
                    "latency_seconds": latency,
                    "status": "error",
                    "error_message": str(e),
                    "attempt": attempt
                }
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
                
                print(f"Error on LLM call attempt {attempt}/{config.MAX_RETRIES}: {e}")
                time.sleep(1) # wait briefly before retrying
                
        # If all retries failed, raise the exception
        raise last_error
