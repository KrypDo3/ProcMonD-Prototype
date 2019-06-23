class Alert:
    """
    The Alert class encapsulates the metadata for a suspicious event.
    """
    message: str
    path: str
    name: str
    pid: int

    def __init__(self, pid=0, name="", path="", message=""):
        """
        Creates a new Alert object that represents a detected suspicious event.
        :param pid: The ID of the suspicious process.
        :param name: The name of the process, as it appears in ps.
        :param path: The path on disk of the process's executable file.
        :param message: The alert message explaining the suspicious activity.
        """
        self.pid = pid
        self.name = name
        self.path = path
        self.message = message

    def __str__(self):
        return f"{self.name}({self.pid}) {self.message}"
