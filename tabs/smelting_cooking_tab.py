from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QSpinBox, QFileDialog
from PyQt6.QtCore import Qt
import os

class SmeltingCookingTab(QWidget):
    def __init__(self, shared_item_list, parent_gui):
        super().__init__()
        self.selected_item = None
        self.output_quantity = 1
        self.input_item = None
        self.output_item = None
        self.item_list = shared_item_list
        self.parent_gui = parent_gui
        self.recipes = []
        self.mode = "smelting"
        self.xp = 0.0
        self.time = 20
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        slots_layout = QHBoxLayout()
        self.input_slot = QLabel("")
        self.input_slot.setStyleSheet(
            "border: 2px solid gray; background-color: gray; min-width: 40px; min-height: 40px;")
        self.input_slot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_slot.mousePressEvent = self.handle_input_click
        slots_layout.addWidget(self.input_slot)

        self.arrow_label = QLabel("            →")
        self.arrow_label.setStyleSheet("font-size: 24px; margin: 0 20px;")
        slots_layout.addWidget(self.arrow_label)

        self.output_slot = QLabel("")
        self.output_slot.setStyleSheet(
            "border: 2px solid gray; background-color: gray; min-width: 40px; min-height: 40px;")
        self.output_slot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.output_slot.mousePressEvent = self.handle_output_click
        slots_layout.addWidget(self.output_slot)
        layout.addLayout(slots_layout)

        mode_layout = QHBoxLayout()
        self.mode_buttons = {
            "smelting": QPushButton("Smelting"),
            "blasting": QPushButton("Blasting"),
            "smoking": QPushButton("Smoking"),
            "campfireCooking": QPushButton("Campfire Cooking")
        }

        for mode, button in self.mode_buttons.items():
            button.setCheckable(True)
            button.clicked.connect(lambda checked, m=mode: self.set_mode(m))
            mode_layout.addWidget(button)
        self.mode_buttons["smelting"].setChecked(True)
        layout.addLayout(mode_layout)

        quantity_layout = QHBoxLayout()
        quantity_label = QLabel("Output Quantity (1-64):")
        quantity_layout.addWidget(quantity_label)
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 64)
        self.quantity_spinbox.setValue(1)
        self.quantity_spinbox.valueChanged.connect(self.update_output_quantity)
        quantity_layout.addWidget(self.quantity_spinbox)
        layout.addLayout(quantity_layout)

        xp_layout = QHBoxLayout()
        xp_label = QLabel("XP (0.0 - ∞):")
        xp_layout.addWidget(xp_label)
        self.xp_spinbox = QSpinBox()
        self.xp_spinbox.setRange(0, 1000000)
        self.xp_spinbox.setValue(0)
        self.xp_spinbox.valueChanged.connect(self.update_xp)
        xp_layout.addWidget(self.xp_spinbox)
        layout.addLayout(xp_layout)

        time_layout = QHBoxLayout()
        time_label = QLabel("Time (seconds):")
        time_layout.addWidget(time_label)
        self.time_spinbox = QSpinBox()
        self.time_spinbox.setRange(1, 1000000)
        self.time_spinbox.setValue(20)
        self.time_spinbox.valueChanged.connect(self.update_time)
        time_layout.addWidget(self.time_spinbox)
        layout.addLayout(time_layout)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_slots)
        layout.addWidget(self.reset_button)

        self.generate_button = QPushButton("Generate Recipe")
        self.generate_button.clicked.connect(self.generate_recipe)
        layout.addWidget(self.generate_button)

        self.append_path_input = QLineEdit()
        self.append_path_input.setPlaceholderText("Paste or select file path (e.g., recipes.js)")
        if self.parent_gui.append_file_path:
            self.append_path_input.setText(self.parent_gui.append_file_path)
        self.append_path_input.textChanged.connect(self.update_append_path)

        layout.addStretch(1)

        self.setLayout(layout)

    def set_mode(self, mode):
        self.mode = mode
        for m, button in self.mode_buttons.items():
            button.setChecked(m == mode)

    def handle_input_click(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.selected_item:
            self.input_item = self.selected_item
            self.input_slot.setText(self.selected_item)
        elif event.button() == Qt.MouseButton.RightButton:
            self.input_item = None
            self.input_slot.setText("")

    def handle_output_click(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.selected_item:
            self.output_item = self.selected_item
            self.output_slot.setText(self.selected_item)
        elif event.button() == Qt.MouseButton.RightButton:
            self.output_item = None
            self.output_slot.setText("")

    def reset_slots(self):
        self.input_item = None
        self.input_slot.setText("")
        self.output_item = None
        self.output_slot.setText("")
        self.quantity_spinbox.setValue(1)
        self.xp_spinbox.setValue(35)
        self.time_spinbox.setValue(30)

    def update_output_quantity(self, value):
        self.output_quantity = value

    def update_xp(self, value):
        self.xp = value
    def update_time(self, value):
        self.time = value * 20

    def browse_and_load_recipes(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Recipes File to Append/Delete", "recipes.js",
            "JavaScript Files (*.js);;All Files (*)"
        )
        if file_path:
            self.parent_gui.append_file_path = file_path
            self.append_path_input.setText(file_path)
            self.load_recipes()
            self.parent_gui.save_config()

    def update_append_path(self, text):
        self.parent_gui.append_file_path = text.strip() if text.strip() else None

    def load_recipes(self):
        if not self.parent_gui.append_file_path or not os.path.exists(self.parent_gui.append_file_path):
            self.parent_gui.result_label.setText("No valid recipes file selected")
            self.recipes = []
            self.all_recipes = []
            return

        file_path = self.parent_gui.append_file_path
        self.recipes = []
        self.all_recipes = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        current_recipe = []
        in_recipe = False

        for line in content.splitlines():
            stripped_line = line.strip()
            if stripped_line.startswith("event.smelting(") or stripped_line.startswith("event.blasting(") or \
                    stripped_line.startswith("event.smoking(") or stripped_line.startswith("event.campfireCooking("):
                in_recipe = True
                current_recipe = [line]
            elif in_recipe:
                current_recipe.append(line)
                if stripped_line == ")":
                    in_recipe = False
                    recipe_text = "\n".join(current_recipe)
                    self.recipes.append(recipe_text)
                    self.all_recipes.append(recipe_text)

        self.parent_gui.update_recipes_list()

    def extract_output_item(self, recipe):
        for line in recipe.splitlines():
            if "Item.of(" in line:
                start = line.find("'") + 1
                end = line.find("'", start)
                if start > 0 and end > start:
                    return line[start:end]
        return "Unknown Recipe"

    def append_to_file(self):
        recipe_text = self.parent_gui.result_display.toPlainText()
        if not recipe_text or "Error:" in recipe_text:
            return

        if not self.parent_gui.append_file_path:
            self.browse_and_load_recipes()
            if not self.parent_gui.append_file_path:
                return

        if recipe_text in self.recipes:
            self.parent_gui.result_label.setText("Recipe already exists in memory")
            return

        self.recipes.append(recipe_text)
        self.all_recipes.append(recipe_text)
        self.parent_gui.update_recipes_list()
        self.parent_gui.result_label.setText("Recipe appended to memory (click Save to write to file)")

    def delete_recipe(self):
        selected_item = self.parent_gui.recipes_list.currentItem()
        if not selected_item or not self.parent_gui.append_file_path:
            self.parent_gui.result_label.setText("No recipe selected or file specified")
            return

        recipe_text = selected_item.data(Qt.ItemDataRole.UserRole)
        if recipe_text in self.recipes:
            self.recipes.remove(recipe_text)
            self.all_recipes.remove(recipe_text)
            self.parent_gui.recipes_list.takeItem(self.parent_gui.recipes_list.row(selected_item))
            self.parent_gui.result_label.setText("Recipe removed from memory (click Save to update file)")
        else:
            self.parent_gui.result_label.setText("Recipe not found in memory")

    def generate_recipe(self):
        recipe_text = self.generate_recipe_text()
        if recipe_text:
            self.parent_gui.result_display.setText(recipe_text)

    def generate_recipe_text(self):
        if not self.input_item or not self.output_item:
            return "Error: Please set input and output items."

        recipe = (
            f"event.{self.mode}(\n"
            f"  Item.of('{self.output_item}', {self.output_quantity}),\n"
            f"  '{self.input_item}',\n"
            f"  {self.xp},\n"
            f"  {self.time}\n)"
        )
        return recipe

    def save_recipes(self):
        if not self.parent_gui.append_file_path:
            self.parent_gui.result_label.setText("No file specified to save")
            return

        file_path = self.parent_gui.append_file_path
        is_js = file_path.endswith('.js')
        header = "ServerEvents.recipes(event => {\n" if is_js else "// Recipes\n"
        footer = "})\n" if is_js else ""

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(header + "\n")
            for i, recipe in enumerate(self.recipes):
                if i > 0:
                    f.write("\n\n\n\n\n")
                f.write(f"  {recipe}\n")
            if is_js:
                f.write(footer)

        self.parent_gui.result_label.setText(f"Recipes saved to {file_path}")