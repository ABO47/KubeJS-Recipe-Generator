from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QSpinBox, QSlider, QPushButton, QLineEdit, QHBoxLayout, QSizePolicy, QCheckBox, QFileDialog
from PyQt6.QtCore import Qt

class CraftingTableTab(QWidget):
    def __init__(self, shared_item_list, parent_gui):
        super().__init__()
        self.selected_item = None
        self.output_quantity = 1
        self.input_slots = [[None for _ in range(3)] for _ in range(3)]
        self.output_item = None
        self.item_list = shared_item_list
        self.parent_gui = parent_gui
        self.recipes = []
        self.is_shaped = True
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        grid_layout = QGridLayout()
        self.slot_labels = [[None for _ in range(3)] for _ in range(3)]
        for row in range(3):
            for col in range(3):
                slot = QLabel("")
                slot.setStyleSheet("border: 2px solid gray; background-color: gray; min-width: 40px; min-height: 40px;")
                slot.setAlignment(Qt.AlignmentFlag.AlignCenter)
                slot.mousePressEvent = lambda event, r=row, c=col: self.handle_slot_click(event, r, c)
                self.slot_labels[row][col] = slot
                grid_layout.addWidget(slot, row, col)
        layout.addLayout(grid_layout)

        output_grid_layout = QGridLayout()
        self.output_slot = QLabel("")
        self.output_slot.setStyleSheet(
            "border: 2px solid black; background-color: gray; min-width: 40px; min-height: 40px;")
        self.output_slot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.output_slot.mousePressEvent = self.handle_output_click
        output_grid_layout.addWidget(self.output_slot, 0, 1)
        output_grid_layout.setColumnStretch(0, 1)
        output_grid_layout.setColumnStretch(2, 1)
        layout.addLayout(output_grid_layout)

        quantity_layout = QHBoxLayout()
        quantity_label = QLabel("Output Quantity (1-64):")
        quantity_layout.addWidget(quantity_label)
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 64)
        self.quantity_spinbox.setValue(1)
        self.quantity_spinbox.valueChanged.connect(self.update_output_quantity_from_spinbox)
        quantity_layout.addWidget(self.quantity_spinbox)
        self.quantity_slider = QSlider(Qt.Orientation.Horizontal)
        self.quantity_slider.setRange(1, 64)
        self.quantity_slider.setValue(1)
        self.quantity_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.quantity_slider.valueChanged.connect(self.update_output_quantity_from_slider)
        quantity_layout.addWidget(self.quantity_slider)

        self.shaped_checkbox = QCheckBox("Shaped Crafting")
        self.shaped_checkbox.setChecked(True)
        self.shaped_checkbox.stateChanged.connect(self.toggle_crafting_mode)
        quantity_layout.addWidget(self.shaped_checkbox)
        layout.addLayout(quantity_layout)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_slots)
        layout.addWidget(self.reset_button)

        self.generate_button = QPushButton("Generate Recipe")
        self.generate_button.clicked.connect(self.generate_recipe)
        layout.addWidget(self.generate_button)

        file_buttons_layout = QHBoxLayout()
        self.create_file_button = QPushButton("  Create File  ")
        self.create_file_button.clicked.connect(self.create_new_file)
        file_buttons_layout.addWidget(self.create_file_button)
        self.name_space_input = QLineEdit()
        self.name_space_input.setPlaceholderText("Namespace (e.g., recipes)")
        file_buttons_layout.addWidget(self.name_space_input)
        layout.addLayout(file_buttons_layout)

        second_row_layout = QHBoxLayout()
        self.browse_load_button = QPushButton("Load Recipes")
        self.browse_load_button.clicked.connect(self.browse_and_load_recipes)
        second_row_layout.addWidget(self.browse_load_button)
        self.append_path_input = QLineEdit()
        self.append_path_input.setPlaceholderText("Paste or select file path (e.g., recipes.js)")
        if self.parent_gui.append_file_path:
            self.append_path_input.setText(self.parent_gui.append_file_path)
        self.append_path_input.textChanged.connect(self.update_append_path)
        second_row_layout.addWidget(self.append_path_input)
        layout.addLayout(second_row_layout)

        layout.addStretch(1)
        self.setLayout(layout)

    def toggle_crafting_mode(self):
        self.is_shaped = self.shaped_checkbox.isChecked()
        self.reset_slots()

    def handle_slot_click(self, event, row, col):
        if event.button() == Qt.MouseButton.LeftButton and self.selected_item:
            self.input_slots[row][col] = self.selected_item
            self.slot_labels[row][col].setText(self.selected_item)
        elif event.button() == Qt.MouseButton.RightButton:
            self.input_slots[row][col] = None
            self.slot_labels[row][col].setText("")

    def handle_output_click(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.selected_item:
            self.output_item = self.selected_item
            self.output_slot.setText(self.selected_item)
        elif event.button() == Qt.MouseButton.RightButton:
            self.output_item = None
            self.output_slot.setText("")

    def reset_slots(self):
        for row in range(3):
            for col in range(3):
                self.input_slots[row][col] = None
                self.slot_labels[row][col].setText("")
        self.output_item = None
        self.output_slot.setText("")
        self.quantity_spinbox.setValue(1)
        self.quantity_slider.setValue(1)

    def update_output_quantity_from_spinbox(self, value):
        self.output_quantity = value
        self.quantity_slider.setValue(value)

    def update_output_quantity_from_slider(self, value):
        self.output_quantity = value
        self.quantity_spinbox.setValue(value)

    def browse_and_load_recipes(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Recipes File", "",
            "JavaScript Files (*.js);;All Files (*)"
        )
        if file_path:
            self.parent_gui.append_file_path = file_path
            self.append_path_input.setText(file_path)
            self.parent_gui.smelting_tab.append_path_input.setText(file_path)
            self.parent_gui.load_recipes()
            self.parent_gui.save_config()

    def create_new_file(self):
        namespace = self.name_space_input.text().strip()
        if not namespace:
            namespace = "recipes"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Create New Recipe File", f"{namespace}.js",
            "JavaScript Files (*.js);;All Files (*)"
        )

        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("ServerEvents.recipes(event => {\n  // Recipes will be placed here\n})\n")

            self.parent_gui.append_file_path = file_path
            self.append_path_input.setText(file_path)
            self.parent_gui.smelting_tab.append_path_input.setText(file_path)
            self.parent_gui.load_recipes()
            self.parent_gui.save_config()

    def update_append_path(self, text):
        self.parent_gui.append_file_path = text.strip() if text.strip() else None
        self.parent_gui.smelting_tab.append_path_input.setText(text)

    def extract_output_item(self, recipe):
        for line in recipe.splitlines():
            if "Item.of(" in line:
                start = line.find("'") + 1
                end = line.find("'", start)
                if start > 0 and end > start:
                    return line[start:end]
        return "Unknown Recipe"

    def generate_recipe(self):
        recipe_text = self.generate_recipe_text()
        if recipe_text:
            self.parent_gui.result_display.setText(recipe_text)

    def generate_recipe_text(self):
        crafting_grid = self.input_slots
        output_item = self.output_item

        if not any(any(row) for row in crafting_grid) or not output_item:
            return "Error: Please fill in input slots and set an output."

        if self.is_shaped:
            placeholder_grid = [[" " for _ in range(3)] for _ in range(3)]
            mapping = {}
            item_to_placeholder = {}
            for row in range(3):
                for col in range(3):
                    if crafting_grid[row][col]:
                        if crafting_grid[row][col] not in item_to_placeholder:
                            placeholder = chr(ord('A') + len(item_to_placeholder))
                            item_to_placeholder[crafting_grid[row][col]] = placeholder
                            mapping[placeholder] = crafting_grid[row][col]
                        placeholder_grid[row][col] = item_to_placeholder[crafting_grid[row][col]]

            recipe_grid = ",\n".join([f"    '{''.join(row)}'" for row in placeholder_grid])
            recipe_mappings = "\n".join([
                f"    {key}: '{value}'" + ("," if idx < len(mapping) - 1 else "")
                for idx, (key, value) in enumerate(mapping.items())
            ])
            return (
                f"event.shaped(\n"
                f"  Item.of('{output_item}', {self.output_quantity}),\n"
                f"  [\n{recipe_grid}\n  ],\n"
                f"  {{\n{recipe_mappings}\n  }}\n)"
            )
        else:
            shapeless_inputs = {}
            for row in range(3):
                for col in range(3):
                    if crafting_grid[row][col]:
                        item = crafting_grid[row][col]
                        shapeless_inputs[item] = shapeless_inputs.get(item, 0) + 1

            items_list = list(shapeless_inputs.items())
            recipe = (
                f"event.shapeless(\n"
                f"  Item.of('{output_item}', {self.output_quantity}),\n"
                f"  [\n"
            )
            for idx, (item, count) in enumerate(items_list):
                formatted_item = f"    '{count}x {item}'" if count > 1 else f"    '{item}'"
                if idx < len(items_list) - 1:
                    formatted_item += ","
                recipe += formatted_item + "\n"
            recipe += "  ]\n)"
            return recipe