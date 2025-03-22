import os

class DirectoryManager:
    def __init__(self):
        self.directories = {
            "home": os.path.expanduser("~"),
            "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
            "documents": os.path.join(os.path.expanduser("~"), "Documents"),
            "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
            # Add more default directories as needed
        }

    def get_directory(self, key):
        return self.directories.get(key, "")

    def add_directory(self, key, path):
        if os.path.exists(path):
            self.directories[key] = path
        else:
            raise ValueError(f"The path {path} does not exist.")

    def get_all_directories(self):
        return "\n".join([f"{k}: {v}" for k, v in self.directories.items()])

directory_manager = DirectoryManager()

# Example of adding a custom directory
#try:
#    directory_manager.add_directory("test", os.path.join(directory_manager.get_directory("documents"), "Test"))
#except ValueError as e:
#    print(f"Note: {e}")