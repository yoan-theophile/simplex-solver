import ast
import os.path

from pathlib import Path
from PySide6 import QtWidgets
from PySide6.QtGui import Qt

from api.simplex_solver import SimplexSolver, fraction_to_text


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("SimplexSolverApp"))
        self.setup_ui()
        self.A = []
        self.B = []
        self.C = []
        self.problem_type = 'max'
        self.simplex_solver = None

    def setup_ui(self):
        self.create_widgets()
        self.modify_widgets()
        self.create_layouts()
        self.add_widgets_to_layouts()
        self.setup_connections()

        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setFixedHeight(self.sizeHint().height() + 50)
        self.setFixedWidth(self.sizeHint().width() + 500)

    def create_widgets(self):
        self.intro_label = QtWidgets.QLabel()

        self.a_matrix_line_edit = QtWidgets.QLineEdit()
        self.b_matrix_line_edit = QtWidgets.QLineEdit()
        self.c_matrix_line_edit = QtWidgets.QLineEdit()
        # self.interactiveModeCheckBox = QtWidgets.QCheckBox(self.tr("Mode &interactif"), self)

        self.reset_button = QtWidgets.QPushButton("&Réinitialiser")
        self.solver_button = QtWidgets.QPushButton(self.tr("Solutionner"))
        self.min_radio_button = QtWidgets.QRadioButton("MIN")
        self.max_radio_button = QtWidgets.QRadioButton("MAX")

        self.option_left_spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding,
                                                        QtWidgets.QSizePolicy.Policy.Minimum)

    def modify_widgets(self):
        self.intro_label.setText(self.tr("Ce programmme permet de résoudre des problèmes de programmation linéaire de "
                                         "la forme matricielle AX <= B avec les contraintes C en utilisant la méthode"
                                         " du simplexe."))
        # add placeholders to lines edit
        self.a_matrix_line_edit.setPlaceholderText("Ex: [[2,1],[1,2]]")
        self.b_matrix_line_edit.setPlaceholderText("Ex: [4,3]")
        self.c_matrix_line_edit.setPlaceholderText("Ex: [1,1]")

        # Maximisation by default
        self.max_radio_button.setChecked(True)

        self.intro_label.setWordWrap(True)

        self.reset_button.setProperty('class', 'warning')

    def create_layouts(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.input_form_layout = QtWidgets.QFormLayout()
        self.options_form_layout = QtWidgets.QHBoxLayout()

    def add_widgets_to_layouts(self):
        self.input_form_layout.addRow(self.tr("&A"), self.a_matrix_line_edit)
        self.input_form_layout.addRow(self.tr("&B"), self.b_matrix_line_edit)
        self.input_form_layout.addRow(self.tr("&C"), self.c_matrix_line_edit)

        self.options_form_layout.addWidget(self.max_radio_button)
        self.options_form_layout.addWidget(self.min_radio_button)
        self.options_form_layout.addItem(self.option_left_spacer)
        self.options_form_layout.addWidget(self.reset_button)
        # self.options_form_layout.addWidget(self.interactiveModeCheckBox)

        self.main_layout.addWidget(self.intro_label)
        self.main_layout.addLayout(self.input_form_layout)
        self.main_layout.addLayout(self.options_form_layout)

        self.main_layout.addWidget(self.solver_button)

        self.a_matrix_line_edit.setFocus()

    def setup_connections(self):
        self.solver_button.clicked.connect(self.solve_problem)
        self.reset_button.clicked.connect(self.reset_entries)

    # END UI

    def solve_problem(self):
        # get input
        try:
            self.get_input()
        except Exception:
            self.display_invalid_parameter_error()
            return

        # check the inputs
        if self.is_input_valid():
            self.solver_button.setEnabled(False)
            self.simplex_solver = SimplexSolver(self.A, self.B, self.C, prob=self.problem_type)
            self.simplex_solver.run_simplex()
            self.solver_button.setEnabled(True)
        else:
            self.display_invalid_parameter_error()

        # Show the solution
        self.show_result_dialog()

    def is_input_valid(self):
        # Now we check if the matrix are not empty
        matrix = [self.A, self.B, self.C]
        for m in matrix:
            if len(m) == 0:
                # print("Une matrice est vide !")
                return False

        # check if the rows of the A matrix have the same size
        a_size = [len(self.A), 0]
        for row in self.A:
            if a_size[1] == 0:
                a_size[1] = len(row)
            else:
                if a_size[1] != len(row):
                    # print("La matrice A n'a pas les lignes de meme taille !")
                    return False

        # Here we check if the different matrix have are compatible by their size
        b_size = [1, len(self.B)]
        c_size = [len(self.C), 1]
        # Si on doit avoir ces tailles ainsi a: A[mxn] * B[1xm] = C[nx1]
        if a_size[0] != b_size[1] or b_size[0] != c_size[1] or a_size[1] != c_size[0]:
            # print("La condition suivante n'est pas respectee A[mxn] * B[1xm] = C[nx1]")
            return False

        return True

    def get_input(self):
        # get A< B, C
        self.A = ast.literal_eval(self.a_matrix_line_edit.text())
        self.B = ast.literal_eval(self.b_matrix_line_edit.text())
        self.C = ast.literal_eval(self.c_matrix_line_edit.text())

        # Get problem type
        if self.max_radio_button.isChecked():
            self.problem_type = 'max'
        else:
            self.problem_type = 'min'

    def display_invalid_parameter_error(self):
        # Display the error
        QtWidgets.QMessageBox.warning(self, self.tr("Parametres incorrects"),
                                      self.tr("Certaines matrices ne sont pas correctes.\n"
                                              "Veuillez verifier et reessayer a nouveau."),
                                      QtWidgets.QMessageBox.StandardButton.Ok)

    @property
    def location_of_result_file(self):
        name = QtWidgets.QFileDialog.getSaveFileName(self, self.tr("Enregistrer le fichier"), os.path.join(Path.home()),
                                                     self.tr('Text Documents (*.txt)'),
                                                     self.tr('Text Documents (*.txt)'))
        return name

    def reset_entries(self):
        self.a_matrix_line_edit.setText("")
        self.b_matrix_line_edit.setText("")
        self.c_matrix_line_edit.setText("")

        self.max_radio_button.setChecked(True)

    def show_result_dialog(self):
        solution = self.simplex_solver.get_current_solution()
        doc = ""
        if solution:
            for key, value in sorted(solution.items()):
                doc += "{} = {}".format(key, fraction_to_text(value))
                if key != 'z':
                    doc += ", "
            text = f"La solution est : {doc}"
        else:
            text = "La solution est irréalisable."

        msg_box = QtWidgets.QMessageBox()
        msg_box.setText(text)
        msg_box.setWindowTitle(self.tr("Solution"))
        msg_box.setDetailedText('\n'.join(self.simplex_solver.doc))
        msg_box.setInformativeText(self.tr("Voulez-vous enregistrer la solution ?"))

        msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Save
                                   | QtWidgets.QMessageBox.StandardButton.Discard)
        msg_box.setButtonText(QtWidgets.QMessageBox.StandardButton.Save, self.tr("Enregistrer"))
        msg_box.setButtonText(QtWidgets.QMessageBox.StandardButton.Discard, self.tr("Annuler"))

        msg_box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Save)

        ret = msg_box.exec_()
        if ret == QtWidgets.QMessageBox.StandardButton.Save:
            file = self.location_of_result_file[0]
            if file:
                self.simplex_solver.save_to_txt(file)
                self.simplex_solver.print_csv_doc(file)

    def save_result(self):
        pass
