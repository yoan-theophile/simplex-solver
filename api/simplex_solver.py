import ast
import copy
import csv
import os
from fractions import Fraction

clear = lambda: os.system('cls' if os.name == 'nt' else 'clear')


def fraction_to_text(fract):
    if fract.denominator == 1:
        return str(fract.numerator)
    else:
        return "{}/{}".format(str(fract.numerator), str(fract.denominator))


def generate_identity(n):
    ''' Helper function for generating a square identity matrix.
    '''
    I = []
    for i in range(0, n):
        row = []
        for j in range(0, n):
            if i == j:
                row.append(1)
            else:
                row.append(0)
        I.append(row)
    return I


def print_matrix(M):
    ''' Print some matrix.
    '''
    for row in M:
        print('|', end=' ')
        for val in row:
            print('{:^5}'.format(str(val)), end=' ')
        print('|')


class SimplexSolver():
    """ Résout des programmes linéaires en utilisant l'algorithme du simplexe et
            afficher les étapes du problème dans le fichier LaTeX.
    """

    def __init__(self, a, b, c, prob='max', ineq=[]):
        self.A = a
        self.B = b
        self.C = c
        self.tableau = []
        self.entering = []
        self.departing = []
        self.ineq = ineq
        self.prob = prob
        self.doc = ["Solveur Simplexe\n"]
        self.csv_doc = []

    def run_simplex(self):
        """ Exécutez l'algorithme du simplexe.
        """

        # Add slack & artificial variables
        self.set_simplex_input()

        # Are there any negative elements on the bottom (disregarding
        # right-most element...)
        while not self.should_terminate():
            # ... if so, continue.
            solution_courante = {}
            for key in self.get_current_solution().keys():
                solution_courante[key] = fraction_to_text(self.get_current_solution()[key])
            self.doc.append(f"Solution courante: {solution_courante}\n")

            # Attempt to find a non-negative pivot.
            pivot = self.find_pivot()
            if pivot[1] < 0:
                self.infeasible_doc()
                return None
            else:
                self.pivot_doc(pivot)

            # Do row operations to make every other element in column zero.
            self.pivot(pivot)
            self.table_doc()

        solution = self.get_current_solution()
        self.final_solution_doc(solution)

        return solution

    def set_simplex_input(self):
        ''' Définissez les variables initiales et créez un tableau.
        '''
        # Convertissez toutes les entrées en fractions pour plus de lisibilité.
        A = self.A.copy()
        b = self.B.copy()
        c = self.C.copy()

        self.A = []
        for a in A:
            self.A.append([Fraction(x) for x in a])
        self.B = [Fraction(x) for x in b]
        self.C = [Fraction(x) for x in c]
        if not self.ineq:
            if self.prob == 'max':
                self.ineq = ['<='] * len(b)
            elif self.prob == 'min':
                self.ineq = ['>='] * len(b)

        self.update_enter_depart(self.get_Ab())
        self.init_problem_doc()

        # Si c'est un probleme de minimisation ...
        if self.prob == 'min':
            # ... trouver le maximum et le résoudre.
            m = self.get_Ab()
            m.append(self.C + [0])
            m = [list(t) for t in zip(*m)]  # Calculates the transpose
            self.A = [x[:(len(x) - 1)] for x in m]
            self.B = [y[len(y) - 1] for y in m]
            self.C = m[len(m) - 1]
            self.A.pop()
            self.B.pop()
            self.C.pop()
            self.ineq = ['<='] * len(self.B)

        self.create_tableau()
        self.ineq = ['='] * len(self.B)
        self.update_enter_depart(self.tableau)
        self.slack_doc()
        self.init_tableau_doc()

    def update_enter_depart(self, matrix):
        self.entering = []
        self.departing = []
        # Create tables for entering and departing variables
        for i in range(0, len(matrix[0])):
            if i < len(self.A[0]):
                prefix = 'x' if self.prob == 'max' else 'y'
                self.entering.append("%s_%s" % (prefix, str(i + 1)))
            elif i < len(matrix[0]) - 1:
                self.entering.append("s_%s" % str(i + 1 - len(self.A[0])))
                self.departing.append("s_%s" % str(i + 1 - len(self.A[0])))
            else:
                self.entering.append("b")

    def add_slack_variables(self):
        ''' Ajoutez des variables d'écart et artificielles à la matrice A pour transformer
            toutes les inégalités aux égalités.
        '''
        slack_vars = generate_identity(len(self.tableau))
        for i in range(0, len(slack_vars)):
            self.tableau[i] += slack_vars[i]
            self.tableau[i] += [self.B[i]]

    def create_tableau(self):
        ''' Créer une table de tableau initiale.
        '''
        self.tableau = copy.deepcopy(self.A)
        self.add_slack_variables()
        c = copy.deepcopy(self.C)
        for index, value in enumerate(c):
            c[index] = -value
        self.tableau.append(c + [0] * (len(self.B) + 1))

    def find_pivot(self):
        ''' Trouver l'indice pivot.
        '''
        enter_index = self.get_entering_var()
        depart_index = self.get_departing_var(enter_index)
        return [enter_index, depart_index]

    def pivot(self, pivot_index):
        ''' Effectuer des opérations sur pivot.
        '''
        j, i = pivot_index

        pivot = self.tableau[i][j]
        self.tableau[i] = [element / pivot for
                           element in self.tableau[i]]
        for index, row in enumerate(self.tableau):
            if index != i:
                row_scale = [y * self.tableau[index][j]
                             for y in self.tableau[i]]
                self.tableau[index] = [x - y for x, y in
                                       zip(self.tableau[index],
                                           row_scale)]

        self.departing[i] = self.entering[j]

    def get_entering_var(self):
        ''' Obtenez la variable d'entrée en déterminant la "plus négative"
            élément de la ligne du bas.
        '''
        bottom_row = self.tableau[len(self.tableau) - 1]
        most_neg_ind = 0
        most_neg = bottom_row[most_neg_ind]
        for index, value in enumerate(bottom_row):
            if value < most_neg:
                most_neg = value
                most_neg_ind = index
        return most_neg_ind

    def get_departing_var(self, entering_index):
        ''' Pour calculer la variable de départ, obtenez le minimum du rapport
            de b (b_i) à la valeur correspondante dans la colonne entrante.
        '''
        skip = 0
        min_ratio_index = -1
        min_ratio = 0
        for index, x in enumerate(self.tableau):
            if x[entering_index] != 0 and x[len(x) - 1] / x[entering_index] > 0:
                skip = index
                min_ratio_index = index
                min_ratio = x[len(x) - 1] / x[entering_index]
                break

        if min_ratio > 0:
            for index, x in enumerate(self.tableau):
                if index > skip and x[entering_index] > 0:
                    ratio = x[len(x) - 1] / x[entering_index]
                    if min_ratio > ratio:
                        min_ratio = ratio
                        min_ratio_index = index

        return min_ratio_index

    def get_Ab(self):
        ''' Obtenez une matrice A avec le vecteur b ajouté.
        '''
        matrix = copy.deepcopy(self.A)
        for i in range(0, len(matrix)):
            matrix[i] += [self.B[i]]
        return matrix

    def should_terminate(self):
        ''' Détermine s'il y a des éléments négatifs
            sur la rangée du bas
        '''
        result = True
        index = len(self.tableau) - 1
        for i, x in enumerate(self.tableau[index]):
            if x < 0 and i != len(self.tableau[index]) - 1:
                result = False
        return result

    def get_current_solution(self):
        ''' Obtenez la solution actuelle à partir de tableau.
        '''
        solution = {}
        for x in self.entering:
            if x != 'b':
                if x in self.departing:
                    solution[x] = self.tableau[self.departing.index(x)] \
                        [len(self.tableau[self.departing.index(x)]) - 1]
                else:
                    solution[x] = 0
        solution['z'] = self.tableau[len(self.tableau) - 1] \
            [len(self.tableau[0]) - 1]

        # If this is a minimization problem...
        if self.prob == 'min':
            # ... then get x_1, ..., x_n  from last element of
            # the slack columns.
            bottom_row = self.tableau[len(self.tableau) - 1]
            for v in self.entering:
                if 's' in v:
                    solution[v.replace('s', 'x')] = bottom_row[self.entering.index(v)]

        return solution

    def init_problem_doc(self):
        # Objective function.
        doc = "Étant donné le système linéaire et la fonction objectif suivants, trouvez la solution optimale.\n"
        func = ""
        found_value = False
        for index, x in enumerate(self.C):
            opp = '+'
            if x == 0:
                continue
            if x < 0:
                opp = ' - '
            elif index == 0 or not found_value:
                opp = ''
            if x == 1 or x == -1:
                x = ''
            func += f" {opp} {str(x)}x_{str(index + 1)}"
            found_value = True
        doc += f"Equation {func}\n"
        self.doc.append(doc)

        self.linear_system_doc(self.get_Ab())

    def linear_system_doc(self, matrix):
        constraint = []
        for c in self.C:
            constraint.append(fraction_to_text(c))
        doc = f"{constraint}\n".replace("'", "")
        for i in range(0, len(matrix)):
            found_value = False
            for index, x in enumerate(matrix[i]):
                opp = '+'
                if x == 0 and index != len(matrix[i]) - 1:
                    continue
                if x < 0:
                    opp = '-'
                elif index == 0 or not found_value:
                    opp = ''
                if index != len(matrix[i]) - 1:
                    if x == 1 or x == -1:
                        x = ''
                    doc += f"{opp} {str(x)}{str(self.entering[index])}"
                else:
                    doc += f" {self.ineq[i]} {str(x)}"
                found_value = True
                if index == len(matrix[i]) - 1:
                    doc += f"\n"
        doc += ""
        self.doc.append(doc)

    def slack_doc(self):
        self.doc.append("Ajoutez des variables d'écart pour transformer toutes les inégalités en égalités.")
        self.linear_system_doc(self.tableau[:len(self.tableau) - 1])

    def init_tableau_doc(self):
        self.doc.append("Créez le tableau initial du nouveau système linéaire. \n")
        self.table_doc()

    def table_doc(self):
        csv_field = []
        doc = "Variables \n"
        for index, var in enumerate(self.entering):
            csv_field.append(var)
            if index != len(self.entering) - 1:
                doc += f"{var} | "
            else:
                doc += f"{var} \n"

        csv_field.insert(0, csv_field.pop())
        csv_field.insert(1, '')
        csv_row = []

        for indexr, row in enumerate(self.tableau):
            one_row = []
            for indexv, value in enumerate(row):
                one_row.append(value)
                if indexv != (len(row) - 1):
                    doc += f"{str(value)} | "
                elif indexr != (len(self.tableau) - 2):
                    doc += f"{str(value)} \n"
                else:
                    doc += f"{str(value)} \n"
            one_row.insert(0, one_row.pop())
            one_row.insert(1, '')
            csv_row.append(one_row)
        doc += "\n\n"

        doc += "Vecteur de base \n"
        variable_base = []
        for var in self.departing:
            doc += f"{var} \n"
            variable_base.append(var)
        for i in range(len(variable_base)):
            csv_row[i][1] = variable_base[i]

        doc += "\n"

        self.doc.append(doc)
        self.csv_doc.append([csv_field, csv_row])

    def infeasible_doc(self):
        self.doc.append("Il n'y a pas de candidats non négatifs pour le pivot. Ainsi, la solution est irréalisable.")

    def pivot_doc(self, pivot):
        doc = ''
        doc += (
            "Ainsi, pivotez pour améliorer la solution actuelle. La variable entrante est $%s$ et la variable "
            "sortante est $%s$.".format(str(self.entering[pivot[0]]),
                                        str(self.departing[pivot[1]])))
        doc += ("Effectuez des opérations élémentaires sur les lignes jusqu'à ce que l'élément pivot soit 1 "
                "et que tous les autres éléments de la colonne d'entrée soient 0.")

        self.doc.append(doc)

    def current_solution_doc(self, solution):
        doc = ""
        for key, value in sorted(solution.items()):
            doc += "{} = {}".format(key, fraction_to_text(value))
            if key != 'z':
                doc += ", "
        doc += ""
        self.doc.append(doc)

    def final_solution_doc(self, solution):
        self.doc.append("Il n'y a pas d'éléments négatifs dans la rangée du bas, nous savons donc que la solution est "
                        "optimale. Ainsi, la solution est : ")
        self.current_solution_doc(solution)

    def save_to_txt(self, filename):
        with open(filename, "w") as f:
            f.write("\n".join(self.doc))

    def print_csv_doc(self, filename, delimiter=';'):
        filename = os.path.splitext(filename)[0]
        for i in range(len(self.csv_doc)):
            csv_field, csv_row = self.csv_doc[i]

            file = "{}-etape{}.csv".format(filename, i + 1)

            # Write in csv file
            with open(file, 'w') as f:
                # using csv.writer method from CSV package
                write = csv.writer(f, delimiter=delimiter)

                write.writerow(csv_field)
                write.writerows(csv_row)

    def print_table(self):
        ''' Imprimer le tableau de simplex.
        '''
        print(' ', end=' ')
        for val in self.entering:
            print('{:^5}'.format(str(val)), end=' ')
        print(' ')
        for num, row in enumerate(self.tableau):
            print('|', end=' ')
            for index, val in enumerate(row):
                print('{:^5}'.format(str(val)), end=' ')
            if num < (len(self.tableau) - 1):
                print('| %s' % self.departing[num])
            else:
                print('|')


if __name__ == '__main__':
    s = SimplexSolver([[2, 1], [1, 2]], [4, 3], [1, 1])
    s.run_simplex()
    print(s.doc)
