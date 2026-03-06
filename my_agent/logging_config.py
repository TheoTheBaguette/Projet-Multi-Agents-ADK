"""
Configuration du système de logging pour le Chef Cuisinier
"""

import logging
import json
from datetime import datetime
from pathlib import Path


class StructuredLogger:
    
    def __init__(self, name="chef_cuisinier"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Créer le dossier logs s'il n'existe pas
        Path("logs").mkdir(exist_ok=True)
        
        # Éviter les duplications
        if self.logger.handlers:
            return
        
        # Handler JSON (pour analyse)
        json_handler = logging.FileHandler("logs/agent_activity.json", encoding='utf-8')
        json_handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(json_handler)
        
        # Handler console (pour debug)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(' [%(levelname)s] %(message)s'))
        self.logger.addHandler(console_handler)
    
    def log_agent_start(self, agent_name, message=""):
        """Log le démarrage d'un agent"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event": "agent_start",
            "agent": agent_name,
            "user_message": message[:200] if message else ""
        }
        self.logger.info(json.dumps(log_data, ensure_ascii=False))
    
    def log_tool_execution(self, tool_name, args=None, result="", duration=0):
        """Log l'exécution d'un outil"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event": "tool_execution",
            "tool": tool_name,
            "args": str(args)[:200] if args else "",
            "result_preview": str(result)[:200] if result else "",
            "duration_ms": duration
        }
        self.logger.info(json.dumps(log_data, ensure_ascii=False))


# Instance globale du logger
agent_logger = StructuredLogger()

