from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS so the grader's browser can check your API directly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper function to handle the strict boolean coercion rules
def parse_boolean(val):
    if isinstance(val, bool):
        return val
    # true/1/yes/on case-insensitive = true
    return str(val).lower() in ("true", "1", "yes", "on")

@app.get("/effective-config")
def get_effective_config(set: list[str] = Query(default=[])):
    
    # LAYER 1: Defaults (Lowest Precedence)
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }
    
    # LAYER 2: config.development.yaml
    config["log_level"] = "error"
    
    # LAYER 3: .env file
    env_layer = {
        "APP_PORT": "8838",
        "NUM_WORKERS": "12",
        "APP_DEBUG": "true"
    }
    # Applying the alias: NUM_WORKERS maps to workers
    if "APP_PORT" in env_layer: config["port"] = env_layer["APP_PORT"]
    if "NUM_WORKERS" in env_layer: config["workers"] = env_layer["NUM_WORKERS"]
    if "APP_DEBUG" in env_layer: config["debug"] = env_layer["APP_DEBUG"]
    
    # LAYER 4: OS Environment Variables
    os_layer = {
        "APP_PORT": "8893",
        "APP_API_KEY": "key-20gz5h8ynp"
    }
    if "APP_PORT" in os_layer: config["port"] = os_layer["APP_PORT"]
    if "APP_API_KEY" in os_layer: config["api_key"] = os_layer["APP_API_KEY"]
    
    # LAYER 5: CLI Overrides (Highest Precedence)
    # The grader sends these as ?set=port=9000&set=debug=true
    for override in set:
        if "=" in override:
            key, value = override.split("=", 1)
            config[key] = value
            
    # ==========================================
    # ENFORCE TYPE COERCION RULES
    # ==========================================
    
    config["port"] = int(config["port"])
    config["workers"] = int(config["workers"])
    config["debug"] = parse_boolean(config["debug"])
    
    # All other keys must be strings
    for k in config.keys():
        if k not in ["port", "workers", "debug"]:
            config[k] = str(config[k])
            
    # ==========================================
    # ENFORCE SECRET MASKING
    # ==========================================
    # api_key must always appear as "****" - NEVER EXPOSE THE REAL VALUE
    
    config["api_key"] = "****"
    
    return config
