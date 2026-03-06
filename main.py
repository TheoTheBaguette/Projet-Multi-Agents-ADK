import asyncio
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from my_agent.agent import root_agent


async def main_async():
    print("Chef Cuisinier Virtuel - Système Multi-Agents")

    
    # Instanciation Runner + InMemorySessionService 
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="chef_cuisinier",
        agent=root_agent,
        session_service=session_service
    )
    
    # Création session
    session_id = "user_session_001"
    user_id = "user_001"
    
    try:
        await session_service.create_session(
            app_name="chef_cuisinier",
            user_id=user_id,
            session_id=session_id
        )
    except Exception:
        pass  # Session existe déjà
    
    # Boucle d'interaction
    try:
        while True:
            user_input = input("Vous: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nAu revoir!")
                break
            
            if not user_input:
                continue
            
            print("Chef: ", end="", flush=True)
            
            try:
                message = types.Content(
                    role="user",
                    parts=[types.Part(text=user_input)]
                )
                
                async for event in runner.run_async(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=message
                ):
                    if hasattr(event, 'content') and hasattr(event.content, 'parts'):
                        for part in event.content.parts:
                            if hasattr(part, 'text'):
                                print(part.text, end="", flush=True)
                
                print("\n")
                
            except Exception as e:
                print(f"\nErreur: {e}\n")
    
    except KeyboardInterrupt:
        print("\n\nFin du runner (Ctrl+C)")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
