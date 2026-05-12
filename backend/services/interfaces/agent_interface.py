class AgentInterface:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    def send_message(self, message: str) -> None:
        raise NotImplementedError(
            "send_message method must be implemented by subclasses"
        )

    def receive_message(self) -> str:
        raise NotImplementedError(
            "receive_message method must be implemented by subclasses"
        )
