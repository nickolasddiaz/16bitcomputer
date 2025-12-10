
class JumpManager:
    def __init__(self):
        self._counters = 0
        self._names: dict[int, str] = dict()  # key: id, value: name
        self._jumps: dict[str, int] = dict()  # key: name, value: position
        self._verify: set[str] = set()  # this checks if it has been used

    def get_jump(self) -> int:
        """
        returns a new jump value id
        """
        self._names[self._counters] = str(self._counters)
        self._jumps[str(self._counters)] = 0
        self._counters += 1
        return self._counters - 1

    def get_function(self, jump_name: str) -> int:
        """
        take input from a string/function name and creates a jump
        """
        key_found = next((key for key, val in self._names.items() if val == key), None)
        if key_found is not None:
            return key_found

        self._names[self._counters] = jump_name
        self._jumps[jump_name] = 0
        self._counters += 1
        return self._counters - 1

    def get_name(self, id_: int) -> str:
        """
        gets a string representation of a jump id
        """
        if self._names[id_].isdigit():
            return f".L{self._names[id_]}"
        else:
            return f".{self._names[id_]}"

    def get_jump_location_index(self, id_: int) -> int:
        """
        returns the jump location index, it is the index of the jump label
        """
        return self._jumps[self._names[id_]]

    def remove_duplicate(self, id1: int | None, id2: int | None = None) -> int:
        """
        if both are None it creates a new label
        else it combines the labels and return one label
        """
        match (id1 is None, id2 is None):
            case (True, True):
                return self.get_jump()
            case (False, True):
                return id1
            case (True, False):
                return id2
            case _:
                num_change = self._names[id1]
                num_to_change = self._names[id2]
                del self._jumps[self._names[id2]]
                for key, value in self._names.items():
                    if value == num_to_change:
                        self._names[key] = num_change
                return id1

    def set_pos(self, id_: int, pos: int):
        """
        sets the position of the jump label
        """
        if self._jumps[self._names[id_]] == 0:
            self._jumps[self._names[id_]] = pos
        else:
            raise ValueError(f"Jump label has already been set: {self._names[id_]}")

    def set_verify_jump(self, id_: int) -> None:
        """
        this verifies the label has been used
        it is used to not print out the unused labels
        """
        self._verify.add(self._names[id_])

    def verify_jump(self, id_: int) -> bool:
        """
        verifies the label is used or not
        """
        if not self._names[id_].isdigit():
            return True
        return self._names[id_] in self._verify


jump_manager = JumpManager()