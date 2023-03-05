import sys
import os
from PySide6.QtWidgets import QApplication
from main_window import MainWindow
from qt_material import apply_stylesheet


if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    window = MainWindow()

    # setup stylesheet
    css_file = os.path.join('ressources', 'css', 'custom.css')
    apply_stylesheet(app, theme='light_cyan_500.xml', invert_secondary=True, css_file=css_file)

    window.show()
    # Run the main Qt loop
    sys.exit(app.exec())
