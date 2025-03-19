import sys
import sqlite3
import pandas as pd
from fpdf import FPDF
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QMessageBox, QVBoxLayout, QPushButton, QLineEdit, QLabel, QHBoxLayout
from PyQt5.QtWidgets import QCompleter
from PyQt5.QtCore import QStringListModel  # Correct import
from datetime import datetime

# Connexion à SQLite
conn = sqlite3.connect("appuis.db")
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS beneficiaires (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        adresse TEXT,
        type_appui TEXT,
        montant REAL,
        annee INTEGER
    )
''')
conn.commit()

class App(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Gestion des Bénéficiaires")
        self.setGeometry(100, 100, 1000, 750)
        self.setStyleSheet("background-color: #f0f0f0;")
        
        layout = QtWidgets.QVBoxLayout()
        title = QLabel("Gestion des Bénéficiaires", self)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)

        form_layout = QtWidgets.QFormLayout()
        self.nom_input = QLineEdit()
        self.completer = QCompleter(self)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)  # Ignorer la casse
        self.completer.setFilterMode(QtCore.Qt.MatchContains)  # Correspondance partielle
        self.nom_input.setCompleter(self.completer)
        
        # Auto-complétion pour "Adresse"
        self.adresse_input = QLineEdit()
        self.completer_adresse = QCompleter(self)
        self.completer_adresse.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.completer_adresse.setFilterMode(QtCore.Qt.MatchContains)
        self.adresse_input.setCompleter(self.completer_adresse)

        # Auto-complétion pour "Type d'Appui"
        self.type_input = QLineEdit()
        self.completer_type = QCompleter(self)
        self.completer_type.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.completer_type.setFilterMode(QtCore.Qt.MatchContains)
        self.type_input.setCompleter(self.completer_type)

        self.mettre_a_jour_suggestions()  # Charger les suggestions initiales
        self.adresse_input = QLineEdit()
        self.type_input = QLineEdit()
        self.montant_input = QLineEdit()
        self.montant_input.setValidator(QtGui.QDoubleValidator(0.0, 99999999.99, 2))  # Permet uniquement les nombres
        self.annee_input = QtWidgets.QComboBox()
        self.annee_input.addItems([str(year) for year in range(1900, 3000)])


        form_layout.addRow("Nom :", self.nom_input)
        form_layout.addRow("Adresse :", self.adresse_input)
        form_layout.addRow("Type d'appui :", self.type_input)
        form_layout.addRow("Montant :", self.montant_input)
        form_layout.addRow("Année :", self.annee_input)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Ajouter Bénéficiaire")
        self.add_button.setStyleSheet("background-color: #0078D7; color: white; padding: 10px; border-radius: 5px;")
        self.add_button.clicked.connect(self.ajouter_beneficiaire)
        button_layout.addWidget(self.add_button)

        layout.addLayout(button_layout)
        
        # Bouton pour exporter la base de données complète ou un bénéficiaire spécifique
        self.export_button = QPushButton("Exporter la base de données")
        self.export_button.setStyleSheet("background-color: #28a745; color: white; padding: 10px; border-radius: 5px;")
        self.export_button.clicked.connect(self.exporter_donnees)
        layout.addWidget(self.export_button)

        self.setLayout(layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par nom...")
        self.search_button = QPushButton("Rechercher")
        self.search_button.setStyleSheet("background-color: #17a2b8; color: white; padding: 10px; border-radius: 5px;")
        self.search_button.clicked.connect(self.rechercher_beneficiaire)
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Nom", "Adresse", "Type d'appui", "Montant", "Année"])
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.afficher_beneficiaires()
        conn.commit()  # S'assurer que les données sont bien enregistrées
        self.mettre_a_jour_suggestions()  # Mise à jour des suggestions après l'affichage de la fenêtre
    
    def mettre_a_jour_suggestions(self):
        """Mise à jour des suggestions de noms en fonction de la base de données."""
        cursor.execute("SELECT DISTINCT nom FROM beneficiaires")
        noms = [row[0] for row in cursor.fetchall()]
        model = QStringListModel(noms)
        self.completer.setModel(model)
        
       
        cursor.execute("SELECT DISTINCT nom FROM beneficiaires")
        noms = [row[0] for row in cursor.fetchall()]
        self.completer.setModel(QStringListModel(noms))
    
        cursor.execute("SELECT DISTINCT type_appui FROM beneficiaires WHERE type_appui IS NOT NULL")
        types = [row[0] for row in cursor.fetchall()]
        self.completer_type.setModel(QStringListModel(types))
 
        cursor.execute("SELECT DISTINCT adresse FROM beneficiaires WHERE adresse IS NOT NULL")
        adresses = [row[0] for row in cursor.fetchall()]
        self.completer_adresse.setModel(QStringListModel(adresses))
        

    def ajouter_beneficiaire(self):
        nom = self.nom_input.text().strip()
        adresse = self.adresse_input.text().strip()
        type_appui = self.type_input.text().strip()
        montant = self.montant_input.text().strip()
        annee = self.annee_input.currentText().strip()

        if not nom or not annee:
            QMessageBox.warning(self, "Erreur", "Nom et Année sont obligatoires !")
            return

        # Vérifier si l'utilisateur existe déjà dans la base
        cursor.execute("SELECT id FROM beneficiaires WHERE nom=?", [nom])
        existing_data = cursor.fetchone()

        if existing_data:
            choix = QMessageBox.question(
                self, "Bénéficiaire existant",
                "Ce bénéficiaire existe déjà. Voulez-vous mettre à jour ses informations ?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )

            if choix == QMessageBox.Yes:
                cursor.execute("UPDATE beneficiaires SET adresse=?, type_appui=?, montant=?, annee=? WHERE id=?", 
                               (adresse, type_appui, montant, annee, existing_data[0]))  # `existing_data[0]` est bien l'ID
                conn.commit()
                QMessageBox.information(self, "Mise à jour", "Les informations du bénéficiaire ont été mises à jour avec succès.")
            else:
                QMessageBox.information(self, "Aucune modification", "Les informations existantes ont été conservées.")
        else:
            cursor.execute("INSERT INTO beneficiaires (nom, adresse, type_appui, montant, annee) VALUES (?, ?, ?, ?, ?)",
                           (nom, adresse, type_appui, montant, annee))
            conn.commit()
            QMessageBox.information(self, "Succès", "Bénéficiaire ajouté avec succès.")


        self.afficher_beneficiaires()
        self.mettre_a_jour_suggestions()  # Mise à jour des suggestions après ajout
        
        # Réinitialiser les champs après l'ajout
        self.nom_input.clear()
        self.adresse_input.clear()
        self.type_input.clear()
        self.montant_input.clear()
        self.annee_input.clear()  
        
    def afficher_beneficiaires(self):
        self.table.setRowCount(0)
        cursor.execute("SELECT * FROM beneficiaires")
        for row_index, row_data in enumerate(cursor.fetchall()):
            self.table.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                self.table.setItem(row_index, col_index, QTableWidgetItem(str(data)))

    def rechercher_beneficiaire(self):
        recherche = self.search_input.text()
        self.table.setRowCount(0)
        cursor.execute("SELECT * FROM beneficiaires WHERE nom LIKE ?", ('%' + recherche + '%',))
        for row_index, row_data in enumerate(cursor.fetchall()):
            self.table.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                item = QTableWidgetItem(str(data))
                item.setForeground(QtGui.QColor("red"))  # Met en rouge les résultats trouvés
                self.table.setItem(row_index, col_index, item)

    def exporter_donnees(self):
        choix, ok = QtWidgets.QInputDialog.getItem(self, "Exportation", "Exporter :", ["Toute la base", "Un bénéficiaire spécifique"], 0, False)
        if not ok:
            return

        with sqlite3.connect("appuis.db") as conn:
            cursor = conn.cursor()
            if choix == "Un bénéficiaire spécifique":
                nom_recherche, ok = QtWidgets.QInputDialog.getText(self, "Rechercher", "Entrez le nom du bénéficiaire :")
                if not ok or not nom_recherche:
                    return
                cursor.execute("SELECT * FROM beneficiaires WHERE nom LIKE ?", ('%' + nom_recherche + '%',))
            else:
                cursor.execute("SELECT * FROM beneficiaires")
            
            data = cursor.fetchall()
            if not data:
                QMessageBox.warning(self, "Alerte", "Aucune donnée à exporter.")
                return

            file_name, _ = QFileDialog.getSaveFileName(self, "Enregistrer le fichier", "", "PDF Files (*.pdf);;Excel Files (*.xlsx);;All Files (*)")
            if not file_name:
                return

            if file_name.endswith(".pdf"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(200, 10, "Liste des Bénéficiaires", ln=True, align="C")
                pdf.set_font("Arial", size=12)
                pdf.ln(10)
                date_export = datetime.now().strftime("%d/%m/%Y %H:%M")
                pdf.set_font("Arial", "I", 10)
                pdf.cell(200, 10, f"Exporté le : {date_export}", ln=True, align="R")
                pdf.ln(5)
                for row in data:
                    pdf.cell(40, 10, row[1], border=1)
                    pdf.cell(50, 10, row[2], border=1)
                    pdf.cell(40, 10, row[3], border=1)
                    pdf.cell(30, 10, str(row[4]), border=1)
                    pdf.cell(20, 10, str(row[5]), border=1)
                    pdf.ln()
                pdf.output(file_name)
                QMessageBox.information(self, "Succès", "Exporté en PDF avec succès !")
            else:
                df = pd.DataFrame(data, columns=["ID", "Nom", "Adresse", "Type d'appui", "Montant", "Année"])
                df.to_excel(file_name, index=False, engine='openpyxl')
                QMessageBox.information(self, "Succès", "Exporté en Excel avec succès !")
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
