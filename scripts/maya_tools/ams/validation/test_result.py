from typing import Callable


class TestResult:
    def __init__(self):
        self.failure_list = []
        self.fix_script: Optional[Callable] = None

    def add_failure(self, message: str):
        """
        Append the list of failure messages
        :param message:
        """
        self.failure_list.append(message)

    def set_fix_script(self, fix_script: Callable):
        """
        Set the fix script to the appropriate function
        :param fix_script:
        """
        self.fix_script = fix_script

    def run_fix_script(self):
        """
        Call the fix script
        """
        if self.fix_script:
            self.fix_script()

    @property
    def passed(self) -> bool:
        return len(self.failure_list) == 0
