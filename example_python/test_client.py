from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult

async def basic_elicitation_handler(message: str, response_type: type, params, context):
    print(f"Server asks: {message}")
    print(f"Expected response type: {response_type}")
    
    # Handle different response types generically
    if response_type is None:
        # No response expected, just approval/decline
        user_input = input("Accept? (y/n): ").lower()
        if user_input in ['y', 'yes']:
            return ElicitResult(action="accept", content=None)
        elif user_input in ['n', 'no']:
            return ElicitResult(action="decline")
        else:
            return ElicitResult(action="cancel")
    
    # Check if it's a structured type (has fields)
    if hasattr(response_type, '__dataclass_fields__'):
        print("This requires structured input:")
        field_values = {}
        for field_name, field in response_type.__dataclass_fields__.items():
            field_type = field.type
            prompt = f"Enter {field_name} ({field_type.__name__}): "
            user_input = input(prompt)
            
            if not user_input:
                return ElicitResult(action="decline")
            
            # Basic type conversion
            try:
                if field_type == int:
                    field_values[field_name] = int(user_input)
                elif field_type == float:
                    field_values[field_name] = float(user_input)
                elif field_type == bool:
                    field_values[field_name] = user_input.lower() in ['true', 'yes', '1', 'y']
                else:
                    field_values[field_name] = user_input
            except ValueError:
                print(f"Invalid input for {field_name}")
                return ElicitResult(action="decline")
        
        # Create the structured response
        return response_type(**field_values)
    
    # Handle simple scalar types
    user_response = input("Your response: ")
    if not user_response:
        return ElicitResult(action="decline")
    
    # For scalar types, FastMCP wraps them in an object with a 'value' field
    return response_type(value=user_response)

client = Client(
    "server.py", 
    elicitation_handler=basic_elicitation_handler
)

async def main():
    async with client:
        result = await client.call_tool("some_tool_that_needs_secrets", {})
        print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())