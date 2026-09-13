import os
import random
import shutil
import sys
from mutagen import File
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFileDialog, QSpinBox, 
    QProgressBar, QMessageBox
)

class USBMusicPrep(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("USB Music Organizer")
        self.resize(500, 250)
        
        layout = QVBoxLayout()

        # Source Folder
        h_origen = QHBoxLayout()
        self.lbl_origen = QLabel("Music Folder: Not selected")
        btn_origen = QPushButton("Browse...")
        btn_origen.clicked.connect(self.select_origen)
        h_origen.addWidget(self.lbl_origen)
        h_origen.addWidget(btn_origen)
        layout.addLayout(h_origen)

        # Song Limit
        h_cantidad = QHBoxLayout()
        h_cantidad.addWidget(QLabel("Number of songs:"))
        self.spin_cant = QSpinBox()
        self.spin_cant.setRange(1, 9999)
        self.spin_cant.setValue(50)
        h_cantidad.addWidget(self.spin_cant)
        layout.addLayout(h_cantidad)

        # USB Destination Folder
        h_destino = QHBoxLayout()
        self.lbl_destino = QLabel("USB Drive: Not selected")
        btn_destino = QPushButton("Browse...")
        btn_destino.clicked.connect(self.select_destino)
        h_destino.addWidget(self.lbl_destino)
        h_destino.addWidget(btn_destino)
        layout.addLayout(h_destino)

        # Progress Bar
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        # Generate Button
        btn_generar = QPushButton("Generate")
        btn_generar.setStyleSheet("font-weight: bold; padding: 8px;")
        btn_generar.clicked.connect(self.procesar)
        layout.addWidget(btn_generar)

        self.setLayout(layout)
        self.origen_path = ""
        self.destino_path = ""

    def select_origen(self):
        path = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if path:
            self.origen_path = path
            self.lbl_origen.setText(f"Music: {os.path.basename(path)}")

    def select_destino(self):
        path = QFileDialog.getExistingDirectory(self, "Select USB Drive Target Folder")
        if path:
            self.destino_path = path
            self.lbl_destino.setText(f"USB: {os.path.basename(path)}")

    def obtener_metadatos(self, filepath):
        try:
            audio = File(filepath, easy=True)
            if audio is None:
                return "Unknown", "0000"
            artista = audio.get("artist", ["Unknown"])[0]
            fecha = audio.get("date", audio.get("year", ["0000"]))[0]
            año = str(fecha)[:4] if str(fecha)[:4].isdigit() else "0000"
            return artista, año
        except Exception:
            return "Unknown", "0000"

    def organizar_canciones(self, archivos, limite):
        items = []
        for f in archivos:
            art, yr = self.obtener_metadatos(f)
            items.append({"path": f, "artist": art, "year": yr})

        random.shuffle(items)
        
        seleccionadas = []
        ultimo_pos_artista = {}

        MIN_DISTANCIA = 5
        MAX_DISTANCIA = 7

        while items and len(seleccionadas) < limite:
            pos_actual = len(seleccionadas)
            candidato_idx = -1
            
            for i, item in enumerate(items):
                art = item["artist"]
                distancia = pos_actual - ultimo_pos_artista.get(art, -999)

                if distancia >= MIN_DISTANCIA:
                    año_anterior = seleccionadas[-1]["year"] if seleccionadas else None
                    if año_anterior is None or item["year"] != año_anterior or distancia >= MAX_DISTANCIA:
                        candidato_idx = i
                        break

            if candidato_idx == -1:
                for i, item in enumerate(items):
                    art = item["artist"]
                    distancia = pos_actual - ultimo_pos_artista.get(art, -999)
                    if distancia >= MIN_DISTANCIA:
                        candidato_idx = i
                        break

            if candidato_idx == -1:
                mayor_distancia = -1
                for i, item in enumerate(items):
                    art = item["artist"]
                    distancia = pos_actual - ultimo_pos_artista.get(art, -999)
                    if distancia > mayor_distancia:
                        mayor_distancia = distancia
                        candidato_idx = i

            elegido = items.pop(candidato_idx if candidato_idx != -1 else 0)
            seleccionadas.append(elegido)
            ultimo_pos_artista[elegido["artist"]] = pos_actual

        return seleccionadas

    def procesar(self):
        if not self.origen_path or not self.destino_path:
            QMessageBox.critical(self, "Error", "You must select both folders.")
            return

        extensiones = ('.mp3', '.flac', '.m4a', '.ogg')
        archivos = [
            os.path.join(dp, f) 
            for dp, dn, filenames in os.walk(self.origen_path) 
            for f in filenames if f.lower().endswith(extensiones)
        ]

        if not archivos:
            QMessageBox.warning(self, "Warning", "No audio files were found.")
            return

        limite = self.spin_cant.value()
        lista_final = self.organizar_canciones(archivos, limite)

        self.progress.setMaximum(len(lista_final))
        self.progress.setValue(0)

        for idx, item in enumerate(lista_final, start=1):
            ext = os.path.splitext(item["path"])[1]
            nombre_orig = os.path.basename(item["path"])
            
            nuevo_nombre = f"{idx:03d} - {nombre_orig}"
            destino_archivo = os.path.join(self.destino_path, nuevo_nombre)

            shutil.copy2(item["path"], destino_archivo)
            self.progress.setValue(idx)

        QMessageBox.information(self, "Success", f"Successfully copied {len(lista_final)} songs to the USB drive!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = USBMusicPrep()
    window.show()
    sys.exit(app.exec())
