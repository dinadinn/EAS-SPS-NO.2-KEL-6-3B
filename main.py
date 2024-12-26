import sys
import numpy as np
import sounddevice as sd
import soundfile as sf  # Pastikan pustaka ini diimpor
from mutagen.mp3 import MP3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QFileDialog, QWidget
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class NoiseAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analisis Kebisingan Mesin Mobil - Kelompok 6")
        self.setGeometry(100, 100, 1000, 700)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #2E3440;
            }
            QLabel {
                color: #D8DEE9;
            }
            QComboBox, QPushButton {
                background-color: #3B4252;
                color: #ECEFF4;
                border: 1px solid #4C566A;
                padding: 5px;
            }
            QPushButton {
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5E81AC;
            }
            QPushButton:disabled {
                background-color: #4C566A;
                color: #D8DEE9;
            }
        """)

        # Layout utama
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Bagian atas: Pilihan jenis mesin dan tombol
        self.top_layout = QHBoxLayout()
        self.engine_label = QLabel("Pilih Jenis Mesin:")
        self.engine_selector = QComboBox()
        self.engine_selector.addItems(["Bensin", "Diesel"])
        self.top_layout.addWidget(self.engine_label)
        self.top_layout.addWidget(self.engine_selector)

        self.start_button = QPushButton("Start Recording")
        self.stop_button = QPushButton("Stop Recording")
        self.play_button = QPushButton("Play")
        self.reset_button = QPushButton("Reset")
        self.upload_button = QPushButton("Upload Audio")

        self.stop_button.setEnabled(False)
        self.play_button.setEnabled(False)
        self.reset_button.setEnabled(False)

        self.top_layout.addWidget(self.start_button)
        self.top_layout.addWidget(self.stop_button)
        self.top_layout.addWidget(self.play_button)
        self.top_layout.addWidget(self.reset_button)
        self.top_layout.addWidget(self.upload_button)
        self.layout.addLayout(self.top_layout)

        # Bagian bawah: Dua grafik matplotlib
        self.figure_realtime = Figure()
        self.figure_dft = Figure()

        self.canvas_realtime = FigureCanvas(self.figure_realtime)
        self.canvas_dft = FigureCanvas(self.figure_dft)

        self.graph_layout = QVBoxLayout()
        self.graph_layout.addWidget(self.canvas_realtime)
        self.graph_layout.addWidget(self.canvas_dft)

        self.layout.addLayout(self.graph_layout)

        # Setup untuk rekaman
        self.fs = 44100  # Default sample rate
        self.duration = 5  # Durasi rekaman
        self.recording = None

        # Connect tombol ke fungsi
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        self.play_button.clicked.connect(self.play_recording)
        self.reset_button.clicked.connect(self.reset_all)
        self.upload_button.clicked.connect(self.upload_audio)

    def start_recording(self):
        self.recording = sd.rec(int(self.duration * self.fs), samplerate=self.fs, channels=1)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_recording(self):
        sd.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.play_button.setEnabled(True)
        self.reset_button.setEnabled(True)
        self.plot_realtime()
        self.plot_dft()

    def play_recording(self):
        if self.recording is not None:
            sd.play(self.recording, samplerate=self.fs)

    def reset_all(self):
        self.recording = None
        self.figure_realtime.clear()
        self.figure_dft.clear()
        self.canvas_realtime.draw()
        self.canvas_dft.draw()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.play_button.setEnabled(False)
        self.reset_button.setEnabled(False)

    def upload_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Pilih File Audio", "", "Audio Files (*.mp3 *.wav)")
        if file_path.endswith('.mp3'):
            try:
                audio = MP3(file_path)
                self.duration = audio.info.length
                # Generate a silent waveform for demonstration
                self.recording = np.zeros(int(self.duration * self.fs), dtype=np.float32)
            except Exception as e:
                self.show_error_message(f"Gagal membaca file MP3: {e}")
                return
        elif file_path.endswith('.wav'):
            try:
                data, self.fs = sf.read(file_path)
                self.recording = data
            except Exception as e:
                self.show_error_message(f"Gagal membaca file WAV: {e}")
                return
        else:
            self.show_error_message("Format file tidak didukung!")
            return

        self.plot_realtime()
        self.plot_dft()
        self.play_button.setEnabled(True)
        self.reset_button.setEnabled(True)

    def plot_realtime(self):
        if self.recording is not None:
            self.figure_realtime.clear()
            ax = self.figure_realtime.add_subplot(111)
            time = np.linspace(0, len(self.recording) / self.fs, len(self.recording))
            ax.plot(time, self.recording)
            ax.set_title("Grafik Rekaman Waktu Nyata - Mesin {}".format(self.engine_selector.currentText()))
            ax.set_xlabel("Waktu (s)")
            ax.set_ylabel("Amplitudo")
            self.canvas_realtime.draw()

    def plot_dft(self):
        if self.recording is not None:
            self.figure_dft.clear()
            signal = self.recording.flatten()
            N = len(signal)
            freq = np.fft.rfftfreq(N, d=1 / self.fs)
            magnitude = np.abs(np.fft.rfft(signal))

            ax = self.figure_dft.add_subplot(111)
            ax.plot(freq, magnitude)
            ax.set_title("Transformasi Fourier Diskret (DFT) - Mesin {}".format(self.engine_selector.currentText()))
            ax.set_xlabel("Frekuensi (Hz)")
            ax.set_ylabel("Amplitudo")
            self.canvas_dft.draw()

    def show_error_message(self, message):
        error_dialog = QFileDialog()
        error_dialog.setWindowTitle("Error")
        error_dialog.setLabelText(message)
        error_dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NoiseAnalyzerApp()
    window.show()
    sys.exit(app.exec())

