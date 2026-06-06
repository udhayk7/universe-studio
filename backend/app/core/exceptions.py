class NotFoundError(Exception):
    def __init__(self, resource: str, resource_id: object) -> None:
        super().__init__(f"{resource} not found: {resource_id}")
        self.resource = resource
        self.resource_id = resource_id
