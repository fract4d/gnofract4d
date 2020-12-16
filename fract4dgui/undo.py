
class HistoryEntry:
    def __init__(self, redo, redo_data, undo, undo_data):
        self.undo_action = undo
        self.undo_data = undo_data
        self.redo_action = redo
        self.redo_data = redo_data

    def undo(self):
        self.undo_action(self.undo_data)

    def redo(self):
        self.redo_action(self.redo_data)


class Sequence:
    def __init__(self):
        self.pos = 0  # the position after the current item
        self.history = []
        self.redo_callback = None
        self.undo_callback = None

    def register_callbacks(self, redo_callback, undo_callback):
        self.redo_callback = redo_callback
        self.undo_callback = undo_callback
        self.execute_callbacks()

    def can_undo(self):
        return self.pos > 0

    def can_redo(self):
        return self.pos < len(self.history)

    def execute_callbacks(self):
        self.redo_callback(self.can_redo())
        self.undo_callback(self.can_undo())

    def do(self, redo_action, redo_data, undo_action, undo_data):
        # replace everything from here on with the new item
        if self.pos < len(self.history):
            undo_action = self.history[self.pos].undo_action
            undo_data = self.history[self.pos].undo_data

        del self.history[self.pos:]
        self.history.append(
            HistoryEntry(redo_action, redo_data, undo_action, undo_data))
        self.pos = len(self.history)

        self.execute_callbacks()

    def undo(self):
        if not self.can_undo():
            raise ValueError("Can't Undo at start of sequence")
        self.pos -= 1
        self.history[self.pos].undo()

        self.execute_callbacks()

    def redo(self):
        if not self.can_redo():
            raise ValueError("Can't Redo at end of sequence")
        self.history[self.pos].redo()
        self.pos += 1

        self.execute_callbacks()
