import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QLineEdit,
    QFileDialog, QPushButton, QHBoxLayout, QTextEdit, QTabWidget, QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt
from fuzzywuzzy import fuzz
from tabs.crafting_table_tab import CraftingTableTab
from tabs.smelting_cooking_tab import SmeltingCookingTab

class CraftingGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.item_list = QListWidget()
        self.append_file_path = None
        self.item_file_path = None
        self.load_config()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Recipe Generator")
        main_layout = QVBoxLayout()

        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search Items (e.g., 'stone', 'minecraft stone')...")
        self.search_bar.textChanged.connect(self.filter_items)
        search_layout.addWidget(self.search_bar)

        self.load_button = QPushButton("Load Items/Blocks from File")
        self.load_button.clicked.connect(self.load_items_from_file)
        search_layout.addWidget(self.load_button)
        left_layout.addLayout(search_layout)

        self.item_list.itemClicked.connect(self.select_item)
        self.item_list.setMinimumHeight(250)
        left_layout.addWidget(self.item_list)

        self.tabs = QTabWidget()
        self.crafting_tab = CraftingTableTab(self.item_list, self)
        self.smelting_tab = SmeltingCookingTab(self.item_list, self)

        self.tabs.addTab(self.crafting_tab, "Crafting Table")
        self.tabs.addTab(self.smelting_tab, "Smelting/Cooking")
        left_layout.addWidget(self.tabs)

        left_widget.setLayout(left_layout)
        main_splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout()

        right_splitter = QSplitter(Qt.Orientation.Vertical)

        existing_recipes_widget = QWidget()
        existing_recipes_layout = QVBoxLayout()
        self.recipes_label = QLabel("Existing Recipes:")
        existing_recipes_layout.addWidget(self.recipes_label)

        recipes_search_layout = QHBoxLayout()
        self.recipes_search_bar = QLineEdit()
        self.recipes_search_bar.setPlaceholderText("Search Recipes (e.g., 'stone')...")
        self.recipes_search_bar.textChanged.connect(self.filter_recipes)
        recipes_search_layout.addWidget(self.recipes_search_bar)
        existing_recipes_layout.addLayout(recipes_search_layout)

        self.recipes_list = QListWidget()
        self.recipes_list.itemClicked.connect(self.display_selected_recipe)
        existing_recipes_layout.addWidget(self.recipes_list)

        delete_append_layout = QHBoxLayout()
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_recipe)
        delete_append_layout.addWidget(self.delete_button)

        self.append_button = QPushButton("Add")
        self.append_button.clicked.connect(self.append_to_file)
        delete_append_layout.addWidget(self.append_button)
        existing_recipes_layout.addLayout(delete_append_layout)

        existing_recipes_widget.setLayout(existing_recipes_layout)
        right_splitter.addWidget(existing_recipes_widget)

        generated_recipe_widget = QWidget()
        generated_recipe_layout = QVBoxLayout()
        self.result_label = QLabel("Generated Recipe / Viewer:")
        generated_recipe_layout.addWidget(self.result_label)
        self.result_display = QTextEdit()
        generated_recipe_layout.addWidget(self.result_display)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_recipes)
        generated_recipe_layout.addWidget(self.save_button)
        generated_recipe_widget.setLayout(generated_recipe_layout)
        right_splitter.addWidget(generated_recipe_widget)

        right_splitter.setSizes([300, 300])

        right_layout.addWidget(right_splitter)
        right_widget.setLayout(right_layout)
        main_splitter.addWidget(right_widget)

        main_splitter.setSizes([400, 400])

        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)

        if self.item_file_path and os.path.exists(self.item_file_path):
            self.load_items_from_file(auto_load=True)
        if self.append_file_path and os.path.exists(self.append_file_path):
            self.load_recipes()

    def display_selected_recipe(self, item):

        if item:
            recipe_text = item.data(Qt.ItemDataRole.UserRole)
            self.result_display.setText(recipe_text)

    def load_items_from_file(self, auto_load=False):
        if not auto_load:
            options = QFileDialog.Option.ReadOnly
            file_path, _ = QFileDialog.getOpenFileName(self, "Load Items/Blocks", "",
                                                       "Text Files (*.txt);;All Files (*)",
                                                       options=options)
        else:
            file_path = self.item_file_path

        if file_path and os.path.exists(file_path):
            with open(file_path, 'r') as file:
                items = file.read().splitlines()
                self.item_list.clear()
                self.item_list.addItems(items)
            self.item_file_path = file_path
            self.save_config()

    def filter_items(self):
        search_text = self.search_bar.text().strip().lower()

        if not hasattr(self, "all_items"):
            self.all_items = [self.item_list.item(i).text() for i in range(self.item_list.count())]

        if not search_text:
            self.item_list.clear()
            self.item_list.addItems(self.all_items)
            return

        exact_matches = []
        partial_matches = []

        for item_text in self.all_items:
            item_lower = item_text.lower().replace("_", " ")
            if all(term in item_lower for term in search_text.split()):
                exact_matches.append((item_text, 100))
            else:
                fuzzy_score = fuzz.partial_ratio(search_text, item_lower)
                if fuzzy_score >= 70:
                    partial_matches.append((item_text, fuzzy_score))

        sorted_items = sorted(exact_matches + partial_matches, key=lambda x: x[1], reverse=True)

        self.item_list.clear()
        self.item_list.addItems([item[0] for item in sorted_items])

    def filter_recipes(self):
        search_text = self.recipes_search_bar.text().strip().lower()

        all_recipes = self.crafting_tab.recipes + self.smelting_tab.recipes

        if not search_text:
            self.update_recipes_list()
            return

        filtered_recipes = []
        for recipe in all_recipes:
            output_item = ""
            if "event.shaped" in recipe or "event.shapeless" in recipe:
                output_item = self.crafting_tab.extract_output_item(recipe).lower()
            else:
                output_item = self.smelting_tab.extract_output_item(recipe).lower()

            if all(term in output_item for term in search_text.split()):
                filtered_recipes.append((recipe, 100))
            else:
                fuzzy_score = fuzz.partial_ratio(search_text, output_item)
                if fuzzy_score >= 70:
                    filtered_recipes.append((recipe, fuzzy_score))

        sorted_recipes = sorted(filtered_recipes, key=lambda x: x[1], reverse=True)

        self.recipes_list.clear()
        for recipe, _ in sorted_recipes:
            if "event.shaped" in recipe or "event.shapeless" in recipe:
                item = QListWidgetItem(f"[Crafting] {self.crafting_tab.extract_output_item(recipe)}")
            else:
                item = QListWidgetItem(f"[Smelting/Cooking] {self.smelting_tab.extract_output_item(recipe)}")
            item.setData(Qt.ItemDataRole.UserRole, recipe)
            self.recipes_list.addItem(item)

    def select_item(self, item):
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.selected_item = item.text()

    def save_config(self):
        config = {
            "item_file_path": self.item_file_path,
            "recipes_file_path": self.append_file_path
        }
        with open("config.json", "w") as f:
            json.dump(config, f)

    def load_config(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                self.item_file_path = config.get("item_file_path")
                self.append_file_path = config.get("recipes_file_path")
        except FileNotFoundError:
            pass

    def append_to_file(self):
        recipe_text = self.result_display.toPlainText()
        if not recipe_text or "Error:" in recipe_text:
            return

        if not self.append_file_path:
            self.browse_and_load_recipes()
            if not self.append_file_path:
                return

        if "event.shaped" in recipe_text or "event.shapeless" in recipe_text:
            self.crafting_tab.recipes.append(recipe_text)
        else:
            self.smelting_tab.recipes.append(recipe_text)

        self.update_recipes_list()
        self.result_label.setText("Recipe appended to memory (click Save to write to file)")

    def delete_recipe(self):
        selected_item = self.recipes_list.currentItem()
        if not selected_item or not self.append_file_path:
            self.result_label.setText("No recipe selected or file specified")
            return

        recipe_text = selected_item.data(Qt.ItemDataRole.UserRole)

        if recipe_text in self.crafting_tab.recipes:
            self.crafting_tab.recipes.remove(recipe_text)
        elif recipe_text in self.smelting_tab.recipes:
            self.smelting_tab.recipes.remove(recipe_text)

        self.recipes_list.takeItem(self.recipes_list.row(selected_item))
        self.result_label.setText("Recipe removed from memory (click Save to update file)")

    def save_recipes(self):
        if not self.append_file_path:
            self.result_label.setText("No file specified to save")
            return

        file_path = self.append_file_path
        is_js = file_path.endswith('.js')
        header = "ServerEvents.recipes(event => {\n" if is_js else "// Recipes\n"
        footer = "})\n" if is_js else ""

        all_recipes = self.crafting_tab.recipes + self.smelting_tab.recipes

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(header + "\n")
            for i, recipe in enumerate(all_recipes):
                if i > 0:
                    f.write("\n\n\n\n\n")
                f.write(f"  {recipe}\n")
            if is_js:
                f.write(footer)

        self.result_label.setText(f"Recipes saved to {file_path}")

    def load_recipes(self):
        if not self.append_file_path or not os.path.exists(self.append_file_path):
            self.result_label.setText("No valid recipes file selected")
            return

        self.crafting_tab.recipes = []
        self.smelting_tab.recipes = []

        file_path = self.append_file_path
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        current_recipe = []
        in_recipe = False

        for line in content.splitlines():
            stripped_line = line.strip()

            if any(stripped_line.startswith(f"event.{t}(") for t in
                   ["shaped", "shapeless", "smelting", "blasting", "smoking", "campfireCooking"]):
                in_recipe = True
                current_recipe = [line]
            elif in_recipe:
                current_recipe.append(line)
                if stripped_line == ")":
                    in_recipe = False
                    recipe_text = "\n".join(current_recipe)

                    if "event.shaped" in recipe_text or "event.shapeless" in recipe_text:
                        self.crafting_tab.recipes.append(recipe_text)
                    else:
                        self.smelting_tab.recipes.append(recipe_text)

        self.update_recipes_list()

    def update_recipes_list(self):
        self.recipes_list.clear()


        for recipe in self.crafting_tab.recipes:
            item = QListWidgetItem(f"[Crafting Table] {self.crafting_tab.extract_output_item(recipe)}")
            item.setData(Qt.ItemDataRole.UserRole, recipe)
            self.recipes_list.addItem(item)

        for recipe in self.smelting_tab.recipes:
            item = QListWidgetItem(f"[Smelting/Cooking] {self.smelting_tab.extract_output_item(recipe)}")
            item.setData(Qt.ItemDataRole.UserRole, recipe)
            self.recipes_list.addItem(item)

    def browse_and_load_recipes(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Recipes File", "",
            "JavaScript Files (*.js);;All Files (*)"
        )
        if file_path:
            self.append_file_path = file_path
            self.crafting_tab.append_path_input.setText(file_path)
            self.smelting_tab.append_path_input.setText(file_path)
            self.load_recipes()
            self.save_config()