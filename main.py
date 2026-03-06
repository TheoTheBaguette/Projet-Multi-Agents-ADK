"""
Runner programmatique pour le système Chef Cuisinier
Contrainte 7 du TP : instancie Runner + InMemorySessionService
"""

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from my_agent.agent import root_agent


def main():
    print("Chef Cuisinier Virtuel - Système Multi-Agents")
    
    # Instanciation Runner + InMemorySessionService (contrainte 7)
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="chef_cuisinier",
        agent=root_agent,
        session_service=session_service
    )
    
    # Création session
    session_id = "user_session_001"
    user_id = "user_001"
    session_service.create_session_sync(
        app_name="chef_cuisinier",
        user_id=user_id,
        session_id=session_id
    )
    
    # Boucle d'interaction
    try:
        while True:
            user_input = input("Vous: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Au revoir!")
                break
            
            if not user_input:
                continue
            
            print("Chef: ", end="", flush=True)
            
            try:
                message = types.Content(
                    role="user",
                    parts=[types.Part(text=user_input)]
                )
                
                events = runner.run(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=message
                )
                
                for event in events:
                    if hasattr(event, 'content') and hasattr(event.content, 'parts'):
                        for part in event.content.parts:
                            if hasattr(part, 'text'):
                                print(part.text, end="", flush=True)
                
                print("\n")
                
            except Exception as e:
                print(f"Erreur: {e}\n")
    
    except KeyboardInterrupt:
        print("\nFin du runner")


if __name__ == "__main__":
    main()
