"""
AI Configuration File
=====================

Configure your AI provider by setting the environment variables or modifying the values below.

Supported Providers:
1. "openai" - OpenAI GPT models (requires OPENAI_API_KEY)
2. "aws" - AWS-hosted custom models (requires AWS_AI_ENDPOINT and AWS_AI_API_KEY)
3. "local" - Local/self-hosted models (Ollama, custom endpoints)

To switch providers, change the AI_PROVIDER environment variable or modify the default below.
"""

import os

# Primary Configuration
AI_PROVIDER = os.environ.get("AI_PROVIDER", "openai")  # Change this to switch providers

# OpenAI Configuration
OPENAI_CONFIG = {
    "api_key": os.environ.get("OPENAI_API_KEY", "your-openai-api-key-here"),
    "default_model": "gpt-4o-mini",  # Most cost-effective GPT-4 model
    "max_tokens": 1000,
    "temperature": 0.7
}

# AWS Configuration
AWS_CONFIG = {
    "endpoint": os.environ.get("AWS_AI_ENDPOINT", "https://your-aws-sagemaker-endpoint.amazonaws.com"),
    "api_key": os.environ.get("AWS_AI_API_KEY", "your-aws-api-key-here"),
    "region": os.environ.get("AWS_REGION", "us-east-1"),
    "default_model": "custom-finetuned-model",
    "max_tokens": 1000,
    "temperature": 0.7
}

# Local Configuration
LOCAL_CONFIG = {
    "endpoint": os.environ.get("LOCAL_AI_ENDPOINT", "http://localhost:11434"),  # Ollama default
    "default_model": os.environ.get("LOCAL_AI_MODEL", "llama2"),  # Can be llama2, codellama, mistral, etc.
    "max_tokens": 1000,
    "temperature": 0.7,
    "timeout": 30
}

# Demo Configuration (fallback when no AI service is available)
DEMO_CONFIG = {
    "enabled": True,
    "responses_per_subject": {
        "mathematics": [
            "Great question about math! Let me break this down step by step. In mathematics, it's important to understand the underlying concepts before moving to complex problems.",
            "I can help you with that math problem! Let's start with the basics and work our way up to more advanced concepts.",
            "Mathematics is all about patterns and logical thinking. Let me help you see the pattern in this problem.",
            "Excellent mathematical thinking! Problem-solving in math requires both logical reasoning and creative approaches."
        ],
        "science": [
            "Excellent science question! Scientific understanding comes from observation, hypothesis, and testing. Let me explain this concept clearly.",
            "Science is fascinating! This topic connects to many real-world applications. Let me show you how this works.",
            "Great scientific curiosity! Understanding the 'why' behind phenomena is key to scientific thinking.",
            "Wonderful inquiry! Science helps us understand the natural world through systematic investigation."
        ],
        "english": [
            "Wonderful question about language and literature! Effective communication involves understanding both structure and meaning.",
            "English literature offers rich insights into human experience. Let me help you analyze this text.",
            "Great observation about language! Writing and reading are powerful tools for expression and understanding.",
            "Excellent literary analysis! Understanding themes, characters, and context enriches our reading experience."
        ],
        "history": [
            "Interesting historical question! Understanding the past helps us make sense of the present and future.",
            "History is full of fascinating stories and important lessons. Let me provide some context for this topic.",
            "Excellent historical thinking! It's important to consider multiple perspectives when studying the past.",
            "Great historical inquiry! Learning from the past helps us understand how societies develop and change."
        ],
        "art": [
            "Wonderful artistic inquiry! Art is a powerful form of expression that reflects culture, emotion, and creativity.",
            "Great question about art! Creative expression takes many forms and serves many purposes in human society.",
            "Artistic exploration is exciting! Let me help you understand the techniques and meanings behind this work.",
            "Excellent artistic observation! Art allows us to express ideas and emotions that words alone cannot capture."
        ]
    }
}

# Setup Instructions for Each Provider
SETUP_INSTRUCTIONS = {
    "openai": {
        "title": "OpenAI Setup",
        "steps": [
            "1. Go to https://platform.openai.com/api-keys",
            "2. Sign in to your OpenAI account",
            "3. Create a new API key",
            "4. Set the OPENAI_API_KEY environment variable",
            "5. Or update the api_key in OPENAI_CONFIG above"
        ],
        "environment_variables": ["OPENAI_API_KEY"]
    },
    "aws": {
        "title": "AWS Setup",
        "steps": [
            "1. Deploy your model to AWS SageMaker or Bedrock",
            "2. Get your endpoint URL from AWS console",
            "3. Configure AWS credentials with appropriate permissions",
            "4. Set AWS_AI_ENDPOINT and AWS_AI_API_KEY environment variables",
            "5. Ensure your model endpoint accepts OpenAI-compatible format"
        ],
        "environment_variables": ["AWS_AI_ENDPOINT", "AWS_AI_API_KEY", "AWS_REGION"]
    },
    "local": {
        "title": "Local Model Setup",
        "steps": [
            "1. Install Ollama: https://ollama.ai/",
            "2. Pull a model: ollama pull llama2",
            "3. Start Ollama: ollama serve",
            "4. Or use custom endpoint with OpenAI-compatible API",
            "5. Update LOCAL_AI_ENDPOINT and LOCAL_AI_MODEL if needed"
        ],
        "environment_variables": ["LOCAL_AI_ENDPOINT", "LOCAL_AI_MODEL"]
    }
}

def get_current_config():
    """Get the configuration for the current AI provider"""
    provider = AI_PROVIDER.lower()
    
    if provider == "openai":
        return OPENAI_CONFIG
    elif provider == "aws":
        return AWS_CONFIG
    elif provider == "local":
        return LOCAL_CONFIG
    else:
        return LOCAL_CONFIG

def get_setup_instructions(provider=None):
    """Get setup instructions for a specific provider"""
    if provider is None:
        provider = AI_PROVIDER.lower()
    
    return SETUP_INSTRUCTIONS.get(provider, SETUP_INSTRUCTIONS["local"])

def validate_config(provider=None):
    """Validate configuration for the current or specified provider"""
    if provider is None:
        provider = AI_PROVIDER.lower()
    
    config = get_current_config()
    issues = []
    
    if provider == "openai":
        if not config["api_key"] or config["api_key"] == "your-openai-api-key-here":
            issues.append("OPENAI_API_KEY not set or using placeholder value")
    
    elif provider == "aws":
        if not config["endpoint"] or "your-aws" in config["endpoint"]:
            issues.append("AWS_AI_ENDPOINT not set or using placeholder value")
        if not config["api_key"] or config["api_key"] == "your-aws-api-key-here":
            issues.append("AWS_AI_API_KEY not set or using placeholder value")
    
    elif provider == "local":
        # Local provider is more forgiving, just warn about common issues
        if "localhost" in config["endpoint"]:
            issues.append("Using localhost endpoint - ensure local AI service is running")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "instructions": get_setup_instructions(provider)
    }

# Print current configuration on import
if __name__ == "__main__":
    print(f"Current AI Provider: {AI_PROVIDER}")
    print(f"Configuration: {get_current_config()}")
    validation = validate_config()
    if not validation["valid"]:
        print(f"Configuration issues: {validation['issues']}")
else:
    # Silent validation on import
    validation = validate_config()
    if not validation["valid"]:
        print(f"AI Config Warning - Current provider '{AI_PROVIDER}' has issues: {', '.join(validation['issues'])}")
        print("Check ai_config.py for setup instructions.")